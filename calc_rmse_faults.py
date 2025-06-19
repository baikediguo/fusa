import glob
import math
import re

def read_log(filename):
    result = []
    pat = re.compile(r"o_sum=\s*(\S+)")
    with open(filename, 'r') as f:
        for line in f:
            m = pat.search(line)
            if not m:
                continue
            val = m.group(1)
            if val == 'X':
                result.append(float('nan'))
            else:
                try:
                    result.append(float(val))
                except:
                    result.append(float('nan'))  # 用nan表示X
    return result

if __name__ == "__main__":
    WORK = 'work.nogit'
    log_files = glob.glob(f'{WORK}/fault_*.log')
    # 排除golden文件
    log_files = [f for f in log_files if f != f'{WORK}/golden_sim_output.log']
    golden_file = f'{WORK}/golden_sim_output.log'

    golden = read_log(golden_file)
    if not golden:
        print("golden_sim_output.log没有可用数据！")
        exit(1)

    print("{:<48s}{}  |  有效对比行数".format("故障点", "RMSE"))
    print("="*65)
    for lf in sorted(log_files):
        fault_name = lf.replace('fault_', '').replace('.log', '')
        vals = read_log(lf)
        if len(vals) != len(golden):
            print("{:<48s}{}".format(fault_name, "数据长度不一致"))
            continue
        # 对比并过滤掉无效行
        valid_pairs = [(a, b, idx) for idx, (a, b) in enumerate(zip(vals, golden)) if not math.isnan(a) and not math.isnan(b)]
        if not valid_pairs:
            print("{:<48s}{}".format(fault_name, "无有效数据"))
            continue
        # 计算RMSE
        rmse = sum((a-b)**2 for a, b, _ in valid_pairs) / len(valid_pairs)
        rmse = rmse ** 0.5
        print("{:<48s}{:.4f}  |  {:d}".format(fault_name, rmse, len(valid_pairs)))
        # 若有差异，输出详细信息
        diff_cnt = 0
        for a, b, idx in valid_pairs:
            if a != b:
                print(f"  [line {idx+1:03d}]  fault={a:.0f}  golden={b:.0f}  diff={a-b:.0f}")
                diff_cnt += 1
        if diff_cnt == 0:
            print("  所有有效行均一致")
