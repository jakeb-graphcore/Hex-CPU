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
    o_data_addr <= address;\
    o_data_wr_data <= data;\
    o_data_wr_en <= 1;\
    end 


`define SETUP_READ_TO_DATA_MEMORY(address, instr) \
    begin\
    o_data_addr <= address;\
    read_from_data_mem_instruction <= instr;\
    o_data_rd_en <= 1;\
    end

logic [p_address_width-1:0] pc; // program counter
logic [p_address_width-1:0]    oreg        = '0; //full operand register
logic [op_width-1:0] instruction = '0; // instruction code
logic [p_address_width-1:0]    areg        = '0; // left side operand
logic [p_address_width-1:0]    breg        = '0; // right side operand
logic retire = '0; // retire signal needed in spec apparently

typedef enum logic[3:0] {SEND_INSTRUCTION=0, WAIT_FOR_INSTRUCTION, DECODE, EXECUTE, WAIT_FOR_MEMORY, CAPTURE_MEMORY, RETIRE, KILL} exec_state;
exec_state state;

initial begin
    pc = '0;
    retire <= '0;
    o_instr_addr <= '0;
    o_instr_rd_en <= '0;
    o_data_addr <= '0;
    o_data_wr_data <= '0;
    o_data_wr_en <= '0;
    o_data_rd_en <= '0;
    state <= SEND_INSTRUCTION;
    // $monitor("oreg=%d, breg=%d, areg=%d, pc=%d", oreg, breg, areg, pc);
end


always_ff @(posedge i_clk) begin
  if(i_rst) begin
      pc = '0;
      retire <= '0;
      o_instr_addr <= '0;
      o_instr_rd_en <= '0;
      o_data_addr <= '0;
      o_data_wr_data <= '0;
      o_data_wr_en <= '0;
      o_data_rd_en <= '0;

      oreg <= 0;
      areg <= 0;
      breg <= 0;
      instruction <= 0;
      
      state <= SEND_INSTRUCTION;
      
      // the following is probably not needed, but helps making tests reentrant
      instruction <= LDAM;
      read_from_data_mem_instruction <= LDAM;
      
  end else begin

    o_instr_rd_en <= 0;
    o_data_wr_en <= 0;
    o_data_rd_en <= 0;
    retire <= 0;

    o_instr_addr <= 0;
    o_data_wr_data <= 0;
    o_data_addr <= 0;
  

  case (state)
    SEND_INSTRUCTION: begin
        o_instr_rd_en <= 1;
        o_instr_addr <= pc;
        state <= WAIT_FOR_INSTRUCTION;
    end

    // causes an implicit wait.
    WAIT_FOR_INSTRUCTION: begin 
        state <= DECODE;      
    end

    // need a seperate decode step to ensure test suite can read oreg's value
    DECODE: begin
        instruction = ((i_instr_rd_data >> op_width) & 15);
        oreg[3:0] <= i_instr_rd_data[3:0];
        state <= EXECUTE;
    end
    
    EXECUTE: begin
        case (instruction)

            LDAM: begin
                `SETUP_READ_TO_DATA_MEMORY(oreg, LDAM);
                state <= WAIT_FOR_MEMORY;
            end

            LDBM: begin
                `SETUP_READ_TO_DATA_MEMORY(oreg, LDBM);
                state <= WAIT_FOR_MEMORY;
            end

            LDAC: begin
                areg <= oreg;
                state <= RETIRE;
                pc <= pc + 1;
            end

            LDBC: begin
                breg <= oreg;
                pc <= pc + 1;
                state <= RETIRE;
            end

            LDAP: begin
                areg <= pc + oreg + 1;
                pc <= pc + 1;
                state <= RETIRE; 
            end

            STAM: begin
                `WRITE_TO_DATA_MEMORY(oreg, areg);
                pc <= pc + 1;
                state <= RETIRE;
            end

            STAI: begin
                `WRITE_TO_DATA_MEMORY(oreg + breg, areg);
                pc <= pc + 1;
                state <= RETIRE;
            end

            SUB: begin
                areg <= areg - breg;
                pc <= pc + 1;
                state <= RETIRE;
            end

            ADD: begin
                areg <= areg + breg;
                pc <= pc + 1;
                state <= RETIRE;
            end

            BR: begin
                if (oreg == 254) begin
                    pc <= pc - 1;// so it plays well with cotocb testing
                    state <= KILL;
                end else begin
                    pc <= pc + oreg + 1;
                    state <= RETIRE;
                end
            end
            
            BRZ: begin
                if(areg == 0) begin
                    pc <= pc + oreg + 1;
                end else begin 
                    pc <= pc + 1;
                end
                state <= RETIRE;
            end

            BRN: begin
                if(areg > 127) begin
                    pc <= pc + oreg + 1;
                end else begin
                    pc <= pc + 1;
                end
                state <= RETIRE;
            end

            BRB: begin
                pc <= breg;
                state <= RETIRE;
            end

            PFIX: begin
                oreg <= oreg << 4;
                pc <= pc + 1;
                state <= RETIRE;
            end

            LDAI: begin
                `SETUP_READ_TO_DATA_MEMORY(areg + oreg, LDAI);
                state <= WAIT_FOR_MEMORY;
            end

            LDBI: begin
                `SETUP_READ_TO_DATA_MEMORY(breg + oreg, LDBI);
                state <= WAIT_FOR_MEMORY;
            end

            default: begin
            end
        endcase

    
    end

    // implicit wait for memory
    WAIT_FOR_MEMORY: begin  
        state <= CAPTURE_MEMORY;
    end

    CAPTURE_MEMORY: begin
        case(read_from_data_mem_instruction)
            LDAM: begin
                areg  <= i_data_rd_data;
            end
            LDBM: begin
                breg <= i_data_rd_data;
            end
            LDAI: begin 
                areg <= i_data_rd_data;
            end
            LDBI: begin
                breg <= i_data_rd_data;
            end 
        endcase
        pc <= pc + 1;
        state <= RETIRE;
    end

    // resest flags
    RETIRE: begin
        if (instruction != PFIX) begin
            oreg <= 0;
        end
        retire <= 1;
        state <= SEND_INSTRUCTION;
    end

    // kill the cpu (shutdown cpu without calling finish)
    KILL: begin
        oreg <= 0;
        state <= KILL;
        retire <= 1;
    end
  endcase

  end
end


endmodule : cpu
