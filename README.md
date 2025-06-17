# fusa
Functional safety evaluations for ML accelerators


Objective:
1. Goal: To evaluate the functional safety of an AI accelerator by measuring the proportion of "unsafe" faults through fault - injection experiments.
2. Criterion: If the inference accuracy under fault is over 90%, the fault is "safe"; otherwise, it's "unsafe".
3. Challenge: The AI accelerator's enormous fault space makes full - scale fault simulation impossible. Thus, only a subset of faults (e.g., single processing element - PE) can be statistically analyzed to infer the global situation.





Step 1: Scan the gate-level netlist (pe.synth_dct.v) and generate cells.v code (code in generate_cells.v.python)

• The gate-level netlist itself only represents instances of gates (i.e., circuit structure) without specifying how each gate works.

• The simulator needs the definitions of each type of gate in cells.v to know how to simulate the logic functions of gates like AND2X1 and DFFX1.

• Without cells.v, the simulator would report errors such as 'module not found' or 'port mismatch' when encountering these gates.

• Pyverilog can parse the netlist, modify the AST, insert fault assignment statements, and generate a new Verilog file with faults. However, if you want to run this file using a Verilog simulator (such as iverilog), you also need to automatically generate a simplified gate library definition file (cells.v). This code can automatically scan your netlist and generate a simplified behavioral model cells.v file that includes only the gates you used. Once cells.v is complete, most gate-level simulations and Pyverilog's automatic fault injection will work.

• Essentially, cells.v is a 'gate library' file. Each module in it must correspond exactly to the types, port names, port order, and number of ports of all gates in your gate-level netlist. If cells.v is missing, when the simulator encounters a gate type from the netlist (like AND2X1), and cannot find the corresponding module definition, it will report an error: 'module AND2X1 not found'.



Step 2: Testbench load (code in tb.v)
The role of the testbench is to:

• Apply input stimulus signals to the circuit

• Collect and evaluate the output

• Implement automated simulation processes

• Compare normal and faulty netlist outputs, analyzing the impact of faults



step 3: gate-level fault injection using Pyverilog (code in gatesa_fault_injection.py)

Basic approach
• Use Pyverilog to parse Verilog netlists and construct an Abstract Syntax Tree (AST).

• Traverse all gates (such as AND/OR/XOR...) and perform 'fault injection' on each gate—such as forcing the output to 0 (stuck-at-0) or 1 (stuck-at-1).

• For each fault version, generate a modified Verilog file, call Icarus Verilog (iverilog) to run functional simulation, and extract the output.

Fault injection mechanism:   Inject faults into all gate output ports, regardless of whether they are wires or registers, by inserting an assign statement to achieve 'generalized node-level' injection, ensuring no output nodes are skipped. This indirectly covers all Q-end registers and wire nodes.

• Single Fault Injection (SFI) —— Industry standard practice

• Introduce only one fault at a time in one netlist (e.g., a register's output stuck-at-1).

• This facilitates analyzing the independent impact and detectability of each fault.

• It is also the recommended method for all mainstream fault simulation and fault-tolerant verification tools (such as FT/FI tools, ATPG, etc.).


step 4: generate_golden_sim_out.log.py
  The script generate_golden_sim_out.py is needed to automatically produce a "golden" (fault-free) simulation output log from your original gate-level Verilog design using your testbench. This golden output serves as the reference baseline for all subsequent fault injection experiments. By comparing the outputs from fault-injected simulations to the golden simulation results, you can accurately detect and quantify the effect of each injected fault on the circuit’s behavior. Without this golden reference, it would be impossible to determine whether a fault has any impact or to measure error metrics such as RMSE (Root Mean Square Error). Therefore, generating golden_sim_output.log is a crucial first step for reliable and automated fault analysis.

step 5: calculating RMSE (cod in calc_rmse_faults.py)

Principle:   RMSE = sqrt(mean((faulty_output - golden_output)^2))

This Python script reads simulation output logs from both golden (fault-free) and fault-injected runs, compares the numerical results, and computes the RMSE (Root Mean Square Error) for each fault. It is designed to automate the analysis of digital circuit fault injection experiments.

**Note:**  
This script is intended for use with log files where each line contains a field like `o_sum= ...`, as produced by the recommended Verilog testbench.
