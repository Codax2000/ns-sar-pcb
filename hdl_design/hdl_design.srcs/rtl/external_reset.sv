module external_reset #(
    parameter RESET_COUNT = 15
) (
    input logic arst,

    input logic clk,
    output logic rst
);

    logic [$clog2(RESET_COUNT)-1:0] reset_counter;

    always @(posedge arst or posedge clk) begin
        if (arst)
            reset_counter <= 0;
        else begin
            if (reset_counter != RESET_COUNT)
                reset_counter <= reset_counter + 1;
        end
    end

    assign rst = reset_counter != RESET_COUNT;

endmodule