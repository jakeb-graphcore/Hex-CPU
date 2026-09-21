module arch_monitor();
logic retire;
logic[7:0] pc;
logic[7:0] oreg;
logic[7:0] areg;
logic[7:0] breg;
logic[3:0] instruction;
logic[3:0] read_from_data_mem_instruction;
logic i_clk;



// collect internal register information
assign areg = testbench.u_dut.areg; 
assign breg = testbench.u_dut.breg;
assign oreg = testbench.u_dut.oreg;
assign pc = testbench.u_dut.pc;
assign retire = testbench.u_dut.retire;

// additional information to collect, to help with coverage.
assign instruction = testbench.u_dut.instruction;
assign read_from_data_mem_instruction = testbench.u_dut.read_from_data_mem_instruction;
assign i_clk = testbench.u_dut.i_clk;

endmodule
