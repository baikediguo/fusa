module pe (
    input wire clock,
    input wire reset,
    input wire signed [7:0] i_weight,
    input wire signed [7:0] i_activation,
    input wire signed [23:0] i_sum,
    output reg signed [23:0] o_sum
    );

    reg signed [7:0] weight;
    reg signed [7:0] activation;

    wire signed [15:0] product = weight * activation;

    always @(posedge clock) begin
        if (reset) begin
            weight <= 0;
            activation <= 0;
            o_sum <= 0;
        end else begin
            weight <= i_weight;
            activation <= i_activation;
            o_sum <= i_sum + product;
        end
    end

endmodule
