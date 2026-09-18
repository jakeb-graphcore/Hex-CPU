# Verif Sandbox

This repository contains a verif testbench for the hex cpu design.
See verif_tb/README.txt and verif_tb/TASKS.txt for more information.

# Formal Verif Sandbox

See formal_tb/README.txt and formal_tb/TASKS.txt for a formal verification task.
This involves formally verifying a FIFO.

## Getting Started

Before you can run a simulation, you must install Python along with the relevant cocotb packages (See https://www.cocotb.org/)
and icarus verilog (https://steveicarus.github.io/iverilog/).
If you are on Mac:
Go to homebrew webpage and follow installation there 
On the terminal run :
- brew install python@3.12
- git clone {link given for cloning repository with HTTPS}

cd into the verif_sandbox directory 

- python -m venv venv
- source venv/bin/activate
- python -m pip install -r requirements.txt
- brew install icarus-verilog

To view waveforms (stored in vcd files), you need GTKWave installed (see https://gtkwave.sourceforge.net/) or use the Surfer
waveform viewer from their website (see https://surfer-project.org/).

If this doesn't work try running : brew install yanjiew1/gtkwave/gtkwave

## Running a Simulation

First make sure you have sourced the python environment:


With a design in file designs/my_cpu.sv, you can run commands:
cd verif_tb
make DESIGN=my_cpu

See verif_tb/README.txt for more details.
