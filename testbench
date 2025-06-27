`timescale 1ns / 1ps

module tb;

  reg clock;
  reg reset;
  reg [7:0] i_weight;
  reg [7:0] i_activation;
  reg [23:0] i_sum;
  wire [23:0] o_sum;

  // Instantiate the DUT (Device Under Test)
  pe uut (
    .clock(clock),
    .reset(reset),
    .i_weight(i_weight),
    .i_activation(i_activation),
    .i_sum(i_sum),
    .o_sum(o_sum)
  );

  // Clock generation: 10ns period
  initial begin
    clock = 0;
    forever #5 clock = ~clock;
  end

  // Stimulus sequence: Generate a diverse set of combinations to activate circuit paths
  integer i;
  initial begin
    reset = 1;
    i_weight = 0;
    i_activation = 0;
    i_sum = 0;
    #20;
    reset = 0;

    // Diverse stimuli: Use different strides, bit patterns, random numbers, and combination patterns
    for (i = 0; i < 1024; i = i + 1) begin
      @(posedge clock);
      i_weight     = (i % 3 == 0) ? i[7:0] : $random % 256;
      i_activation = (i % 3 == 1) ? ~i[7:0] : $random % 256;
      i_sum        = (i % 4 == 0) ? 24'h000000 :
                     (i % 4 == 1) ? 24'hFFFFFF :
                     (i % 4 == 2) ? $random :
                                   {i[7:0], i[7:0], i[7:0]};
    end

    // Wait for the last computation result
    repeat (10) @(posedge clock);
    $finish;
  end

  // Display output changes: Only display non-zero high bits or changed values
  reg [23:0] last_o_sum;
  initial begin
    last_o_sum = 24'hX;
    forever begin
      @(posedge clock);
      if (o_sum !== last_o_sum) begin
        $display("o_sum=%06x", o_sum);
        last_o_sum = o_sum;
      end
    end
  end

  // VCD waveform output
  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
  end

endmodule

