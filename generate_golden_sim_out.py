import os
import subprocess

# 1. 定义文件名（如有不同请手动替换）
netlist = 'pe.synth_dct.v'
tb = 'tb.v'
cells = 'cells.v'
exec_file = 'simv'
golden_output = 'golden_sim_output.log'

# 2. 编译无故障设计
compile_cmd = f'iverilog -o {exec_file} {netlist} {tb} {cells}'
print(f'[INFO] 正在编译: {compile_cmd}')
ret = os.system(compile_cmd)
if ret != 0:
    print('[ERROR] iverilog 编译失败，请检查文件名和语法！')
    exit(1)

# 3. 运行仿真并保存输出
sim_cmd = f'vvp {exec_file}'
print(f'[INFO] 正在运行仿真: {sim_cmd}')
with open(golden_output, 'w') as f:
    proc = subprocess.Popen(sim_cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    proc.communicate()

print(f'[SUCCESS] golden_sim_output.log 已生成，请检查文件内容！')
