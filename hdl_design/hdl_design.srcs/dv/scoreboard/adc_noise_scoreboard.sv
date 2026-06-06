`uvm_analysis_imp_decl(_spi)
`uvm_analysis_imp_decl(_osc)

class adc_noise_scoreboard extends uvm_scoreboard;

    `uvm_object_utils(adc_noise_scoreboard)

    // 2. Define the analysis imports using the declared suffixes
    uvm_analysis_imp_spi #(spi_packet, multi_input_scoreboard) spi_export;
    uvm_analysis_imp_osc #(sine_packet, multi_input_scoreboard) osc_export;

    // Internal data structures for checking
    spi_transaction spi_queue[$];

    bit  enable;
    bit  disabled_state;
    real frequency;
    real amplitude;

    function new(string name = "multi_input_scoreboard", uvm_component parent = null);
        super.new(name, parent);
        spi_export = new("spi_export", this);
        osc_export = new("osc_export", this);
    endfunction

    virtual function void write_spi(spi_transaction tr);
        // if NFFT == 1 and in incremental mode, and the oscillator input is DC
        // (not enabled), and the conversion was started and is done, check 
        // single values against Python model


        // otherwise, if oscillator is enabled, wait for the entire memory
        // (0 - NFFT value) to be read back. Once read back, calculate SNDR and
        // THD and such.


    endfunction
    
    virtual function void write_osc(sine_packet tr);
        this.enable = tr.enabled;
        this.disabled_state = tr.disabled_state;
        this.frequency = tr.frequency;
        this.amplitude = tr.amplitude;
    endfunction


endclass