module posedge_detector # (
    parameter N_CYCLES = 2
) (
    input  logic clk,
    input  logic rst,
    input  logic in,
    output logic posedge_detected
);

    enum logic [1:0] {READY, COUNT, DONE} state, next_state;

    logic [$clog2(N_CYCLES)-1:0] count;

    always_comb begin
        case (state)
            READY: next_state = in ? COUNT : READY;
            COUNT: begin
                if (!in) begin
                    next_state = READY;
                end
                else if ((count == N_CYCLES - 1) && in) begin
                    next_state = DONE;
                end
                else
                    next_state = COUNT;
            end
            DONE: next_state = in ? DONE : READY;
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            count <= 0;
            state <= READY;
        end
        else begin
            state <= next_state;
            if (state == COUNT && next_state == COUNT)
                count <= count + 1;
            else
                count <= 0;
        end
    end

    assign posedge_detected = (state == COUNT) && (next_state == DONE);

endmodule