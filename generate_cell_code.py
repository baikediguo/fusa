import re
from collections import OrderedDict

# Functional templates (additional gate types can be added as needed)
logic_templates = {
    'DFFX1':   "always @(posedge CLK) Q <= D; assign QN = ~Q;",
    'DFFX2':   "always @(posedge CLK) Q <= D; assign QN = ~Q;",
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

# Which gates' ports are of reg type (mainly flip-flop Q ports)
reg_outputs = {
    'DFFX1': ['Q'],
    'DFFX2': ['Q'],
}

def extract_gate_types_and_ports_v2(netlist_path):
    with open(netlist_path, 'r') as f:
        netlist = f.read()
    gate_port_order = OrderedDict()
    # Extract gate instances (e.g., AND2X1 U1 ( .IN1(A), .IN2(B), .Q(Z) ); )
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
            port_types = []
            reg_declares = []
            for p in ports:
                if cell in reg_outputs and p in reg_outputs[cell]:
                    port_types.append(f"output reg {p}")
                elif logic_templates.get(cell, "").find(f"{p} =") >= 0 or \
                     (p.startswith('Q') or p in ['Z', 'ZN', 'QN']):
                    port_types.append(f"output {p}")
                else:
                    port_types.append(f"input {p}")
            port_types_str = "; ".join(port_types)
            logic = logic_templates.get(cell, "")
            # Generate module
            f.write(f"module {cell} ({portlist}); {port_types_str}; {logic} endmodule\n")
    print(f"cells.v has been generated successfully!")

if __name__ == "__main__":
    netlist_file = "pe.synth_dct.v"  # Change to your main gate-level netlist file name
    gate_port_order = extract_gate_types_and_ports_v2(netlist_file)
    print("Automatically detected gate types and port order:")
    for cell, ports in gate_port_order.items():
        print(f"{cell}: {ports}")
    gen_cells_v(gate_port_order, logic_templates, out_file="cells.v")
