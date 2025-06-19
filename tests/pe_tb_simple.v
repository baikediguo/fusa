`default_nettype none
`timescale 1 ns / 1 ps

`define assert(signal, value, detail) \
        if (signal !== value) begin \
            $display("ASSERTION FAILED @ %t: signal should be value, but was %x detail.", $time, signal); \
            $finish; \
        end

module tb;

    reg clock = 0;
    always #10 clock = ~clock;  // 20 ns period for 50 MHz clock

    reg reset = 1;
    initial #100 reset = 0; // release reset after 100 ns

    reg signed [7:0] weight;
    reg signed [7:0] activation;
    reg signed [23:0] prev_sum;
    
    wire signed [23:0] next_sum;
    
    // Device Under Test
    pe dut (
        .clock(clock),
        .reset(reset),
        .i_weight(weight),
        .i_activation(activation),
        .i_sum(prev_sum),

        .o_sum(next_sum)
    );

    initial begin
        $timeformat(-9, 2, " ns", 1);
        $dumpfile("tb.vcd");
        $dumpvars;

        weight = 0;
        activation = 0;
        prev_sum = 0;

        #100;
        @(negedge clock);

        // check condition after reset
        `assert(next_sum, 0, after reset)
        
        // clock in weight and activation
        weight = 21;
        activation = 2;
        @(negedge clock);

        // clock in next assignment, finish first calculation
        weight = -11;
        activation = 2;
        prev_sum = 1;
        @(negedge clock);
        
        `assert(next_sum, 43, after calculation)  // check first calculation
        @(negedge clock);
        
        `assert(next_sum, -21, after calculation)  // check second calculation
        @(negedge clock);

        $display("Test successful! ^o^");

        $finish;
    end

endmodule