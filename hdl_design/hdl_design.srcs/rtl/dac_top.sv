// Module: dac_top
// Skeleton of the on-fabric DAC datapath.
//
// Ports are the sysclk domain clock and active-low reset, the PeakRDL
// passthrough CPUIF (the ports peakrdl-regblock emits for dac_regs_mod,
// including ack and stall), and the two unsigned 8-bit codes for the
// DAC5311 pair (same names as the generate_dac_values columns
// dacp_value and dacn_value).
//
// DAC5311 SYNC, SCLK, and DIN stay on test_dac_top. Power-down is the
// dacp_power / dacn_power fields in dac_registers.rdl, not extra pins.
//
// Not in this module: CORDIC, phase accumulator, delta-sigma modulator,
// clock divider, and the dac_registers.rdl decode. The CPUIF is one
// loopback word at address 0.

module dac_top (
    // sysclk and synchronous active-low reset.
    // test_dac_top synchronizes arst_n before connecting rst_n.
    input  logic        sysclk,
    input  logic        rst_n,

    // PeakRDL passthrough CPUIF. Data width is the 16-bit dac_regs
    // access. Address width is the 4-bit slice test_dac_top already
    // drives: {sysclk_dac_if_addr[3:1], 1'b0}.
    input  logic        s_cpuif_req,
    input  logic        s_cpuif_req_is_wr,
    input  logic [3:0]  s_cpuif_addr,
    input  logic [15:0] s_cpuif_wr_data,
    input  logic [15:0] s_cpuif_wr_biten,
    output logic        s_cpuif_req_stall_wr,
    output logic        s_cpuif_req_stall_rd,
    output logic        s_cpuif_rd_ack,
    output logic        s_cpuif_rd_err,
    output logic [15:0] s_cpuif_rd_data,
    output logic        s_cpuif_wr_ack,
    output logic        s_cpuif_wr_err,

    // Unsigned DAC5311 codes, 0..255. Midscale 128 is unsigned zero
    // in generate_dac_values (signed code + 128). Held at 0 in reset.
    output logic [7:0]  dacp_value,
    output logic [7:0]  dacn_value
);

    // Unsigned zero of the Python model. Not a programmed DC code.
    localparam logic [7:0] DAC_MIDSCALE = 8'h80;

    logic [15:0] cpuif_loopback;
    logic        cpuif_addr_hit;

    assign cpuif_addr_hit = (s_cpuif_addr == '0);
    // Same-cycle accept. The generated regblock retimes the read and can
    // stall the next write; this stub never stalls.
    assign s_cpuif_req_stall_wr = 1'b0;
    assign s_cpuif_req_stall_rd = 1'b0;
    assign s_cpuif_rd_ack = s_cpuif_req && !s_cpuif_req_is_wr;
    assign s_cpuif_wr_ack = s_cpuif_req &&  s_cpuif_req_is_wr;
    assign s_cpuif_rd_err = s_cpuif_req && !s_cpuif_req_is_wr && !cpuif_addr_hit;
    assign s_cpuif_wr_err = s_cpuif_req &&  s_cpuif_req_is_wr && !cpuif_addr_hit;

    assign dacp_value = rst_n ? DAC_MIDSCALE : '0;
    assign dacn_value = rst_n ? DAC_MIDSCALE : '0;

    always_ff @(posedge sysclk) begin
        if (!rst_n) begin
            cpuif_loopback  <= '0;
            s_cpuif_rd_data <= '0;
        end else begin
            if (s_cpuif_req && s_cpuif_req_is_wr && cpuif_addr_hit) begin
                cpuif_loopback <= (cpuif_loopback & ~s_cpuif_wr_biten)
                                | (s_cpuif_wr_data &  s_cpuif_wr_biten);
            end
            if (s_cpuif_req && !s_cpuif_req_is_wr) begin
                if (cpuif_addr_hit)
                    s_cpuif_rd_data <= cpuif_loopback;
                else
                    s_cpuif_rd_data <= '0;
            end
        end
    end

endmodule
