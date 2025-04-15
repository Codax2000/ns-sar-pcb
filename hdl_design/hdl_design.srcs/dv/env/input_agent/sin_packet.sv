/**
class representing a sine wave, with amplitude, frequency, and phase.
Depends on N_fft from config to ensure that sampling is coherent
*/

`timescale 1ns / 1ns

class sin_packet extends uvm_sequency_item;

    `uvm_object_utils(sin_packet)
    
    int primes [] = '{97, 197}; // extend this list later
    rand int prime;
    int nfft;
    rand int amplitude_numerator;
    int amplitude_denominator = 97;
    real amplitude;
    real frequency;

    constraint amplitude_lte_1 { amplitude_numerator <= amplitude_denominator; }
    constraint index_is_valid { prime inside primes; }

    function new(string name = "sin_packet");
        super.new(name);
    endfunction

    function void post_randomize();
        amplitude = amplitude_numerator / amplitude_denominator;
        frequency = primes[prime_index] / nfft;  // equivalent to fin / fs
    endfunction

    function real get_amplitude(real phase);
        return amplitude * $cos(phase * 2 * 3.14159);  // phase in radians
    endfunction

endclass