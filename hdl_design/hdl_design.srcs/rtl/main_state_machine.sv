module main_state_machine (
    input logic i_arst_b,
    input logic i_clk,

    // START FIFO handshake
    output logic o_ready,
    input logic i_start,

    input logic i_conversion_done,
    output logic o_start_coversion
);

    enum logic {READY=1'b0, CONVERT=1'b1} ps_e, ns_e;

    assign o_ready = ps_e == READY;
    assign o_start_coversion = (ps_e == READY) && i_start;

    always_comb begin
        case (ps_e)
            READY:
                ns_e = i_start ? CONVERT : READY;
            CONVERT:
                ns_e = i_conversion_done ? READY : CONVERT;
        endcase
    end

    always_ff @(posedge i_clk or negedge i_arst_b) begin
        if (!i_arst_b)
            ps_e <= READY;
        else
            ps_e <= ns_e;
    end

endmodule