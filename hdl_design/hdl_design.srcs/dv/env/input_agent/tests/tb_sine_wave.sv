module tb_sine_wave ();

    import uvm_pkg::*;
    import input_agent_pkg::*;

    if_input iut; // interface under test

    initial begin
        uvm_config_db #(virtual if_input)::set(null, "*", "if_input", iut);
        run_test("sine_wave_test");
    end

endmodule