module testbench #(
      parameter p_address_width = 8
    , parameter p_data_width    = 8
) (
      input  logic                       i_clk
    , input  logic                       i_rst
    // Program fetch
    , output logic [p_address_width-1:0] o_instr_addr
    , output logic                       o_instr_rd_en
    , input  logic [p_data_width-1:0]    i_instr_rd_data
    // Data interface
    , output logic [p_address_width-1:0] o_data_addr
    , output logic [p_data_width-1:0]    o_data_wr_data
    , output logic                       o_data_wr_en
    , output logic                       o_data_rd_en
    , input  logic [p_data_width-1:0]    i_data_rd_data
);

cpu #(
      .p_address_width ( p_address_width )
    , .p_data_width    ( p_data_width    )
) u_dut (
      .i_clk           ( i_clk           )
    , .i_rst           ( i_rst           )
    // Program fetch
    , .o_instr_addr    ( o_instr_addr    )
    , .o_instr_rd_en   ( o_instr_rd_en   )
    , .i_instr_rd_data ( i_instr_rd_data )
    // Data interface
    , .o_data_addr     ( o_data_addr     )
    , .o_data_wr_data  ( o_data_wr_data  )
    , .o_data_wr_en    ( o_data_wr_en    )
    , .o_data_rd_en    ( o_data_rd_en    )
    , .i_data_rd_data  ( i_data_rd_data  )
);

arch_monitor u_arch_monitor();




initial begin
   $dumpfile("dump.vcd");
   $dumpvars(0,testbench);
end

endmodule : testbench
