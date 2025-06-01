class base_test extends uvm_test;

    // have to connect interfaces here too

    virtual task reset_phase;
        // run clock and reset through CLKGEN agent
        // wait for FSM to be reset to the correct ready state
    endtask

    virtual task configure_phase;
        // set registers using SPI
    endtask

endclass

class test_register_read_write extends base_test;

    // during run phase, write a random register

    // read it back

    // should match up with RAL model

endclass

class test_random_conversion extends base_test;

    // drive a bunch of random values onto the input and convert nfft
    // different values (nfft should be a random number written to the nfft
    // register at start of test)

endclass

class test_dwa extends base_test;

    // during build phase, override scoreboard to use a noise-based model instead
    // of a register-based one

    // write nfft to be a random power of 2
    // set DWA to be off
    // convert, compare SNDR/SFDR to ref model (should be close, within 1 dB)
    // turn DWA on
    // convert same signal again, compare SNDR/SFDR to ref model (should be 
    // within 1 dB also)

endclass