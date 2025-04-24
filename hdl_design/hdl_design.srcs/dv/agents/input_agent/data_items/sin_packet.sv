`timescale 1ns / 1ns

import uvm_pkg::*;
`include "uvm_macros.svh"

class sin_packet extends uvm_sequence_item;
    
    int primes [$];
    rand int prime;
    int nfft;
    rand int amplitude_numerator;
    int amplitude_denominator;
    real amplitude;
    real frequency;
    int driver_delay_ns;
    real fs;

    constraint amplitude_lte_1 { 
        amplitude_numerator <= amplitude_denominator; 
        amplitude_numerator > 0;
    }
    constraint index_is_valid {
        prime inside {primes} ; 
        prime < (nfft / 2);
    }

    `uvm_object_utils_begin(sin_packet)
        `uvm_field_int(prime, UVM_DEFAULT)
        `uvm_field_int(nfft, UVM_DEFAULT)
        `uvm_field_int(amplitude_numerator, UVM_DEFAULT)
        `uvm_field_int(amplitude_denominator, UVM_DEFAULT)
        `uvm_field_real(amplitude, UVM_DEFAULT)
        `uvm_field_real(frequency, UVM_DEFAULT)
        `uvm_field_int(driver_delay_ns, UVM_DEFAULT)
    `uvm_object_utils_end

    function new(string name = "sin_packet");
        super.new(name);
        set_nfft(32);
        set_fs(100e6);
        `uvm_info("PKT", "Packet creation successful", UVM_LOW)
    endfunction
    
    function void set_nfft(int n_fft);
        nfft = n_fft;
        calc_primes(nfft, primes);
        `uvm_info("PKT", $sformatf("NFFT Changed to %d", nfft), UVM_LOW)
        amplitude_denominator = primes[primes.size() - 1];
        `uvm_info("PKT", $sformatf("Primes: %p", primes), UVM_LOW)
    endfunction

    function void set_fs(real sampling_freq);
        fs = sampling_freq;
    endfunction

    function void post_randomize();
        amplitude = real'(amplitude_numerator) / real'(amplitude_denominator);
        frequency = fs * real'(prime) / real'(nfft);
        driver_delay_ns = int'($rtoi(1e9 / fs));
    endfunction

    function automatic void calc_primes (int top_val, ref int primes [$]);
        bit i_is_prime;
        primes = {};

        for (int i = 2; i <= top_val; i++) begin
            i_is_prime = 1'b1;
            for (int j = 0; (j < primes.size()) && i_is_prime; j++) begin
                if (i % primes[j] == 0) begin
                    i_is_prime = 1'b0;
                end
            end
            if (i_is_prime)
                primes.push_back(i);
        end
    endfunction

endclass