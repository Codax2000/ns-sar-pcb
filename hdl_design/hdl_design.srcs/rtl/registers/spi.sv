module spi (

    input  logic scl,
    input  logic mosi,
    output logic miso,
    output logic miso_en,
    input  logic cs_b,

    // system clock
    input  logic sysclk,
    input  logic rst,

    output logic                      if_req,
    output logic                      if_rd_en,
    output logic               [14:0] if_addr,
    output logic               [15:0] if_wr_data,

    input  logic               [15:0] if_rd_data,
    input  logic                      if_rd_err,
    input  logic                      if_wr_err
);

    logic        load_address;
    logic        load_miso_shift_reg;
    logic [3:0]  byte_count;
    logic [15:0] miso_shift_reg;
    logic [15:0] mosi_shift_reg;

    logic rd_en, wr_en;

    // SPI-clock-domain request side. Synced to sysclk below.
    logic        spi_req;
    logic        spi_rd_en;
    logic [14:0] spi_addr;
    logic [15:0] spi_wr_data;

    // Held sysclk-domain read data for the SPI shift register.
    logic [15:0] if_rd_data_held;

    enum logic [1:0] {ADDR, RECEIVE_WRITE, DRIVE_READ} addr_state;

    always_ff @(posedge scl or posedge cs_b) begin
        if (cs_b) begin
            addr_state          <= ADDR;
            load_address        <= 0;
            byte_count          <= 0;
            mosi_shift_reg      <= 0;
            load_miso_shift_reg <= 0;
            spi_rd_en           <= 0;
            spi_addr            <= 0;
            spi_wr_data         <= 0;
            rd_en               <= 0;
            wr_en               <= 0;
        end
        else begin
            // always increment
            mosi_shift_reg <= {mosi_shift_reg[14:0], mosi};
            byte_count <= byte_count + 1;
            rd_en <= (byte_count == 4'hF) && (spi_rd_en);
            wr_en <= (byte_count == 4'hF) && (addr_state == RECEIVE_WRITE);

            // state transitions
            if ((byte_count == 0) && (addr_state == ADDR)) begin
                spi_rd_en <= mosi;
            end
            else if (byte_count == 15) begin
                if (addr_state == ADDR) begin
                    spi_addr[14:0] <= {mosi_shift_reg[13:0], mosi};
                    if (mosi_shift_reg[14])
                        addr_state    <= DRIVE_READ;
                    else
                        addr_state    <= RECEIVE_WRITE;
                end
            end

            if (rd_en || wr_en) begin
                if (spi_addr == 15'h7FFF)
                    spi_addr <= spi_addr;
                else
                    spi_addr <= spi_addr + 1;
            end

            // load write data
            if (byte_count == 4'hF && addr_state == RECEIVE_WRITE)
                spi_wr_data <= {mosi_shift_reg[14:0], mosi};
            else
                spi_wr_data <= 0;
        end
    end

    assign spi_req = rd_en || wr_en;

    // ------------------------------------------------------------------
    // CDC: SPI clock -> sysclk. Req is multi-cycle in SPI; sync then
    // edge-detect to a single-cycle sysclk pulse. Addr/data ride the
    // same synchronizer and are sampled with that pulse.
    // ------------------------------------------------------------------
    logic        sync_req;
    logic        sync_rd_en;
    logic [14:0] sync_addr;
    logic [15:0] sync_wr_data;

    sync_nstage #(.N_BITS(33)) i_spi_to_sysclk_sync (
        .src_data ({
            spi_req,
            spi_rd_en,
            spi_addr,
            spi_wr_data
        }),
        .dest_data ({
            sync_req,
            sync_rd_en,
            sync_addr,
            sync_wr_data
        }),
        .src_clk(1'b0),
        .dest_clk(sysclk),
        .dest_clk_rst(rst)
    );

    posedge_detector #(
        .N_CYCLES(3)
    ) i_req_posedge_detector (
        .clk(sysclk),
        .rst(rst),
        .in (sync_req),
        .posedge_detected(if_req)
    );

    assign if_rd_en   = sync_rd_en;
    assign if_addr    = sync_addr;
    assign if_wr_data = sync_wr_data;

    // Latch and hold read data in sysclk. The SPI shift register only
    // samples this when a request is in flight, so holding indefinitely
    // is enough (see docs/hdl.rst SPI CDC).
    always_ff @(posedge sysclk) begin
        if (rst)
            if_rd_data_held <= '0;
        else if (if_req)
            if_rd_data_held <= if_rd_data;
    end

    always_ff @(negedge scl or posedge cs_b) begin
        if (cs_b) begin
            miso_shift_reg <= 0;
        end
        else begin
            if (spi_req)
                miso_shift_reg <= if_rd_data_held;
            else
                miso_shift_reg <= {miso_shift_reg[14:0], 1'b0};
        end
    end

    assign miso    = miso_shift_reg[15];
    assign miso_en = addr_state == DRIVE_READ;

    wire _unused_ok = &{1'b0, if_rd_err, if_wr_err};

endmodule