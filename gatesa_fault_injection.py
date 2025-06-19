import os
import sys
import copy
import subprocess
from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

# 配置区：指定文件名、参数、门列表等
VERILOG_FILE = 'synthesized/pe.saed90.v'     # 被注入的门级Verilog文件
TB_FILE = 'tests/pe_tb_functional.v'                    # 测试平台文件
CELLS_FILE = 'lib.nogit/saed90nm.v'              # 标准单元库文件
STUCK_VALUES = [0, 1]               # 故障类型：SA0和SA1
MAX_FAULTS = 100                    # 最多注入多少个故障（None为全部）
SKIP_TOP_OUTPUTS = ['o_sum']        # 不注入的顶层输出端口，可扩展
WORK = 'work.nogit'

# 常见门类型及其输出端口映射表
GATE_OUTPUT_PORT_MAP = {
    "DFFX1":    ["Q", "QN"],
    "DFFX2":    ["Q", "QN"],
    "NBUFFX2":  ["Z"],
    "NBUFFX4":  ["Z"],
    "INVX0":    ["ZN"],
    "INVX32":   ["ZN"],
    "AND2X1":   ["Q"],
    "AND2X2":   ["Q"],
    "AND2X4":   ["Q"],
    "OR2X1":    ["Q"],
    "OR2X2":    ["Q"],
    "OR2X4":    ["Q"],
    "NAND2X0":  ["QN"],
    "NAND2X1":  ["QN"],
    "NOR2X0":   ["QN"],
}

def find_all_instances_recursive(node, found=None, current_module=None):
    """
    递归遍历AST，查找所有门实例。
    返回格式为[(实例名, 模块类型, 实例对象, 当前module定义对象)]
    """
    if found is None:
        found = []
    if hasattr(node, 'children'):
        for child in node.children():
            # 找到门实例（InstanceList）
            if child.__class__.__name__ == "InstanceList":
                module_type = getattr(child, "module", "")
                for inst in child.instances:
                    found.append((inst.name, module_type, inst, current_module))
            else:
                # 如果是module定义，则标记
                next_mod = current_module
                if hasattr(child, 'name') and hasattr(child, 'items'):
                    next_mod = child
                find_all_instances_recursive(child, found, next_mod)
    return found

def get_gate_output_ports(module_type, inst):
    """
    找到指定门实例的输出端口名
    优先查表，否则默认取portlist第一个端口
    """
    outs = GATE_OUTPUT_PORT_MAP.get(module_type, [])
    result = []
    if outs:
        # 查表获取端口
        for portname in outs:
            for p in inst.portlist:
                if hasattr(p, 'portname') and p.portname == portname:
                    if hasattr(p.argname, 'name'):
                        result.append(p.argname.name)
    else:
        # 没有查到，默认取第一个端口
        if hasattr(inst, 'portlist') and inst.portlist:
            first = inst.portlist[0]
            if hasattr(first.argname, 'name'):
                result.append(first.argname.name)
    return result

def is_injectable_signal(module, signal_name):
    """
    判断信号名是否可被注入（排除reg类型，因为reg不能assign）
    """
    for item in getattr(module, 'items', []):
        if hasattr(item, 'children'):
            for decl in item.children():
                if not hasattr(decl, 'names'):
                    continue
                for n in decl.names:
                    if hasattr(n, 'name') and n.name == signal_name:
                        typename = decl.__class__.__name__.lower()
                        if 'reg' in typename:
                            return False
                        return True
    return True  # 默认为可注入

def is_skip_top_output(signal_name):
    """判断该信号名是否为被跳过的顶层输出"""
    return signal_name in SKIP_TOP_OUTPUTS

