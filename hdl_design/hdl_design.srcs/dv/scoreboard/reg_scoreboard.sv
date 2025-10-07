class reg_scoreboard extends uvm_scoreboard;
    // TODO: gather coverage information

    // TODO: throw error every time a SUBSEQUENT read does not match the mirrored value
    //       this is because primary reads should match mirrored vlaues
    //       Also : this should pay attention and make sure it compares before RAL is updated
endclass