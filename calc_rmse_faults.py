import glob
import os
import math
import re
import csv


def read_log(filename):
    """
    Parse simulation log file to extract numerical output values.
    Args:
        filename (str): Path to log file
    Returns:
        list: Extracted numerical values, NaN for invalid entries
    """
    result = []
    pat = re.compile(r"(o_sum|OUTPUT|result)\s*[=:]\s*(0x)?([0-9a-fA-F]+)", re.IGNORECASE)
    try:
        with open(filename, 'r') as f:
            for line in f:
                m = pat.search(line)
                if m:
                    try:
                        base = 16 if m.group(2) else 10
                        result.append(int(m.group(3), base))
                    except ValueError:
                        result.append(float('nan'))
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
    return result


def compute_rmse(golden, faulty):
    """
    Calculate RMSE between golden and faulty outputs.
    Args:
        golden (list): Reference values
        faulty (list): Faulty values
    Returns:
        tuple: (RMSE value, valid comparison count)
    """
    minlen = min(len(golden), len(faulty))
    valid_pairs = [(g, f) for g, f in zip(golden[:minlen], faulty[:minlen])
                   if not math.isnan(g) and not math.isnan(f)]
    if not valid_pairs:
        return None, 0
    return math.sqrt(sum((g - f) ** 2 for g, f in valid_pairs) / len(valid_pairs)), len(valid_pairs)


def main():
    log_dir = os.path.join(os.getcwd(), 'sim_logs')
    golden_file = os.path.join(log_dir, 'golden.log')

    # Validate golden log
    if not os.path.exists(golden_file):
        print(f"❌ Golden log not found: {golden_file}")
        return

    golden = read_log(golden_file)
    if not golden:
        print("❌ No valid data in golden log")
        return

    # Process fault logs
    results = []
    log_files = [f for f in glob.glob(os.path.join(log_dir, 'fault_*.log'))
                 if not f.endswith('golden.log')]

    print("{:<50s} {:>12s}  |  {:s}".format("Fault", "RMSE", "Valid Points"))
    print("=" * 72)

    for lf in sorted(log_files):
        fault_name = os.path.basename(lf).replace('.log', '')
        vals = read_log(lf)

        if not vals:
            print(f"{fault_name:<50s} {'No Data':>12}")
            results.append([fault_name, float('nan'), 0])
            continue

        rmse, count = compute_rmse(golden, vals)
        if rmse is None:
            print(f"{fault_name:<50s} {'Invalid':>12}")
            results.append([fault_name, float('nan'), 0])
        else:
            print(f"{fault_name:<50s} {rmse:12.4f}  |  {count:<6d}")
            results.append([fault_name, rmse, count])

    # Save results
    with open('rmse_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['fault_name', 'rmse', 'valid_points'])
        writer.writerows(results)
    print("\n✅ Results saved to rmse_results.csv")


if __name__ == "__main__":
    main()
