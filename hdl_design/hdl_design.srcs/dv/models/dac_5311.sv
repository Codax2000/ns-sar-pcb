// Behavioral DAC5311. SYNC, SCLK, and DIN in; a real voltage out.
//
// rst_n is active-low, the same polarity as dac_datapath. While reset
// is asserted the converter sits at midscale (code 128, power-down 00),
// which is 128/256 * VDD. It also starts there, so an idle serializer
// that never completes a frame leaves the output at midscale.
//
// A frame is 16 bits, MSB first, sampled on the falling edge of SCLK
// while SYNC is low, and applied on the rising edge of SYNC.
// DB15-14 are don't-care, DB13-12 are PD1/PD0, DB11-4 are the 8-bit
// code, and DB3-0 are don't-care. PD 00 is normal operation. Any other
// power-down code drives 0.0.

module dac_5311 #(
    parameter real VDD = 3.3
) (
    input  logic syncb,
    input  logic sclk,
    input  logic din,
    input  logic rst_n,
    output real  vout
);

    logic [15:0] shreg = 16'h0800;
    logic [7:0]  code  = 8'h80;
    logic [1:0]  pd    = 2'b00;

    always_ff @(negedge sclk or negedge rst_n) begin
        if (!rst_n)
            shreg <= 16'h0800;
        else if (!syncb)
            shreg <= {shreg[14:0], din};
    end

    always_ff @(posedge syncb or negedge rst_n) begin
        if (!rst_n) begin
            code <= 8'h80;
            pd   <= 2'b00;
        end else begin
            pd   <= shreg[13:12];
            code <= shreg[11:4];
        end
    end

    assign vout = (pd == 2'b00) ? (real'(code) * VDD / 256.0) : 0.0;

endmodule
