module spi (
    input  logic scl,
    input  logic mosi,
    output logic miso,
    input  logic cs_b,

    output logic                      if_req,
    output logic                      if_rd_en,
    output logic               [14:0] if_addr,
    output logic                [7:0] if_wr_data,

    input  logic                [7:0] if_rd_data,
    input  logic                      if_rd_err,
    input  logic                      if_wr_err
);

    logic       load_address;
    logic       load_miso_shift_reg;
    logic [2:0] byte_count;
    logic [7:0] miso_shift_reg;
    logic [7:0] mosi_shift_reg;
    logic [1:0] addr_state;

    always_ff @(posedge scl or posedge cs_b) begin
        if (cs_b) begin
            addr_state <= 0;
            load_address <= 0;
            byte_count   <= 0;
            miso_shift_reg <= 0;
            mosi_shift_reg <= 0;
        end
        else begin
            mosi_shift_reg <= {mosi_shift_reg[6:0], mosi};
            byte_count <= byte_count + 1;
            if (load_miso_shift_reg)
                miso_shift_reg <= if_rd_data;
            else
                miso_shift_reg <= {miso_shift_reg[6:0], 1'b0};
            if (byte_count == 7 && (addr_state == 0)) begin
                if_addr[14:8] <= mosi_shift_reg[6:0];
                if_rd_en      <= mosi_shift_reg[7];
            end
            else if (byte_count == 7 && (addr_state == 1))
                if_addr[7:0] <= mosi_shift_reg[6:0];
            
        end
    end

    always_ff @(negedge scl or posedge cs_b) begin
        if (cs_b) begin
            miso <= 0;
        end
        else begin
            miso <= miso_shift_reg[7];
        end
    end

endmodule