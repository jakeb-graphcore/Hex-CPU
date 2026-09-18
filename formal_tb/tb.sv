module tb(input logic clk, input logic rst);
  parameter WIDTH = 32;
  parameter DEPTH_LEN = 4;

  reg i_clk, i_rst_n;
  reg [WIDTH-1:0] i_data;
  reg wr_en, rd_en;
  wire [WIDTH-1:0] o_data;
  wire o_full;
  wire o_empty;

  fifo #( .WIDTH(4), .DEPTH_LEN(4)) u_fifo (
                    .i_clk(clk), .i_rst_n(!rst), .i_data(i_data), .wr_en(wr_en),
                    .rd_en(rd_en), .o_data(o_data), .o_full(o_full), .o_empty(o_empty)
                     );


    p1: assert property (@(posedge clk)  wr_en |-> !o_empty); // This should fail
    p2: cover property (@(posedge clk)  !o_empty); // This should pass
    // Write your assertions here.
endmodule
