/**
Class: reg_env

Typed register environment containing a sequence item, predictor, and register block.
The goal is to avoid some of the boilerplate code in case of another UVM environment;
The thing is that EVERY SINGLE register environment needs this, so it's entirely reusable.
*/
class reg_env #(
    type SEQ_ITEM = uvm_sequence_item,
    type ADAPTER  = uvm_reg_adapter,
    type REG_BLOCK= uvm_reg_block
) extends uvm_env;

    function new (string name = "reg_env", uvm_component parent);
        super.new(name, parent);
    endfunction

    `uvm_component_param_utils(reg_env #(SEQ_ITEM, ADAPTER, REG_BLOCK))

    // Variable: ral
    // The typed register model for the specific device.
    REG_BLOCK ral;

    // Variable: adapter
    // The typed register adapter used by the register model and predictor.
    ADAPTER adapter;

    // Variable: predictor
    // The register predictor that converts bus transactions into
    // register predictions.
    uvm_reg_predictor #(SEQ_ITEM) predictor;

    // Function: build_phase
    // Constructs the adapter, register block, and the predictor. Also locks
    // the RAL and sets the auto predict to 0, since the RAL will be set via
    // subscriber instead of auto prediction.
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // set type override so volatile fields don't need updates
        uvm_reg_field::type_id::set_inst_override(
            adc_reg_field::get_type(), 
            "ral.*",
            this
        );

        adapter = ADAPTER::type_id::create("adapter");
        ral     = REG_BLOCK::type_id::create("ral_model");
        
        predictor = uvm_reg_predictor #(SEQ_ITEM)::type_id::create("predictor", this);

        ral.build();
        ral.lock_model();
        ral.reset();
        ral.default_map.set_auto_predict(0);
        
    endfunction

    // Function: connect_phase
    // Connects RAL and adapter to the predictor. Client env still has to connect
    // bus monitor to predictor.
    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        predictor.map = ral.default_map;
        predictor.adapter = adapter;
    endfunction

endclass