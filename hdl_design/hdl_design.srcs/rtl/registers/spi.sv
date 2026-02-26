module spi #(
    parameter ADDR_BYTES = 2
)(
    input  logic scl,
    input  logic mosi,
    output logic miso,
    input  logic cs_b
);

    logic                      if_req;
    logic                      if_rd_en;
    logic [(8*ADDR_BYTES)-1:0] if_addr;
    logic                [7:0] if_wr_data;
    logic                [7:0] if_rd_data;

    logic                      if_rd_err;
    logic                      if_wr_err;

    typedef enum logic [2:0] {
        RECEIVE_HEADER,
        RECEIVE_WR_DATA,
        SEND_RD_DATA,
        CHECK_AND_SEND_HEADER_PARITY,
        CHECK_AND_SEND_DATA_PARITY,
        DONE
    } spi_state_e;

    // Group: registers (should total )
    spi_state_e                        current_state, next_state;
    logic [2:0]                        bit_counter;
    logic [$clog2(ADDR_BYTES+1)-1:0]   head_byte_counter;
    logic [6:0]                        data_byte_counter;
    logic [ADDR_BYTES:0][7:0]          header;
    logic [6:0]                        n_expected_transactions;
    logic [7:0]                        mosi_shift_register, miso_shift_register;
    logic                              current_parity;
    logic                              if_err;

    // Group: wires/enables
    logic increment_bit_counter;
    logic increment_head_byte_counter;
    logic increment_data_byte_counter;
    logic load_header;
    logic load_miso_shift_register;
    logic load_wr_data;
    logic flip_parity;
    logic bad_parity;

    // Variable: bit_counter_done
    // Utility variable to avoid having to type it out every time
    logic bit_counter_done;
    assign bit_counter_done = bit_counter == 3'h7;

    assign if_rd_en = header[0][0];
    assign if_addr = header[ADDR_BYTES:1];
    assign n_expected_transactions = header[0][7:1];
    assign load_wr_data = bit_counter_done && (current_state == RECEIVE_WR_DATA);
    assign flip_parity = 0;
    assign increment_head_byte_counter = current_state == CHECK_AND_SEND_HEADER_PARITY;
    assign increment_data_byte_counter = current_state == CHECK_AND_SEND_DATA_PARITY;
    assign increment_bit_counter = !((current_state == CHECK_AND_SEND_DATA_PARITY) || 
                                     (current_state == CHECK_AND_SEND_HEADER_PARITY));
    assign load_header = ((current_state == RECEIVE_HEADER) && (bit_counter_done));
    assign miso = 0;
    assign bad_parity = 0;

    always_ff @(negedge scl or negedge cs_b) begin
        if (!cs_b) begin
            current_state <= next_state;

            if (increment_bit_counter)
                bit_counter <= bit_counter + 3'h1;

            if (increment_data_byte_counter)
                data_byte_counter <= data_byte_counter + 7'h01;

            if (load_header)
                header[head_byte_counter] <= {mosi, mosi_shift_register[7:1]};

            if (load_miso_shift_register)
                miso_shift_register <= if_rd_data;
            else
                miso_shift_register <= {1'b0, miso_shift_register[7:1]};

            if (flip_parity)
                current_parity <= !current_parity;

            if (load_wr_data)
                if_wr_data <= mosi_shift_register;

            if (if_wr_err || if_rd_err)
                if_err <= 1;
        end
        else begin
            current_state <= RECEIVE_HEADER;
            bit_counter <= 0;
            head_byte_counter <= 0;
            data_byte_counter <= 0;
            header <= 0;
            miso_shift_register <= 0;
            current_parity <= 1;
            if_err <= 0;
        end
    end

    always_ff @(posedge scl) // no reset needed here, since things are protected from mosi_shift_register
        mosi_shift_register <= {mosi, mosi_shift_register[7:1]};

    always_comb begin : next_state_logic
        case (current_state)
            RECEIVE_HEADER : next_state = bit_counter_done ? CHECK_AND_SEND_HEADER_PARITY : RECEIVE_HEADER;
            RECEIVE_WR_DATA: next_state = bit_counter_done ? CHECK_AND_SEND_DATA_PARITY   : RECEIVE_WR_DATA;
            SEND_RD_DATA   : next_state = bit_counter_done ? CHECK_AND_SEND_DATA_PARITY   : SEND_RD_DATA;
            CHECK_AND_SEND_HEADER_PARITY : begin
                if (bad_parity)
                    next_state = DONE;
                else
                if (head_byte_counter == ADDR_BYTES) begin
                    if (if_rd_data)
                        next_state = SEND_RD_DATA;
                    else
                        next_state = RECEIVE_WR_DATA;
                end
                else begin
                    next_state = RECEIVE_HEADER;
                end
            end
            CHECK_AND_SEND_DATA_PARITY : begin
                if (bad_parity || (n_expected_transactions == data_byte_counter))
                    next_state = DONE;
                else
                if (if_rd_en)
                    next_state = SEND_RD_DATA;
                else
                    next_state = RECEIVE_WR_DATA;
            end
            default: next_state = DONE;
        endcase
    end : next_state_logic
endmodule