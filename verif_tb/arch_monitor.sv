module arch_monitor();
logic retire;
logic[7:0] pc;
logic[7:0] oreg;
logic[7:0] areg;
logic[7:0] breg;




// collect internal register information
assign areg = testbench.u_dut.areg; 
assign breg = testbench.u_dut.breg;
assign oreg = testbench.u_dut.oreg;
assign pc = testbench.u_dut.pc;
assign retire = testbench.u_dut.retire;



endmodule
