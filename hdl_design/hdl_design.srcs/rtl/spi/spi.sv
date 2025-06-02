module spi #(
    parameter DATA_WIDTH=16,
    parameter ADDR_WIDTH=4
) (
    if_spi spi_if,
    if_reg reg_if,
    input logic i_clk,

    // FIFO interface
    logic o_start_coversion,
    logic i_fifo_full,

    // Mem read interface
    output logic [ADDR_WIDTH-1:0] o_rd_addr,
    input logic [DATA_WIDTH-1:0] i_memory_data
);

    logic [7:0] miso_r;
    logic [3:0] mosi_reg_response;
    logic [ADDR_WIDTH-1:0] rd_addr_n;
    logic [DATA_WIDTH-1:0] mosi_mem_response;

    logic [15:0] mem_nfft_counter_n, mem_nfft_counter_r;
    logic [3:0]  mem_data_counter_n, mem_data_counter_r;
    logic [1:0]  reg_response_counter_n, reg_response_counter_r;
    logic [2:0]  receive_data_counter_n, receive_data_counter_r;

    enum logic [2:0] { // one-hot encoding for FPGA synthesis
        RECEIVE_DATA=3'b001,
        SEND_REGISTER=3'b010,
        SEND_MEMORY=3'b100
    } ps_e, ns_e;

    always_comb begin
        case (ps_e)
            RECEIVE_DATA: begin
                if (receive_data_counter_r == 3'b111) begin
                    if (miso_r[7:6] == 2'b10)
                        ns_e = SEND_MEMORY;
                    else
                        ns_e = SEND_REGISTER;
                end else
                    ns_e = RECEIVE_DATA
            end
            SEND_REGISTER: begin
                if (reg_response_counter_r == 2'b11)
                    ns_e = RECEIVE_DATA;
                else
                    ns_e = SEND_REGISTER;
            end
            SEND_MEMORY: begin
                if (mem_nfft_counter_r == 16'hffff)
                    ns_e = RECEIVE_DATA;
                else
                    ns_e = SEND_MEMORY;
            end
            default: ns_e = RECEIVE_DATA;
        endcase
    end

    always_ff @(posedge spi_if.sck or posedge spi_if.csb) begin
        if (spi_if.csb) begin
            ps_e <= RECEIVE_DATA;
            mem_nfft_counter_r <= 0;
            mem_data_counter_r <= 0;
            reg_response_counter_r <= 0;
            receive_data_counter_r <= 0;
        end else begin
            ps_e <= ns_e;
            mem_nfft_counter_r <= mem_nfft_counter_n;
            mem_data_counter_r <= mem_data_counter_n;
            reg_response_counter_r <= reg_response_counter_n;
            receive_data_counter_r <= receive_data_counter_n;
        end
    end

endmodule