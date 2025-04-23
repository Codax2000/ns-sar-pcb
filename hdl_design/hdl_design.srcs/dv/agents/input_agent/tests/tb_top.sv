module tb_top ();

    import uvm_pkg::*;

    if_input iut (); // interface under test

    initial begin
        uvm_config_db #(virtual if_input)::set(null, "uvm_test_top.agent.*", "vif", iut);
        run_test("base_test");
    end

    int fd;
    int i;
    initial begin
        fd = $fopen("output.csv", "w");
        $fwrite(fd, "test_index,vip,vin\n");
        for (i = 0; i < 512; i++) begin
            @(iut.vip);
            $fwrite(fd,"%u,%.4f%,.4f\n", i, iut.vip, iut.vin);
        end
        $fclose(fd);
    end

endmodule