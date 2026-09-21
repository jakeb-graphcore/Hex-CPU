module testbench;
   parameter p_address_width = 8;
   parameter p_data_width    = 32;

   logic                       i_clk; //clock
   logic                       i_rst; //reset instruction

   // Program fetch
   logic [p_address_width-1:0] o_instr_addr;   // send instruction out (address bus)
   logic                       o_instr_rd_en;  // if the instruction is a read

   logic [p_data_width-1:0]    i_instr_rd_data; // incoming from address bus

   // Data interface
   logic [p_address_width-1:0] o_data_addr; // data memory address bus
   logic [p_data_width-1:0]    o_data_wr_data; // data memory data bus
   logic                       o_data_wr_en; //true on a write operation
   logic                       o_data_rd_en; //true on a read operation

   logic [p_data_width-1:0]    i_data_rd_data; // data incoming from data memory

cpu dut (
      .i_clk(i_clk), //clock
      .i_rst(i_rst), //reset instruction

      // Program fetch
      .o_instr_addr(o_instr_addr),   // send instruction out (address bus)
      .o_instr_rd_en(o_instr_rd_en),  // if the instruction is a read
      .i_instr_rd_data(i_instr_rd_data), // incoming from address bus

       // Data interface
      .o_data_addr(o_data_addr), // data memory address bus
      .o_data_wr_data(o_data_wr_data), // data memory data bus
      .o_data_wr_en(o_data_wr_en), //true on a write operation
      .o_data_rd_en(o_data_rd_en), //true on a read operation

      .i_data_rd_data(i_data_rd_data) // data incoming from data memory
);
logic rst;
always #1 i_clk =~ i_clk;



// simulated memory 
logic [7:0] data_memory [0:255]; //256 locations of 8 bit data
logic [7:0] instruction_memory [0:255]; //256 locations of 8 bit instructions
logic [7:0] final_instruction_address;
logic stop;

typedef enum logic [3:0] { LDAM=0, LDBM, STAM, LDAC, LDBC, LDAP, LDAI, LDBI, STAI, BR, BRZ, BRN, BRB, ADD, SUB, PFIX } instr_t;


function automatic logic [7:0] FORM_OPCODE_OPERAND (input instr_t opcode, input logic[3:0] operand);
   $display("opcode: %b", opcode);
   return {opcode, operand}; // concat operator 
endfunction

// very basic test to check its recieving instructions
// wait for signal from cpu and return an LDAC instruction

`define EXECUTE_INSTR(opcode, operand) \
   begin \
   repeat (1) @(posedge i_clk); \ 
   $display("Data being sent: %b", FORM_OPCODE_OPERAND(opcode, operand)); \
   i_instr_rd_data = FORM_OPCODE_OPERAND(opcode, operand); \
   repeat (1) @(posedge i_clk); \
   end


//handle memory write (could be a race condition with writing)
always@(posedge o_data_wr_en) begin
   data_memory[o_data_addr] <= o_data_wr_data;
   $display("Recieved write instruction. Address: %b, Data: %b", o_data_addr, o_data_wr_data);
end

//handle memory read
always@(posedge o_data_rd_en) begin
   i_data_rd_data <= data_memory[o_data_addr];
   $display("Recieved read instruciton. Address: %b", o_data_addr);
end

// handle instruction memory serve, effectively happens at the start of the clock cycle.
always@(o_instr_addr) begin
   if (stop) begin
      $finish;
   end
   i_instr_rd_data = instruction_memory[o_instr_addr];

   if (o_instr_addr >= final_instruction_address) begin
      stop = 1;
   end   
end

initial begin
   //Fill instruction memory 
   
   instruction_memory[0] = FORM_OPCODE_OPERAND(LDAC, 15);
   instruction_memory[1] = FORM_OPCODE_OPERAND(STAM, 1);
   final_instruction_address = 1;


   // Start the clock
   i_clk = 1;
   repeat (1) @(posedge i_clk);

   
   `EXECUTE_INSTR(LDAC, 15);
   `EXECUTE_INSTR(STAM, 1);
   `EXECUTE_INSTR(LDAC, 0);
   `EXECUTE_INSTR(LDAM, 1);
   `EXECUTE_INSTR(LDBC, 0);
   $finish;
end

final begin
   $dumpfile("dump.vcd");
   $dumpvars(0,testbench);
end

endmodule : testbench
