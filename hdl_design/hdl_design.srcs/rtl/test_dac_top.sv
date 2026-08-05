
module test_dac_top (
    // system clock and reset
    input sysclk,
    input arst_n,
    
    // SPI interfaces    
    input  logic csb,
    input  logic scl,
    input  logic mosi,
    output logic miso,
    output logic miso_en,

    // sinegen DAC signals
    output logic sinegen_syncb,
    output logic sinegen_sclk,
    output logic sinegen_dinp,
    output logic sinegen_dinn
);

    // Sync reset generation
    logic rst_n;

    sync_nstage #(.N_BITS(1)) i_rst_sync (
        .src_data(arst_n),
        .dest_data(rst_n),
        .src_clk(1'b0),
        .dest_clk(sysclk),
        .dest_clk_rst(1'b0)
    );

    // Register interface
    logic        dac_if_req;
    logic        dac_if_rd_en;
    logic [14:0] dac_if_addr;
    logic [15:0] dac_if_wr_data;
    logic [15:0] dac_if_rd_data;
    logic        dac_if_rd_err;
    logic        dac_if_wr_err;

    spi i_dac_spi (
        .sysclk(sysclk),
        .rst_n (rst_n),

        .scl    (scl),
        .mosi   (mosi),
        .cs_b   (csb),
        .miso   (miso),
        .miso_en(miso_en),

        .if_req    (dac_if_req    ),
        .if_rd_en  (dac_if_rd_en  ),
        .if_addr   (dac_if_addr   ),
        .if_wr_data(dac_if_wr_data),
        .if_rd_data(dac_if_rd_data),
        .if_rd_err (dac_if_rd_err ),
        .if_wr_err (dac_if_wr_err )
    );

    // Sync-to-sysclk
    logic        sysclk_dac_if_req;  
    logic        sysclk_dac_if_req_posedge;    
    logic        sysclk_dac_if_rd_en;  
    logic [3:0]  sysclk_dac_if_addr; 
    logic [15:0] sysclk_dac_if_wr_data;
    logic [15:0] sysclk_dac_if_rd_data;
    logic        sysclk_dac_if_rd_err;
    logic        sysclk_dac_if_wr_err;

    sync_nstage #(.N_BITS(22)) i_spi_to_sysclk_sync (
        .src_data ({
            dac_if_req, 
            dac_if_rd_en, 
            dac_if_addr[3:0], 
            dac_if_wr_data
        }),
        .dest_data ({
            sysclk_dac_if_req, 
            sysclk_dac_if_rd_en, 
            sysclk_dac_if_addr, 
            sysclk_dac_if_wr_data
        }),
        .src_clk(0),
        .dest_clk(sysclk),
        .dest_clk_rst(!rst_n)
    );

    posedge_detector #(
        .N_CYCLES(3)
    ) i_req_posedge_detector (
        .clk(sysclk),
        .rst(!rst_n),
        .in (sysclk_dac_if_req),
        .posedge_detected(sysclk_dac_if_req_posedge)
    );

    dac_regs_mod_pkg::dac_regs__in_t  hwif_in;
    dac_regs_mod_pkg::dac_regs__out_t hwif_out;

    dac_regs_mod i_registers (
        .clk(sysclk),
        .rst(!rst_n),

        .s_cpuif_req      ( sysclk_dac_if_req_posedge),
        .s_cpuif_req_is_wr(!sysclk_dac_if_rd_en),
        .s_cpuif_addr     ({sysclk_dac_if_addr[3:1], 1'b0}),
        .s_cpuif_wr_data  ( sysclk_dac_if_wr_data),
        .s_cpuif_wr_biten ( 16'hFFFF),
        .s_cpuif_rd_err   ( sysclk_dac_if_rd_err),
        .s_cpuif_rd_data  ( sysclk_dac_if_rd_data),
        .s_cpuif_wr_err   ( sysclk_dac_if_wr_err),

        .hwif_in(hwif_in),
        .hwif_out(hwif_out)
    );

    always_ff @(posedge sysclk) begin
        if (!rst_n)
            dac_if_rd_data <= 0;
        else begin
            if (sysclk_dac_if_req_posedge)
                dac_if_rd_data <= sysclk_dac_if_rd_data;
        end
    end

    assign dac_if_rd_err  = 0;
    assign dac_if_wr_err  = 0;

    // TODO: assign this to 1 when DSM is locked
    assign hwif_in.STATUS.dsm_locked.next = 0;

endmodule