def inject_fault(ast, target_inst_name, output_port, stuck_val, instances):
    """
    在指定门实例的输出端口插入故障语句（assign xxx = 0/1;）
    修改AST树，返回是否注入成功
    """
    from pyverilog.vparser.ast import Assign, Identifier, IntConst, Lvalue, Rvalue
    for (inst_name, module_type, inst, mod) in instances:
        if inst_name == target_inst_name and mod is not None:
            if output_port is not None:
                if is_skip_top_output(output_port):
                    print(f"[INFO] 跳过顶层输出 {output_port}")
                    return False
                if not is_injectable_signal(mod, output_port):
                    print(f"[INFO] 跳过不可注入类型 {output_port}")
                    return False
                # 在module开头插入 assign xxx = stuck_val;
                assign_stmt = Assign(
                    Lvalue(Identifier(output_port)),
                    Rvalue(IntConst(str(stuck_val)))
                )
                if isinstance(mod.items, tuple):
                    mod.items = list(mod.items)
                mod.items.insert(0, assign_stmt)
                return True
    return False

def write_verilog(ast, filename):
    """将修改后的AST生成Verilog代码，写入文件"""
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(f"[DEBUG] Writing {filename}")
    with open(filename, 'w') as f:
        f.write(rslt)

def run_simulation(fault_v, tb_v, cells_v, log_path):
    """
    编译并仿真一个带故障的Verilog，log输出到log_path
    """
    exec_cmd = f"iverilog -o {fault_v.replace('.v','')}_simv {tb_v} {fault_v} {cells_v} && vvp {fault_v.replace('.v','')}_simv"
    with open(log_path, 'w') as f:
        proc = subprocess.run(exec_cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    return proc.returncode == 0

def main():
    print("当前工作目录:", os.getcwd())
    # 检查必需的文件是否存在
    if not os.path.exists(VERILOG_FILE):
        print(f"缺少文件: {VERILOG_FILE}")
        sys.exit(1)
    if not os.path.exists(TB_FILE):
        print(f"缺少testbench文件: {TB_FILE}")
        sys.exit(1)
    if not os.path.exists(CELLS_FILE):
        print(f"缺少标准单元库文件: {CELLS_FILE}")
        sys.exit(1)

    # 解析Verilog门级文件，得到AST
    ast, _ = parse([VERILOG_FILE])
    instances = find_all_instances_recursive(ast)
    print(f"共找到 {len(instances)} 个实例")
    if len(instances) == 0:
        print("未找到任何门实例！")
        sys.exit(1)

    count = 0
    reached_limit = False
    # 遍历每个门实例的每个输出端口，每个stuck值
    for idx, (inst_name, module_type, inst, mod) in enumerate(instances):
        outs = get_gate_output_ports(module_type, inst)
        if not outs:
            print(f"[INFO] {inst_name} ({module_type}) 没有检测到输出端口，跳过")
            continue
        for out_port in outs:
            for stuck in STUCK_VALUES:
                if MAX_FAULTS is not None and count >= MAX_FAULTS:
                    reached_limit = True
                    break
                # 深拷贝AST以便每次注入不同故障
                ast_faulty = copy.deepcopy(ast)
                faulty_instances = find_all_instances_recursive(ast_faulty)
                ok = inject_fault(ast_faulty, inst_name, out_port, stuck, faulty_instances)
                fault_v = f'{WORK}/fault_{inst_name}_{out_port}_sa{stuck}.v'
                log_path = f'{WORK}/fault_{inst_name}_{out_port}_sa{stuck}.log'
                if ok:
                    print(f"[DEBUG] About to write {fault_v}")
                    write_verilog(ast_faulty, fault_v)
                    print(f"注入 {inst_name} ({module_type}) {out_port} stuck-at-{stuck} ...仿真中")
                    run_simulation(fault_v, TB_FILE, CELLS_FILE, log_path)
                    count += 1
                else:
                    print(f"[INFO] 跳过 {inst_name} 的 {out_port} 注入")
            if reached_limit:
                print(f"已注入 {MAX_FAULTS} 个节点，提前停止。")
                break
        if reached_limit:
            break
    print(f"最终共注入 {count} 个有效节点")

if __name__ == '__main__':
    main()
