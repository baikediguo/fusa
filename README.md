# fusa - FUnctional SAfety evaluations for ML accelerators

## Objective
1. Goal: Evaluate the functional safety of an AI accelerator by measuring the proportion of "unsafe" faults through fault-injection experiments.
2. Safety Criterion: A fault is "unsafe", if it causes the inference accuracy to fall below 90%.
3. Challenge: The AI accelerator's enormous fault space makes full-scale fault simulation impossible. Thus, only a subset of faults can be explicitely simulated to estimate the proportion of "unsafe" faults.

## Fault injection using Pyverilog in a single PE

[Pyverilog](https://github.com/PyHDI/Pyverilog) can parse the Verilog netlists into Abstract Syntax Trees (ASTs) and generate verilog code from ASTs. ASTs can be modified to inject faults.

Golden Simulation:
* Compile and run the gate-level model with `make golden`
* Outputs golden simulation results in `work.nogit/golden_sim_output.log`

Fault Injection:
* Model: single stuck-at fault
* `gatesa_fault_injection.py` traverses all gates (such as AND/OR/XOR...) and performs 'fault injection' on each gate—such as forcing the output to 0 (stuck-at-0) or 1 (stuck-at-1). Injects faults into all gate output ports, regardless of whether they are wires or registers, by inserting an assign statement to achieve 'generalized node-level' injection, ensuring no output nodes are skipped. This indirectly covers all Q-end registers and wire nodes.
* For each fault version, generate a modified Verilog file, call Icarus Verilog (iverilog) to run functional simulation, and extract the output.

Evaluation:
* `calc_rmse_faults.py` reads simulation output logs from both golden (fault-free) and fault-injected runs, compares the numerical results, and computes the RMSE (Root Mean Square Error) for each fault.
* This script is intended for use with log files where each line contains a field like `o_sum= ...`, as produced by the recommended Verilog testbench.
* Measure RMSE = sqrt(mean((faulty_output - golden_output)^2))

## TODO

* Perform subsequent whole - accelerator - level simulation (input inference and accuracy evaluation) by assuming the code can load and run the entire accelerator model.
* Use the output RMSE and FS as a measure of fault impact.


## Environment Setup Notes

* [Pyverilog](https://github.com/PyHDI/Pyverilog): `pip install pyverilog`
* [iVerilog](https://steveicarus.github.io/iverilog/)
* On Windows: Use [mingw-w64](https://www.mingw-w64.org) or [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)
* Technology libraries need to be downloaded separately:
  * Synopsys Educational Design Kit (SAED90nm)
  * [Nangate Open Cell Library](https://github.com/JulianKemmerer/Drexel-ECEC575/tree/master/Encounter/NangateOpenCellLibrary)
