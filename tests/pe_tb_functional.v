`timescale 1ns/1ps

module tb;

reg         clock;
reg         reset;
reg  [7:0]  i_weight;
reg  [7:0]  i_activation;
reg  [23:0] i_sum;
wire [23:0] o_sum;

pe uut (
    .clock(clock),
    .reset(reset),
    .i_weight(i_weight),
    .i_activation(i_activation),
    .i_sum(i_sum),
    .o_sum(o_sum)
);

// 时钟生成
initial clock = 0;
always #5 clock = ~clock; // 10ns周期

integer i, seed_w, seed_a, seed_s;

// 奇异/极端激励函数
function [7:0] alt_pattern; input integer idx; begin alt_pattern = (idx % 2) ? 8'hAA : 8'h55; end endfunction
function [7:0] onehot_pattern; input integer idx; begin onehot_pattern = (8'h1 << (idx % 8)); end endfunction

initial begin
    reset = 1; i_weight = 0; i_activation = 0; i_sum = 0;
    #20; reset = 0;

    seed_w = 42; seed_a = 99; seed_s = 12345;

    for (i = 0; i < 3000; i = i + 1) begin
        @(negedge clock);

        // 1. 全0激励
        if (i < 4) begin
            i_weight = 8'h00;
            i_activation = 8'h00;
            i_sum = 24'h000000;
        end
        // 2. 全1激励
        else if (i < 8) begin
            i_weight = 8'hFF;
            i_activation = 8'hFF;
            i_sum = 24'hFFFFFF;
        end
        // 3. 交替激励(0xAA, 0x55)
        else if (i < 16) begin
            i_weight = (i % 2) ? 8'hAA : 8'h55;
            i_activation = (i % 2) ? 8'h55 : 8'hAA;
            i_sum = (i % 2) ? 24'hAAAAAA : 24'h555555;
        end
        // 4. 边界值激励
        else if (i < 24) begin
            i_weight = (i == 16) ? 8'h01 : (i == 17) ? 8'hFE : (i == 18) ? 8'h80 : (i == 19) ? 8'h7F :
                        (i == 20) ? 8'h10 : (i == 21) ? 8'hEF : (i == 22) ? 8'hF0 : 8'h0F;
            i_activation = (i == 16) ? 8'h01 : (i == 17) ? 8'hFE : (i == 18) ? 8'h80 : (i == 19) ? 8'h7F :
                            (i == 20) ? 8'h10 : (i == 21) ? 8'hEF : (i == 22) ? 8'hF0 : 8'h0F;
            i_sum = (i == 16) ? 24'h000001 : (i == 17) ? 24'hFFFFFE : (i == 18) ? 24'h800000 : (i == 19) ? 24'h7FFFFF :
                     (i == 20) ? 24'h001000 : (i == 21) ? 24'hFFEFFF : (i == 22) ? 24'hFFF000 : 24'h000F00;
        end
        // 5. one-hot激励
        else if (i < 40) begin
            i_weight = onehot_pattern(i);
            i_activation = onehot_pattern(39-i);
            i_sum = 24'h1 << (i % 24);
        end
        // 6. 递增/递减激励
        else if (i < 60) begin
            i_weight = i[7:0];
            i_activation = 8'hFF - i[7:0];
            i_sum = (i * 123456) & 24'hFFFFFF;
        end
        // 7. 极大/极小交错激励
        else if (i < 80) begin
            i_weight = (i % 4 == 0) ? 8'h00 : (i % 4 == 1) ? 8'hFF : (i % 4 == 2) ? 8'h01 : 8'hFE;
            i_activation = (i % 4 == 0) ? 8'hFF : (i % 4 == 1) ? 8'h00 : (i % 4 == 2) ? 8'hFE : 8'h01;
            i_sum = (i % 4 == 0) ? 24'hFFFFFF : (i % 4 == 1) ? 24'h000000 : (i % 4 == 2) ? 24'h000001 : 24'hFFFFFE;
        end
        // 8. 随机激励（大样本覆盖）
        else if (i < 1000) begin
            i_weight = $urandom(seed_w) % 256; seed_w = seed_w + 1;
            i_activation = $urandom(seed_a) % 256; seed_a = seed_a + 1;
            i_sum = $urandom(seed_s) % 16777216; seed_s = seed_s + 1;
        end
        // 9. 高相关性/反相关性激励
        else if (i < 2000) begin
            i_weight = $urandom(seed_w) % 256;
            i_activation = i_weight ^ (i[7:0]);
            i_sum = ($urandom(seed_s) ^ (i_weight << 8)) & 24'hFFFFFF;
        end
        // 10. 其它特殊激励
        else if (i < 2500) begin
            i_weight = (i % 2) ? (i[7:0]) : (8'hFF - i[7:0]);
            i_activation = (i % 4) ? (8'hAA) : (8'h55);
            i_sum = i * 98765 & 24'hFFFFFF;
        end
        // 11. 仍然用随机极值补充
        else begin
            i_weight = $random % 256;
            i_activation = $random % 256;
            i_sum = $random % 16777216;
        end

        @(posedge clock); #1;
        if (^o_sum === 1'bX)
            $display("idx=%4d i_weight=%3d i_activation=%3d i_sum=%8d o_sum=       X", i, i_weight, i_activation, i_sum);
        else
            $display("idx=%4d i_weight=%3d i_activation=%3d i_sum=%8d o_sum=%8d", i, i_weight, i_activation, i_sum, o_sum);
    end
    #10 $finish;
end

endmodule
