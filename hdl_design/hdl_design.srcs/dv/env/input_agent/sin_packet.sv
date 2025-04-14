/**
class representing a sine wave, with amplitude, frequency, and phase.
Depends on N_fft from config to ensure that sampling is coherent
*/

class sin_packet extends uvm_object;
    
    int primes [97, 197]; // extend this list later
    rand int prime_index;
    rand int phase_numerator
    int phase_denominator;
    int nfft;
    real PI = 3.14159;
endclass