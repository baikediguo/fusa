TECHLIBS=lib.nogit
WORK=work.nogit

all: golden

golden:
	mkdir -p $(WORK)
	iverilog -o $(WORK)/simv synthesized/pe.saed90.v $(TECHLIBS)/saed90nm.v tests/pe_tb_functional.v && vvp $(WORK)/simv >$(WORK)/golden_sim_output.log