module latencyInsensitiveAdder (
    input   logic           clk,
    input   logic           rst_n,

    // Source Interface (input operands)
    input   logic [31:0]    in_a,
    input   logic [31:0]    in_b,
    input   logic           in_valid,
    output  logic           in_ready,

    // Sink Interface (output result)
    output  logic [31:0]    sum,
    output  logic           out_valid,
    input   logic           out_ready
);

    logic [31:0] sum_reg;
    logic        compute_done_state;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            sum_reg            <= 32'd0;
            compute_done_state <= 1'b0;
        end
        else begin
            if (in_valid && in_ready) begin
                sum_reg            <= in_a + in_b;
                compute_done_state <= 1'b1;
            end
            else if (out_valid && out_ready) begin
                sum_reg            <= 32'd0;
                compute_done_state <= 1'b0;
            end
        end
    end

    always_comb begin
        if (compute_done_state) begin
            in_ready  = 1'b0;
            out_valid = 1'b1;
        end
        else begin
            in_ready  = 1'b1;
            out_valid = 1'b0;
        end
    end

    assign sum = sum_reg;

endmodule
