`timescale 1ns / 1ns

import uvm_pkg::*;
`include "uvm_macros.svh"

class sin_packet extends uvm_sequence_item;

    `uvm_object_utils(sin_packet)
    
    int primes [];
    rand int prime;
    int nfft;
    rand int amplitude_numerator;
    int amplitude_denominator;
    real amplitude;
    real frequency;
    int driver_delay_ns;

    constraint amplitude_lte_1 { amplitude_numerator < amplitude_denominator; }
    constraint index_is_valid { prime inside {primes} ; }

    function new(string name = "sin_packet");
        super.new(name);
        gen_prime_numbers_under(nfft);
        amplitude_denominator = primes[primes.size() - 1];
    endfunction
    
    function set_nfft(int n_fft);
        nfft = n_fft;
    endfunction

    function void post_randomize();
        amplitude = amplitude_numerator / amplitude_denominator;
        frequency = prime / nfft;  // equivalent to fin / fs
        driver_delay_ns = int'(2 * $rtoi(1 / frequency));
    endfunction

    function int prime_numbers_under(int top_val);
        int i;
        
        if (top_val > 1) begin

            for (i = 2; i < top_val; i++) begin
                bit is_prime = 1;
    
                for (int j = 2; j * j <= i; j++) begin
                    if (i % j == 0) begin
                        is_prime = 0;
                        j = i; // Not prime, kill the loop
                    end
                end
    
                if (is_prime) begin
                    primes = new [primes.size() + 1] (primes);
                end
            end
        end
    endfunction

endclass