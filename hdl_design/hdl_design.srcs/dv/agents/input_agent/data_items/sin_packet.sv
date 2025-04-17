`timescale 1ns / 1ns

import uvm_pkg::*;

class sin_packet extends uvm_sequence_item;

    `uvm_object_utils(sin_packet)
    
    int primes [];
    rand int prime;
    int nfft;
    rand int amplitude_numerator;
    int amplitude_denominator;
    real amplitude;
    real frequency;

    constraint amplitude_lte_1 { amplitude_numerator <= amplitude_denominator; }
    constraint index_is_valid { prime inside primes; }

    function new(string name = "sin_packet");
        super.new(name);
        if (!uvm_config_db #(int)::get(this, "", "nfft", nfft))
            `uvm_fatal("CONFIG", "NFFT not found", UVM_LOW)
        primes = prime_numbers_under(nfft);
        amplitude_denominator = primes[$];
    endfunction

    function void post_randomize();
        amplitude = amplitude_numerator / amplitude_denominator;
        frequency = prime / nfft;  // equivalent to fin / fs
        int driver_delay_ns = 2 * $rtoi(1 / frequency);
        if (!uvm_config_db #(int)::set(this, "", "driver_delay_ns", nfft))
            `uvm_warning("SIN_PKT", "Drive delay not updated", UVM_LOW)
    endfunction

    function int prime_numbers_under(int top_val);
        int primes[];

        if (top_val <= 1) begin
            return primes;
        end

        foreach (int i in [2:top_val-1]) begin
            bit is_prime = 1;

            for (int j = 2; j * j <= i; j++) begin
                if (i % j == 0) begin
                    is_prime = 0;
                    j = i; // Not prime, kill the loop
                end
            end

            if (is_prime) begin
                primes.push_back(i);
            end
        end
        return primes;
    endfunction

endclass