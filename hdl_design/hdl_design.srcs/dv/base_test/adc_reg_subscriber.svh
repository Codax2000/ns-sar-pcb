class adc_reg_subscriber extends spi_reg_subscriber;

    `uvm_component_utils(adc_reg_subscriber)

    adc_regs regmodel;

    // Constructor
    function new(string name = "adc_reg_subscriber", uvm_component parent = null);
        super.new(name, parent);
    endfunction : new

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (! $cast(regmodel, m_ral))
            `uvm_fatal(get_full_name(), "Incorrect register model specified in uvm_config_db. adc_reg_subscriber requires adc_regs.");
    endfunction

    // Optional: Override write if ADC needs custom packet processing
    virtual function void write(spi_packet t);
        // Custom ADC logic can go here
        super.write(t); // Still passes it to the predictor port
    endfunction : write

endclass : adc_reg_subscriber