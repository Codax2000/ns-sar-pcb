module dac5311_ctrl (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Sample selected by dsm_bypass_mux.
    input  logic [7:0] i_sine,
    input  logic       i_sine_valid,

    // One SCLK. Each DAC5311 has its own active-low SYNC and DIN.
    // Both SYNC outputs stay high (inactive) until the serializer exists.
    output logic o_sclk,
    output logic o_syncb_dacp,
    output logic o_syncb_dacn,
    output logic o_din_dacp,
    output logic o_din_dacn
);

    logic latch_mode;

    logic        shregp_load, shregn_load;
    logic [15:0] shregp_din, shregn_din;
    logic        shregp_busy, shregn_busy;

    logic o_sclk_en_dacp, o_sclk_en_dacn;
    wire  dacp_power = hwif_out.STATUS.dacp_power.value;
    wire  dacn_power = hwif_out.STATUS.dacn_power.value;

    wire  dacp_ac_en = hwif_out.ENABLE.dacp_mode.value == 1'b1 && hwif_out.ENABLE.dacp_enable.value == 1'b1;
    wire  dacn_ac_en = hwif_out.ENABLE.dacn_mode.value == 1'b1 && hwif_out.ENABLE.dacn_enable.value == 1'b1;

    always_ff @(posedge clk) begin : latch_dac_mode
        if (rst) begin
            // One-shot after reset/ENABLE: load DC or power-down once.
            latch_mode <= 1'b0;
            shregp_load <= 1'b0;
            shregp_din  <= 16'h0000;
            shregn_load <= 1'b0;
            shregn_din  <= 16'h0000;
        end
        else begin
            latch_mode <= 1'b1;

            if (latch_mode == 1'b0) begin : shregp_load_dc
                if (hwif_out.ENABLE.dacp_enable.value == 1'b0) begin : shregp_load_dacp_disable
                    shregp_load <= 1'b1;
                    shregp_din  <= {dacp_power, !dacp_power, 14'h0000};
                end : shregp_load_dacp_disable
                else if (hwif_out.ENABLE.dacp_mode.value == 1'b0) begin : shregp_load_dacp_dc
                    shregp_load <= 1'b1;
                    shregp_din  <= {2'b00, hwif_out.DACP_DC_VALUE.dc_value.value, 6'h00};
                end : shregp_load_dacp_dc
            end : shregp_load_dc
            else if (i_sine_valid && dacp_ac_en && (!shregp_busy)) begin : shregp_load_ac
                shregp_load <= 1'b1;
                shregp_din  <= {2'b00, i_sine, 6'h00};
            end : shregp_load_ac
            else begin : shregp_load_idle
                shregp_load <= 1'b0;
            end : shregp_load_idle

            if (latch_mode == 1'b0) begin : shregn_load_dc
                if (hwif_out.ENABLE.dacn_enable.value == 1'b0) begin : shregn_load_dacn_disable
                    shregn_load <= 1'b1;
                    shregn_din  <= {dacn_power, !dacn_power, 14'h0000};
                end : shregn_load_dacn_disable
                else if (hwif_out.ENABLE.dacn_mode.value == 1'b0) begin : shregn_load_dacn_dc
                    shregn_load <= 1'b1;
                    shregn_din  <= {2'b00, hwif_out.DACN_DC_VALUE.dc_value.value, 6'h00};
                end : shregn_load_dacn_dc
            end : shregn_load_dc
            else if (i_sine_valid && dacn_ac_en && (!shregn_busy)) begin : shregn_load_ac
                shregn_load <= 1'b1;
                shregn_din  <= {2'b00, (~i_sine + 8'h01), 6'h00};
            end : shregn_load_ac
            else begin : shregn_load_idle
                shregn_load <= 1'b0;
            end : shregn_load_idle
        end
    end : latch_dac_mode;

    dac5311_shift_reg u_shift_reg_out_dacp (
        .rst(rst),
        .clk(clk),
        .load(shregp_load),
        .din(shregp_din),
        .busy(shregp_busy),
        .sclk(o_sclk_en_dacp),
        .syncb(o_syncb_dacp),
        .dout(o_din_dacp)
    );

    dac5311_shift_reg u_shift_reg_out_dacn (
        .rst(rst),
        .clk(clk),
        .load(shregn_load),
        .din(shregn_din),
        .busy(shregn_busy),
        .sclk(o_sclk_en_dacn),
        .syncb(o_syncb_dacn),
        .dout(o_din_dacn)
    );

    assign o_sclk = o_sclk_en_dacp || o_sclk_en_dacn;
    
endmodule
