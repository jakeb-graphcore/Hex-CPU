/*
all instructions are 8 bit
Instructions are split into 4 bit representing an operation and 4 bits of data
OPR a special instruction causing operand to be interpreter as a inter-register operation
Harvard archetecture
*/

module cpu #(
      parameter p_address_width = 8
    , parameter p_data_width    = 32
    , parameter op_width = 4 // each instruction is 4 bits long
) (
      input  logic                       i_clk //clock
    , input  logic                       i_rst //reset instruction

    // Program fetch
    , output logic [p_address_width-1:0] o_instr_addr   // send instruction out (address bus)
    , output logic                       o_instr_rd_en  // if the instruction is a read

    , input  logic [p_data_width-1:0]    i_instr_rd_data // incoming from address bus (changed to p_address_width)

    // Data interface
    , output logic [p_address_width-1:0] o_data_addr // data memory address bus
    , output logic [p_data_width-1:0]    o_data_wr_data // data memory data bus
    , output logic                       o_data_wr_en //true on a write operation
    , output logic                       o_data_rd_en //true on a read operation

    , input  logic [p_data_width-1:0]    i_data_rd_data // data incoming from data memory
);

//enum to hopefully make case statement clearer.
typedef enum logic [3:0] { LDAM=0, LDBM, STAM, LDAC, LDBC, LDAP, LDAI, LDBI, STAI, BR, BRZ, BRN, BRB, ADD, SUB, PFIX } instr_t;
instr_t read_from_data_mem_instruction;

`define WRITE_TO_DATA_MEMORY(address, data) \
    begin \
    o_data_addr = address;\
    o_data_wr_data = data;\
    o_data_wr_en = 1;\
    end 


`define SETUP_READ_TO_DATA_MEMORY(address, instr) \
    begin\
    o_data_addr = address;\
    read_from_data_mem_instruction = instr;\
    o_data_rd_en = 1;\
    end


logic [p_address_width-1:0] pc; // program counter
logic [p_address_width-1:0]    oreg        = '0; //full operand register
logic [op_width-1:0] instruction = '0; // instruction code
logic [p_address_width-1:0]    areg        = '0; // left side operand
logic [p_address_width-1:0]    breg        = '0; // right side operand
logic retire = '0; // retire signal needed in spec apparently
logic [p_data_width-1:0] bus_instr_memory;



//reset logic
always_ff @(posedge i_clk) begin

  if(i_rst) begin
      pc = '0;
      retire <= '0;
      o_instr_addr = '0;
      o_instr_rd_en = '0;
      o_data_addr = '0;
      o_data_wr_data = '0;
      o_data_wr_en = '0;
      o_data_rd_en = '0;
  end else begin
    //start instruction
    o_instr_rd_en <= 1;
    o_instr_addr <= pc;
  end 
end

// reset flags on clock cycle down
always_ff@(negedge i_clk) begin
    o_instr_rd_en = '0;
    o_data_rd_en = '0;
    o_data_wr_en = '0;
    retire <= '0;
end

// may not need this?
initial begin
  pc = '0;
  o_instr_addr = '0;
  o_instr_rd_en = '0;
  o_data_addr = '0;
  o_data_wr_data = '0;
  o_data_wr_en = '0;
  o_data_rd_en = '0;
end


// Execute when data incoming?
always@(i_instr_rd_data) begin
  bus_instr_memory = i_instr_rd_data;
  pc = pc + 1; //increment the program counter -> may need to be done at a different time

  // DECODE
  instruction = ((i_instr_rd_data >> op_width) & 15);

  //fetch operand (hopefully), least significant 4 bits
  oreg[3:0] = bus_instr_memory[3:0];
  

  // EXECUTE
  unique case (instruction)
    LDAM: begin
        `SETUP_READ_TO_DATA_MEMORY(oreg, LDAM);
    end

    LDBM: begin
        `SETUP_READ_TO_DATA_MEMORY(oreg, LDBM);
    end

    LDAC: begin
        areg = oreg;
    end

    LDBC: begin
        breg = oreg;
    end

    LDAP: begin
        areg = pc + oreg;
    end

    STAM: begin
        `WRITE_TO_DATA_MEMORY(oreg, areg);
    end

    STAI: begin
        `WRITE_TO_DATA_MEMORY(oreg + breg, areg);
    end

    SUB: begin
        areg = areg - breg;
    end

    ADD: begin
        areg = areg + breg;
    end

    BR: begin
        if (oreg == 254) begin
            $display("\nareg = %d\n", areg);
            retire <= 1;
        end
        pc = pc + oreg;
    end
    
    BRZ: begin
        if(areg == 0) begin
            pc = pc + oreg;
        end
    end

    BRN: begin
        if(areg > 127) begin
            pc = pc + oreg;
        end
    end

    BRB: begin
        pc = breg;
    end

    PFIX: begin
        oreg = oreg << 4;
    end

    LDAI: begin
        `SETUP_READ_TO_DATA_MEMORY(areg + oreg, LDAI);
    end

    LDBI: begin
        `SETUP_READ_TO_DATA_MEMORY(breg + oreg, LDBI);
    end

    default: begin
        $display("Unrecognised instruction: %b", instruction);
    end
    endcase

    $display("Instruction: %b", instruction);
    $display("oreg: %b \n", oreg);

    $display("areg: %b", areg);
    $display("breg: %b", breg);
    
    if (instruction != PFIX) begin
        if (|oreg[p_address_width-1: 4]) begin
            $warning("PFIX overflow: oreg=%b", oreg);
        end 
        oreg <= 0;
    end

    //not explicit in the spec but test requires a retire flag to go up when instr completed.
    // Instruction yet to be completed for load until it comes back
    if (instruction != LDAM && instruction != LDBM && instruction != LDAI && instruction != LDBI) begin
        retire <= 1;
    end
end

// handle incoming data from memory
always@(i_data_rd_data) begin
    case(read_from_data_mem_instruction)
        LDAM: begin
            areg  = i_data_rd_data;
        end
        LDBM: begin
            breg = i_data_rd_data;
        end
        LDAI: begin 
            areg = i_data_rd_data;
        end
        LDBI: begin
            breg = i_data_rd_data;
        end 
    endcase
    retire <= 1;
end


endmodule : cpu
