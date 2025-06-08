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

    logic [7:0] mosi_r, mosi_n;
    logic [3:0] mosi_reg_response;
    logic [ADDR_WIDTH-1:0] rd_addr_n;
    logic [DATA_WIDTH-1:0] mosi_mem_response;

    logic [16:0] mem_nfft_counter_n, mem_nfft_counter_r;
    logic [4:0]  mem_data_counter_n, mem_data_counter_r;
    logic [2:0]  reg_response_counter_n, reg_response_counter_r;
    logic [3:0]  receive_data_counter_n, receive_data_counter_r;

    logic write_registers;
    logic [1:0] reg_write_addr;
    logic [3:0] command;

    enum logic [2:0] { // one-hot encoding for FPGA synthesis
        RECEIVE_DATA=3'b001,
        SEND_REGISTER=3'b010,
        SEND_MEMORY=3'b100
    } ps_e, ns_e;

    always_comb begin
        case (ps_e)
            RECEIVE_DATA: begin
                if (receive_data_counter_r == 8) begin
                    if (mosi_r[7:6] == 2'b10)
                        ns_e = SEND_MEMORY;
                    else
                        ns_e = SEND_REGISTER;
                end else
                    ns_e = RECEIVE_DATA;
            end
            SEND_REGISTER: begin
                if (reg_response_counter_r == 4)
                    ns_e = RECEIVE_DATA;
                else
                    ns_e = SEND_REGISTER;
            end
            SEND_MEMORY: begin
                if (mem_nfft_counter_r == (1 << i_if_reg.nfft_power))
                    ns_e = RECEIVE_DATA;
                else
                    ns_e = SEND_MEMORY;
            end
            default: ns_e = RECEIVE_DATA;
        endcase
    end

    assign mosi_n = ps_e == RECEIVE_DATA ? {mosi_r, i_mosi} : mosi_r;
    assign write_registers = (ps_e == RECEIVE_DATA) && (ns_e == SEND_REGISTER);
    assign reg_write_addr = mosi_r[5:4];
    assign command = (1 << mosi_r[7:6]) & {4{ write_registers }};
    assign o_start_coversion = command[3];
    
    assign i_if_reg.i_dwa_wr_en = command[1] && reg_write_addr == 2'h1;
    assign i_if_reg.i_osr_wr_en = command[1] && reg_write_addr == 2'h1;
    assign i_if_reg.i_nfft_wr_en = command[1] && reg_write_addr == 2'h0;
    assign i_if_reg.i_clk_div_wr_en = command[1] && reg_write_addr == 2'h2;

    assign i_if_reg.i_osr_power = mosi_r[3:1];
    assign i_if_reg.i_dwa = mosi_r[0];
    assign i_if_reg.i_nfft_power = mosi_r[3:0];
    assign i_if_reg.i_clk_div = mosi_r[3:0];

    // counter logic for register read/write
    assign receive_data_counter_n = ps_e == RECEIVE_DATA ? receive_data_counter_r + 1 : 0;
    assign reg_response_counter_n = ps_e == SEND_REGISTER ? reg_response_counter_r + 1 : 0;

    // counter logic for mem read/write
    assign mem_nfft_counter_n = 1 << i_if_reg.nfft_power;

    // clocking logic
    always_ff @(posedge i_scl or posedge i_csb) begin
        if (i_csb) begin
            ps_e <= RECEIVE_DATA;
            mem_nfft_counter_r <= 0;
            mem_data_counter_r <= 0;
            reg_response_counter_r <= 0;
            receive_data_counter_r <= 0;
            mosi_r <= 8'h00;
        end else begin
            ps_e <= ns_e;
            mem_nfft_counter_r <= mem_nfft_counter_n;
            mem_data_counter_r <= mem_data_counter_n;
            reg_response_counter_r <= reg_response_counter_n;
            receive_data_counter_r <= receive_data_counter_n;
            mosi_r <= mosi_n;
        end
    end

endmodule