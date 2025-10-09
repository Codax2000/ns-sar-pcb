module spi #(
    parameter ADDR_WIDTH = 15,
    parameter DATA_WIDTH = 16
)(
    input  logic        scl,        // SPI clock
    input  logic        mosi,       // Master Out Slave In
    output logic        miso,       // Master In Slave Out
    input  logic        cs_b,       // Chip Select (active low)

    output logic [DATA_WIDTH-1:0] reg_wr_data,
    input  logic [DATA_WIDTH-1:0] reg_rd_data,
    output logic [ADDR_WIDTH-1:0] reg_addr,
    output logic                  reg_rd_en,
    output logic                  reg_wr_en,

    input logic rst_b
);

    typedef enum logic [1:0] {
        RESET,
        ADDR_DECODE,
        REG_RECEIVE,
        REG_SEND
    } spi_state_e;

    spi_state_e state, next_state;

    logic [$clog2(ADDR_WIDTH+1)-1:0] addr_count;
    logic [ADDR_WIDTH:0] addr_shift;
    logic [DATA_WIDTH-1:0] rx_shift, tx_shift;
    logic [$clog2(DATA_WIDTH)-1:0] bit_cnt;
    logic miso_n;

    // FSM state transition
    always_ff @(posedge scl or posedge cs_b or negedge rst_b) begin
        if (cs_b || (!rst_b))
            state <= ADDR_DECODE;
        else
            state <= next_state;
    end

    // FSM next state logic
    always_comb begin
        case (state)
            ADDR_DECODE: begin
                if (addr_count == ADDR_WIDTH)
                    next_state = addr_shift[ADDR_WIDTH-1] ? REG_SEND : REG_RECEIVE;
                else
                    next_state = ADDR_DECODE;
            end
            REG_RECEIVE: next_state = REG_RECEIVE; // burst mode write
            REG_SEND   : next_state = REG_SEND;    // burst mode read
            RESET      : next_state = ADDR_DECODE;
            default    : next_state = RESET;
        endcase
    end

    // Shift logic reset on cs_b deassertion
    always_ff @(posedge scl or posedge cs_b or negedge rst_b) begin
        if (cs_b || (!rst_b)) begin
            addr_count  <= 0;
            addr_shift  <= 0;
            rx_shift    <= 0;
            tx_shift    <= 0;
            bit_cnt     <= 0;
            reg_rd_en   <= 0;
            reg_wr_en   <= 0;
        end else begin
            case (state)

                ADDR_DECODE: begin
                    addr_shift <= {addr_shift[ADDR_WIDTH-1:0], mosi};
                    if (addr_count < ADDR_WIDTH)
                        addr_count <= addr_count + 1;
                end

                REG_RECEIVE: begin
                    rx_shift <= {rx_shift[DATA_WIDTH-2:0], mosi};
                    if (bit_cnt == DATA_WIDTH-1) begin
                        bit_cnt <= 0;
                        addr_shift <= addr_shift + 1;
                    end else begin
                        bit_cnt  <= bit_cnt + 1;
                    end
                end

                REG_SEND: begin
                    if (bit_cnt == 0)
                        tx_shift <= {reg_rd_data[DATA_WIDTH-2:0], 1'b0};
                    else
                        tx_shift <= {tx_shift[DATA_WIDTH-2:0], 1'b0};
                    bit_cnt  <= bit_cnt + 1;
                    if ((bit_cnt == (DATA_WIDTH-1)))
                        addr_shift <= addr_shift + 1;
                end
            endcase
        end
    end

    always_ff @(negedge scl or posedge cs_b or negedge rst_b) begin
        if (cs_b || (!rst_b))
            miso <= 0;
        else
            miso <= miso_n;
    end

    assign reg_rd_en   = ((state == ADDR_DECODE) && (next_state == REG_SEND)) ||
                         ((state == REG_SEND)    && (bit_cnt == DATA_WIDTH-1));
    assign reg_wr_en   = ((state == REG_RECEIVE) && (bit_cnt == DATA_WIDTH-1));
    assign reg_wr_data = {rx_shift[DATA_WIDTH-2:0], mosi};
    assign miso_n      = (state == REG_SEND) && (bit_cnt == 0) ? reg_rd_data[DATA_WIDTH-1] : 
                         (state == REG_SEND)                   ? tx_shift[DATA_WIDTH-1]    : 0;
    assign reg_addr    = (state == ADDR_DECODE) ? {addr_shift[ADDR_WIDTH-1:0], mosi} : 
                         (state == REG_RECEIVE) ? addr_shift                         : addr_shift + 1;

endmodule