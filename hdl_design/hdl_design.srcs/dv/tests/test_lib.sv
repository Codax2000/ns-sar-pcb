class base_test extends uvm_test;

endclass

class test_register_read_write;

    // during run phase, write a random register

    // read it back

    // should see the same value if the register is writeable,
    // ref model should pull from toplevel config object

endclass

class test_random_conversion;

    // drive a bunch of random values onto the input and convert nfft
    // different values (nfft should be a random number written to the nfft
    // register at start of test)

endclass

class test_dwa;

    // during build phase, override scoreboard to use a noise-based model instead
    // of a register-based one

    // write nfft to be a random power of 2
    // set DWA to be off
    // convert, compare SNDR/SFDR to ref model (should be close, within 1 dB)
    // turn DWA on
    // convert same signal again, compare SNDR/SFDR to ref model (should be 
    // within 1 dB also)

endclass