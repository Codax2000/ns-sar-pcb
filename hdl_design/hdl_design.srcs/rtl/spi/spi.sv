module spi #(
    parameter DATA_WIDTH=16,
    parameter ADDR_WIDTH=4
) (
    // SPI interface
    input logic i_scl,
    input logic i_csb,
    input logic i_mosi,
    output logic o_miso,

    // FIFO interface
    logic o_start_coversion,

    // Mem read interface
    output logic [ADDR_WIDTH-1:0] o_rd_addr,
    input logic [DATA_WIDTH-1:0] i_memory_data,

    // register interface
    if_reg i_if_reg
);

    enum logic [1:0] {
        READY=2'b00,
        RECEIVE_DATA=2'b01,
        SEND_REGISTER=2'b10,
        SEND_MEMORY=2'b11
    } ps_e, ns_e;

    enum logic [1:0] {
        READ_REG=2'h0,
        WRITE_REG=2'h1,
        MEM_READ=2'h2,
        BEGIN_SAMPLE=2'h3
    } command;

    logic  [3:0] data_send_counter_r, data_send_counter_n;
    logic [15:0] nfft_send_counter_r, nfft_send_counter_n;
    logic [15:0] nfft;

    logic  [7:0] miso_r, miso_n, mosi_r, mosi_n;
    logic  [1:0] reg_index;

    logic data_send_done;
    logic next_state_is_transfer_register;
    logic next_state_is_transfer_memory;
    logic next_state_is_begin_sample;
    logic load_mem_lsb, load_mem_msb;
    logic increment_nfft_counter;

    assign next_state_is_transfer_register = (ps_e == RECEIVE_DATA) && (data_send_counter_r == 4'h7) && (command != MEM_READ);
    assign next_state_is_transfer_memory   = (ps_e == RECEIVE_DATA) && (data_send_counter_r == 4'h7) && (command == MEM_READ);
    assign next_state_is_begin_sample      = (ps_e == RECEIVE_DATA) && (data_send_counter_r == 4'h7) && (command == BEGIN_SAMPLE);
    assign data_send_done = ((ps_e == SEND_REGISTER) && (data_send_counter_r == 4'h3)) || // register send case
                            ((ps_e == SEND_MEMORY)   && (nfft_send_counter_r == (nfft - 1)) && (data_send_counter_r == 4'hF));
    assign load_mem_lsb = ((ps_e == SEND_MEMORY) && (data_send_counter_r == 4'hF)) || next_state_is_transfer_memory;
    assign load_mem_msb = ((ps_e == SEND_MEMORY) && (data_send_counter_r == 4'h7));
    assign increment_nfft_counter = data_send_done || ((ps_e == SEND_REGISTER) && (ns_e == SEND_MEMORY));
    assign command = mosi_r[7:6];
    assign reg_index = mosi_r[5:4];

    // counting logic
    assign nfft = 1 << i_if_reg.nfft_power;
    assign nfft_send_counter_n = increment_nfft_counter ? nfft_send_counter_r + 1 : nfft_send_counter_r;
    assign data_send_counter_n =    ((ps_e == READY)) ||
                                    ((ps_e == RECEIVE_DATA)  && (data_send_counter_r == 4'h7)) ||
                                    ((ps_e == SEND_MEMORY)   && (data_send_counter_r == 4'hF)) || 
                                    ((ps_e == SEND_REGISTER) && (data_send_counter_r == 4'h3)) ? 4'h0 : data_send_counter_r + 1;

    // shifting logic
    always_comb begin
        if (next_state_is_transfer_register) begin
            if (next_state_is_begin_sample)
                miso_n = 4'b1010;
            else begin
                case (reg_index)
                    2'h0: miso_n = {i_if_reg.nfft_power, 4'h0};
                    2'h1: miso_n = {i_if_reg.osr_power, i_if_reg.dwa, 4'h0};
                    2'h2: miso_n = {i_if_reg.clk_div, 4'h0};
                    2'h3: miso_n = {o_start_coversion, 1'b0, 2'h0, 4'h0};
                    default: miso_n = 8'h0; // should never be touched
                endcase
            end
        end else if (load_mem_lsb)
            miso_n = i_memory_data[7:0];
        else if (load_mem_msb)
            miso_n = i_memory_data[15:8];
        else // if not load, then shift
            miso_n = {miso_r[6:0], 1'b0};
    end

    assign o_miso = mosi_r[7]; // LSB-first shifting
    assign mosi_n = ps_e == READY ? {mosi_r[6:0], i_mosi} :
                    ps_e == RECEIVE_DATA ? {mosi_r[6:0], i_mosi} : 8'h00;
    assign o_rd_addr = nfft_send_counter_r;
    assign o_start_coversion = next_state_is_begin_sample;

    // next state logic
    always_comb begin
        case (ps_e)
            READY:          ns_e =  RECEIVE_DATA;
            RECEIVE_DATA:   ns_e =  next_state_is_transfer_memory ? SEND_MEMORY :
                                    next_state_is_transfer_register ? SEND_REGISTER : RECEIVE_DATA;
            SEND_REGISTER:  ns_e =  data_send_done ? READY : SEND_REGISTER;
            SEND_MEMORY:    ns_e =  data_send_done ? READY : SEND_MEMORY;
            default:        ns_e =  READY;
        endcase
    end

    // clocked logic
    always_ff @(posedge i_scl or negedge i_csb) begin
        if (i_csb) begin
            miso_r <= 8'h00;
            mosi_r <= 8'h00;
            ps_e <= READY;
            data_send_counter_r <= 4'h0;
            nfft_send_counter_r <= 16'h0000;
        end else begin
            miso_r <= miso_n;
            mosi_r <= mosi_n;
            ps_e <= ns_e;
            data_send_counter_r <= data_send_counter_n;
            nfft_send_counter_r <= nfft_send_counter_n;
        end
    end

endmodule