import re
from collections import OrderedDict

# 功能模板
logic_templates = {
    'DFFX1':   "reg Q; always @(posedge CLK) Q <= D; assign QN = ~Q;",
    'DFFX2':   "reg Q; always @(posedge CLK) Q <= D; assign QN = ~Q;",
    'NBUFFX2': "assign Z = INP;",
    'NBUFFX4': "assign Z = INP;",
    'INVX0':   "assign ZN = ~INP;",
    'INVX32':  "assign ZN = ~INP;",
    'AND2X1':  "assign Q = IN1 & IN2;",
    'AND2X2':  "assign Q = IN1 & IN2;",
    'AND2X4':  "assign Q = IN1 & IN2;",
    'OR2X1':   "assign Q = IN1 | IN2;",
    'OR2X2':   "assign Q = IN1 | IN2;",
    'OR2X4':   "assign Q = IN1 | IN2;",
    'NAND2X0': "assign QN = ~(IN1 & IN2);",
    'NAND2X1': "assign QN = ~(IN1 & IN2);",
    'NOR2X0':  "assign QN = ~(IN1 | IN2);",
}

def extract_gate_types_and_ports_v2(netlist_path):
    with open(netlist_path, 'r') as f:
        netlist = f.read()
    gate_port_order = OrderedDict()
    # 提取门实例 (如 AND2X1 U1 ( .IN1(A), .IN2(B), .Q(Z) ); )
    instances = re.findall(r"^\s*([A-Z0-9_]+)\s+\w+\s*\(([^;]*)\)\s*;", netlist, re.MULTILINE | re.DOTALL)
    for cell_type, connections in instances:
        if cell_type not in gate_port_order:
            connections = re.sub(r"//.*", "", connections)
            port_connections = re.findall(r"\.(\w+)\s*\(", connections)
            if port_connections:
                gate_port_order[cell_type] = port_connections
    return gate_port_order

def gen_cells_v(gate_port_order, logic_templates, out_file="cells.v"):
    with open(out_file, "w") as f:
        for cell, ports in gate_port_order.items():
            portlist = ", ".join(ports)
            # 端口方向声明
            port_dirs = []
            for p in ports:
                logic = logic_templates.get(cell, "")
                # 判断输出端口
                if logic.find(f"{p} =") >= 0 and "assign" in logic:
                    port_dirs.append(f"output {p}")
                elif logic.find(f"{p};") >= 0 and "reg" in logic:
                    port_dirs.append(f"output reg {p}")
                elif p.startswith('Q') and cell.startswith('DFFX'):
                    port_dirs.append(f"output {p}")
                elif p == 'Z' or p == 'ZN':
                    port_dirs.append(f"output {p}")
                else:
                    port_dirs.append(f"input {p}")
            port_dirs_str = "; ".join(port_dirs)
            logic = logic_templates.get(cell, "")
            if logic:
                f.write(f"module {cell} ({portlist}); {port_dirs_str}; {logic} endmodule\n")
            else:
                # 没有功能模板的直接黑盒
                f.write(f"module {cell} ({portlist}); {port_dirs_str}; endmodule\n")
    print(f"cells.v 生成完成！")

if __name__ == "__main__":
    # 填写你的门级网表文件名
    netlist_file = "pe.synth_dct.v"
    gate_port_order = extract_gate_types_and_ports_v2(netlist_file)
    print("自动检测到门类型及端口顺序：")
    for cell, ports in gate_port_order.items():
        print(f"{cell}: {ports}")
    gen_cells_v(gate_port_order, logic_templates, out_file="cells.v")
