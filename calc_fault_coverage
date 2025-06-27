import pandas as pd
import argparse
import time
from datetime import timedelta


def calculate_coverage(rmse_file, threshold):
    """
    Calculate fault coverage (all thresholds passed as parameters)
    Parameters:
        rmse_file: Path to RMSE results file
        threshold: RMSE threshold (must be specified as a parameter)
    Returns:
        coverage: Coverage percentage
        critical_count: Number of critical faults
    """
    start_time = time.time()
    try:
        df = pd.read_csv(rmse_file)

        # Calculate coverage
        critical = df[df['rmse'] > threshold]
        coverage = len(critical) / len(df) * 100
        critical_count = len(critical)

        # Print results
        print("\n" + "=" * 40)
        print(f"Total Faults:      {len(df)}")
        print(f"Critical Faults:   {critical_count}")
        print(f"Coverage:          {coverage:.2f}%")
        print(f"Threshold:         {threshold}")
        print("=" * 40 + "\n")

        # Save list of critical faults
        critical['fault_name'].to_csv('critical_fs.txt', index=False, header=False)
        print("✅ Critical faults saved to 'critical_fs.txt'")

        return coverage, critical_count

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 0, 0
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️  Total execution time: {timedelta(seconds=elapsed)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fault Coverage Calculator with 1024 random vectors support')
    parser.add_argument("--threshold", type=float, default=1,
                        help="RMSE threshold value (default: 5.0)")
    parser.add_argument("--input", default="rmse_results.csv",
                        help="Input CSV file (default: rmse_results.csv)")
    parser.add_argument("--vectors", type=int, default=1024,
                        help="Number of test vectors used per fault (default: 24)")
    args = parser.parse_args()

    print(f"🔧 Configuration:")
    print(f"- RMSE threshold: {args.threshold}")
    print(f"- Input file: {args.input}")
    print(f"- Test vectors per fault: {args.vectors}")

    coverage, critical_count = calculate_coverage(rmse_file=args.input, threshold=args.threshold)

    # Analysis of low coverage reasons
    if coverage < 50:  # If coverage is less than 50%
        print("\n⚠️ Low coverage analysis:")
        if args.vectors < 100:
            print(f"- The number of test vectors ({args.vectors}) may be too low")
            print("- Recommendation: Increase to 1024 vectors like reference method")
        else:
            print("- Possible causes:")
            print("  a) Threshold may be too high (try --threshold 1)")
            print("  b) Fault injection may not be effective")
            print("  c) PE module may have fault masking")
