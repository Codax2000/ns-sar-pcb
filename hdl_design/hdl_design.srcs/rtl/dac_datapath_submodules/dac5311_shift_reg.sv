/**
 * Shift register for DAC5311 control logic.
 *
 * On load, captures din, drops SYNCb, and starts SCLK (clk/4) on the next
 * sysclk. Phase: rise, hold-high, fall, hold-low. Shift on the rising phase
 * so dout is stable for the DAC5311 falling-edge sample; the first rising
 * edge does not shift (MSB already on dout). After the last falling edge,
 * wait SYNCB_LAG_CYCLES sysclks before raising SYNCb.
 */

module dac5311_shift_reg #(
    parameter int unsigned SYNCB_LAG_CYCLES = 9
) (
    input  logic        rst,
    input  logic        clk,

    // input interface
    input  logic        load,
    input  logic [15:0] din,
    output logic        busy,

    // output signals (DAC5311 pins)
    output logic        sclk,
    output logic        syncb,
    output logic        dout
);

    localparam int unsigned LAG_W =
        (SYNCB_LAG_CYCLES <= 1) ? 1 : $clog2(SYNCB_LAG_CYCLES + 1);

    logic               shift;
    logic [LAG_W-1:0]   lag_cnt;   // sysclks left before raising SYNCb
    logic [1:0]         clk_div;   // 0=rise, 1=hold high, 2=fall, 3=hold low
    logic [4:0]         bits_left; // falling edges still to issue
    logic [15:0]        shift_reg;

    assign dout = shift_reg[15];
    // Rising phase after at least one falling sample; skip first rise.
    assign shift = busy && (lag_cnt == '0) && (clk_div == 2'd0) &&
                   (bits_left != 5'd16);

    always_ff @(posedge clk) begin : shift_output
        if (rst) begin
            shift_reg <= 16'h0000;
            busy      <= 1'b0;
            syncb     <= 1'b1;
            sclk      <= 1'b0;
            bits_left <= 5'd0;
            lag_cnt   <= '0;
            clk_div   <= 2'd0;
        end
        else if (load && !busy) begin
            shift_reg <= din;
            busy      <= 1'b1;
            syncb     <= 1'b0;
            sclk      <= 1'b0;
            bits_left <= 5'd16;
            lag_cnt   <= '0;
            clk_div   <= 2'd0;
        end
        else if (busy) begin
            if (lag_cnt != '0) begin
                sclk <= 1'b0;
                if (lag_cnt == LAG_W'(1)) begin
                    syncb   <= 1'b1;
                    busy    <= 1'b0;
                    lag_cnt <= '0;
                    clk_div <= 2'd0;
                end
                else begin
                    lag_cnt <= lag_cnt - LAG_W'(1);
                end
            end
            else begin
                unique case (clk_div)
                    2'd0: begin
                        // Rising edge this cycle.
                        sclk    <= 1'b1;
                        clk_div <= 2'd1;
                        if (shift)
                            shift_reg <= shift_reg << 1;
                    end
                    2'd1: begin
                        // Hold high.
                        sclk    <= 1'b1;
                        clk_div <= 2'd2;
                    end
                    2'd2: begin
                        // Falling edge this cycle (DAC samples dout).
                        sclk      <= 1'b0;
                        bits_left <= bits_left - 5'd1;
                        clk_div   <= 2'd3;
                        if (bits_left == 5'd1) begin
                            if (SYNCB_LAG_CYCLES == 0) begin
                                syncb   <= 1'b1;
                                busy    <= 1'b0;
                                clk_div <= 2'd0;
                            end
                            else begin
                                lag_cnt <= LAG_W'(SYNCB_LAG_CYCLES);
                            end
                        end
                    end
                    default: begin
                        // Hold low for the fourth sysclk of the SCLK period.
                        sclk    <= 1'b0;
                        clk_div <= 2'd0;
                    end
                endcase
            end
        end
    end : shift_output

endmodule
