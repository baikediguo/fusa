import os
import re
import shutil
import time  # For measuring runtime

# === Configuration Parameters ===
ORIGINAL_NETLIST = 'pe.synth_dct.v'  # Path to the original synthesized netlist file
TB_TEMPLATE = 'tb.v'  # Path to the testbench template file
CELLS_FILE = 'cells.v'  # Path to the cell library file
MAX_FAULTS = None  # Maximum number of faults to inject (None = no limit)
STUCK_VALUES = [0, 1]  # Types of stuck-at faults to inject (0 and 1)

LOGDIR = 'sim_logs'  # Directory to store simulation logs
os.makedirs(LOGDIR, exist_ok=True)  # Create log directory if it doesn't exist


def extract_fault_targets(verilog_code):
    """
    Extract likely *output* net connections from Verilog netlist as fault targets.

    Args:
        verilog_code (str): Content of the Verilog netlist file

    Returns:
        list: Tuples of (instance_name, net_name, port_name, cell_type)
    """
    inst_pat = re.compile(r'(\w+)\s+(\w+)\s*\((.*?)\);', re.DOTALL)
    port_pat = re.compile(r'\.(\w+)\s*\(\s*([\w\[\]_\.]+)\s*\)')

    OUTPUT_PORT_HINTS = {'Z', 'ZN', 'Q', 'QN', 'OUT', 'Y', 'o_sum'}  # 可自定义扩展

    results = []

    for m in inst_pat.finditer(verilog_code):
        cell_type, inst_name, port_block = m.groups()
        ports = port_pat.findall(port_block)
        for port_name, net_name in ports:
            if port_name.upper() in OUTPUT_PORT_HINTS:  # 大写匹配
                clean_net = net_name.replace('.', '_')
                results.append((inst_name, clean_net, port_name, cell_type))
    return results


def modify_tb_template(tb_lines, target_net, stuck_val):
    """
    Modify testbench template to inject a fault.

    Args:
        tb_lines (list): Lines of the original testbench
        target_net (str): Net to inject fault into
        stuck_val (int): Value to force (0 or 1)

    Returns:
        list: Modified testbench lines with fault injection code
    """
    new_content = []
    force_added = False

    for line in tb_lines:
        if 'initial begin' in line and not force_added:
            new_content.append(line)
            new_content.append(f'    force uut.{target_net} = {stuck_val}; // [fault injected]\n')
            force_added = True
        elif 'endmodule' in line:
            new_content.append(f'    initial $display("FAULT_INJECTED: {target_net}={stuck_val}");\n')
            new_content.append(line)
        else:
            new_content.append(line)
    return new_content


def simulate(netlist, tb_file, logfile):
    """
    Run simulation using iverilog/vvp toolchain.

    Args:
        netlist (str): Path to netlist file
        tb_file (str): Path to testbench file
        logfile (str): Path to save simulation output

    Returns:
        bool: True if simulation succeeded, False otherwise
    """
    outfile = os.path.join(LOGDIR, 'temp.out')
    cmd = f'iverilog -o {outfile} {tb_file} {netlist} {CELLS_FILE}'
    if os.system(cmd) != 0:
        return False
    return os.system(f'vvp {outfile} > {logfile}') == 0


def main():
    start_time = time.time()

    # 1. Golden simulation
    golden_log = os.path.join(LOGDIR, 'golden.log')
    print("Running golden simulation...")
    if not simulate(ORIGINAL_NETLIST, TB_TEMPLATE, golden_log):
        print("❌ Golden simulation failed")
        return

    # 2. Extract fault targets
    with open(ORIGINAL_NETLIST, 'r') as f:
        netlist = f.read()
    targets = extract_fault_targets(netlist)
    print(f"Found {len(targets)} fault targets")

    # 3. Fault injection simulations
    with open(TB_TEMPLATE, 'r') as f:
        base_tb = f.readlines()

    count = 0
    for inst, net, pin, cell in targets[:MAX_FAULTS]:
        for val in STUCK_VALUES:
            fault_id = f"{inst}_{pin}_sa{val}"
            logfile = os.path.join(LOGDIR, f"fault_{fault_id}.log")

            modified_tb = modify_tb_template(base_tb, net, val)
            temp_tb = os.path.join(LOGDIR, 'temp_tb.v')
            with open(temp_tb, 'w') as f:
                f.writelines(modified_tb)

            print(f"Injecting {fault_id}...")
            if simulate(ORIGINAL_NETLIST, temp_tb, logfile):
                count += 1
                with open(logfile, 'r') as f:
                    if f"FAULT_INJECTED: {net}={val}" not in f.read():
                        print(f"⚠️ Injection failed for {fault_id}")
            os.remove(temp_tb)

    total_time = time.time() - start_time
    hours, rem = divmod(total_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\nCompleted {count} fault injections in "
          f"{int(hours):0>2}h:{int(minutes):0>2}m:{seconds:05.2f}s")


if __name__ == "__main__":
    main()
