module spi (
    input  logic sysclk,
    input  logic rst_n,

    input  logic scl,
    input  logic mosi,
    output logic miso,
    output logic miso_en,
    input  logic cs_b,

    output logic                      if_req,
    output logic                      if_rd_en,
    output logic               [14:0] if_addr,
    output logic               [15:0] if_wr_data,

    input  logic               [15:0] if_rd_data,
    input  logic                      if_rd_err,
    input  logic                      if_wr_err
);

    logic       load_address;
    logic       load_miso_shift_reg;
    logic [3:0] byte_count;
    logic [15:0] miso_shift_reg;
    logic [15:0] mosi_shift_reg;

    logic rd_en, wr_en;
    
    enum logic [1:0] {ADDR, RECEIVE_WRITE, DRIVE_READ} addr_state;

    assign miso_en = 0;

    always_ff @(posedge scl or posedge cs_b) begin
        if (cs_b) begin
            addr_state          <= 0;
            load_address        <= 0;
            byte_count          <= 0;
            miso_shift_reg      <= 0;
            mosi_shift_reg      <= 0;
            load_miso_shift_reg <= 0;
            if_rd_en            <= 0;
            if_addr             <= 0;
            if_wr_data          <= 0;
            rd_en               <= 0;
            wr_en               <= 0;
        end
        else begin
            // always increment
            mosi_shift_reg <= {mosi_shift_reg[14:0], mosi};
            byte_count <= byte_count + 1;
            rd_en <= (byte_count == 4'hF) && (if_rd_en);
            wr_en <= (byte_count == 4'hF) && (addr_state == RECEIVE_WRITE);
            
            // state transitions
            if ((byte_count == 0) && (addr_state == ADDR)) begin
                if_rd_en <= mosi;
            end
            else if (byte_count == 15) begin
                if (addr_state == ADDR) begin
                    if_addr[14:0] <= {mosi_shift_reg[13:0], mosi};
                    if (mosi_shift_reg[14])
                        addr_state    <= DRIVE_READ;
                    else
                        addr_state    <= RECEIVE_WRITE;
                end
                else begin
                    if (if_addr == 15'h7FFF)
                        if_addr <= if_addr;
                    else
                        if_addr <= if_addr + 1;
                end
            end
        end
    end

    assign if_req = rd_en || wr_en;

    always_ff @(negedge scl or posedge cs_b) begin
        if (cs_b) begin
            miso <= 0;
        end
        else begin
            if (if_req)
                miso_shift_reg <= if_rd_data;
            else
                miso_shift_reg <= {miso_shift_reg[14:0], 1'b0};
        end
    end

    assign miso    = miso_shift_reg[15];
    assign miso_en = addr_state == DRIVE_READ;

endmodule