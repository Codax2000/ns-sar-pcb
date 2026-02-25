module spi #(
    parameter ADDR_BYTES = 2,
    parameter REGISTER_BYTES = 2
)(
    input  logic        scl, 
    input  logic        mosi,
    output logic        miso,
    input  logic        cs_b
);

    typedef enum logic [2:0] {
        RECEIVE_HEADER,
        RECEIVE_ADDR,
        RECEIVE_WR_DATA,
        SEND_RD_DATA,
        CHECK_AND_SEND_WRITE_PARITY,
        CHECK_AND_SEND_READ_PARITY,
        DONE
    } spi_state_e;

    logic [ADDR_BYTES-1:0][7:0] reg_addr;

    logic [7:0] mosi_shift_register;
    logic [7:0] miso_shift_register;
    logic       current_parity, next_parity;

    spi_state_e current_state, next_state;
    logic [2:0] byte_counter;
    logic [$clog2(ADDR_BYTES)-1:0] address_counter;
    logic [6:0] transaction_count, n_expected_transactions;

    logic shift_mosi;
    logic increment_address_counter;
    logic increment_transaction_count;
    logic transaction_is_read

    assign miso = 0;

    always_ff @(posedge scl or posedge cs_b) begin : state_transition
        if (cs_b) begin
            current_state <= RECEIVE_HEADER;
            current_parity <= 1;
            byte_counter <= 0;
            n_expected_transactions <= 0;
        end
        else begin
            current_state <= next_state;
            byte_counter  <= (current_state == next_state) ? byte_counter + 1 : 0;
            if (current_state == RECEIVE_HEADER && next_state == CHECK_AND_SEND_WRITE_PARITY)
                n_expected_transactions <= mosi_shift_register[6:0];
            if (increment_address_counter)
                address_counter <= address_counter + 1;
            if (increment_transaction_count)
                address_counter <= 
        end
    end : state_transition

    always_comb begin : next_state_logic
        case (current_state)
            RECEIVE_HEADER : next_state = byte_counter == 3'h7 ? 
                                          CHECK_AND_SEND_WRITE_PARITY : 
                                          RECEIVE_HEADER;
            RECEIVE_ADDR : next_state = byte_counter == 3'h7 ?
                                        CHECK_AND_SEND_WRITE_PARITY :
                                        RECEIVE_ADDR;
            RECEIVE_WR_DATA : next_state = byte_counter == 3'h7 ?
                                           CHECK_AND_SEND_WRITE_PARITY :
                                           RECEIVE_WR_DATA;
            SEND_RD_DATA : next_state = byte_counter == 3'h7 ?
                                        CHECK_AND_SEND_READ_PARITY :
                                        SEND_RD_DATA;
            CHECK_AND_SEND_WRITE_PARITY : begin
                next_state = transaction_count == n_expected_transactions ? DONE :
                             (current_parity ^ mosi) || (current_parity ^ miso) ? DONE :
                             (address_counter != (ADDR_BYTES - 1)) ? RECEIVE_ADDR :
                             RECEIVE_WR_DATA;
            end
            CHECK_AND_SEND_READ_PARITY : next_state = transaction_count == n_expected_transactions ?
                                                      DONE : SEND_RD_DATA;
            default: next_state = DONE;
        endcase
    end : next_state_logic

endmodule