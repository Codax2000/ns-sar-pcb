`timescale 1ns / 1ps

import uvm_pkg::*;
`include "uvm_macros.svh"

class sin_packet extends uvm_sequence_item;
    
    int primes [$];

    int nfft;
    int osr;
    real fs;
    
    rand int prime_index;
         int prime;
    rand int amplitude_numerator;
         int amplitude_denominator;

    real amplitude;
    real frequency;

    constraint amplitude_lte_1 { 
        amplitude_numerator <  amplitude_denominator;
        amplitude_numerator > -amplitude_denominator;
    }

    constraint frequency_is_valid {
        prime_index < primes.size();
        prime_index >= 0;
    }

    `uvm_object_utils_begin(sin_packet)
        `uvm_field_int(nfft, UVM_ALL_ON)
        `uvm_field_int(osr, UVM_ALL_ON)
        `uvm_field_real(fs, UVM_ALL_ON)
        `uvm_field_int(prime, UVM_ALL_ON)
        `uvm_field_int(amplitude_numerator, UVM_ALL_ON)
        `uvm_field_int(amplitude_denominator, UVM_ALL_ON)
        `uvm_field_real(amplitude, UVM_ALL_ON)
        `uvm_field_real(frequency, UVM_ALL_ON)
        `uvm_field_queue_int(primes, UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "sin_packet");
        super.new(name);
        amplitude_denominator = 10000;
    endfunction
    
    function void set_nfft(int nfft);
        int nfft_adjusted;
        this.nfft = nfft;
        nfft_adjusted = (nfft >> (1 + $clog2(osr)));
        calc_primes(nfft_adjusted, primes);
    endfunction

    function void set_osr(int osr);
        this.osr = osr;
    endfunction

    function void set_fs(real fs);
        this.fs = fs;
    endfunction

    function void post_randomize();
        prime = primes[prime_index];
        amplitude = 1.0 * amplitude_numerator / amplitude_denominator;
        frequency = (fs * prime) / (osr * nfft);
    endfunction

    function automatic void calc_primes (int top_val, ref int primes [$]);
        bit i_is_prime;
        primes = {};

        primes.push_back(1);
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