/**
Class: adc_reg_field

This is just like the normal uvm_reg_field, except this never needs to be updated
if it is volatile.
*/
class adc_reg_field extends uvm_reg_field;

    `uvm_object_utils(adc_reg_field)

    function new (string name = "adc_reg_field");
        super.new(name);
    endfunction

    virtual function bit needs_update();
        if (this.is_volatile())
            return 0;
        else
            return super.needs_update();
    endfunction

endclass