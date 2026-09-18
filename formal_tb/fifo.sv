// Design taken from https://github.com/avashist003/FIFO_SystemVerilog_Assertion
module fifo
          #(parameter WIDTH = 4,
            parameter DEPTH_LEN = 4) // 2^4 depth
          (
          i_clk, i_rst_n, i_data, wr_en,
          rd_en, o_data, o_full, o_empty
          );

  input i_clk, i_rst_n;
  input [WIDTH-1:0] i_data;

  input wr_en, rd_en;

  output  reg[WIDTH-1:0] o_data;

  reg [WIDTH-1:0] mem [(1<<DEPTH_LEN)-1:0];

  output  o_full;
  output  o_empty;

  // points to the address to read/write to
  // notice extra bit
  reg [DEPTH_LEN: 0] rd_ptr, wr_ptr;

  wire rd_req, wr_req;

  assign rd_req = rd_en && !o_empty;
  assign wr_req = wr_en && !o_full;

  wire [DEPTH_LEN: 0] fill;

  assign fill = (wr_ptr - rd_ptr);
  assign o_empty = (fill==0);
  assign o_full = (fill == {1'b1, {DEPTH_LEN{1'b0}}});


  always@(posedge i_clk, negedge i_rst_n)
  begin
    if(!i_rst_n)
    begin
      wr_ptr <= 5'h00;
    end

    else
    begin
      if(wr_req)
      begin
        mem[wr_ptr[DEPTH_LEN-1: 0]] <= i_data;
        wr_ptr <= wr_ptr + 1'b1;
      end
    end
  end

  always@(posedge i_clk, negedge i_rst_n)
  begin
    if(!i_rst_n)
    begin
      rd_ptr <= 5'h00;
    end
    else
    begin
      if (rd_req)
      begin
        rd_ptr <= rd_ptr + 1'b1;
      end
    end
  end

  // combinational read
  assign o_data = mem[rd_ptr[DEPTH_LEN-1: 0]];

endmodule
