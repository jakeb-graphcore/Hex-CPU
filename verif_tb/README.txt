Before running any simulation, cd into this directory (verif_tb).
Run the testbench with the following command:
make DESIGN=my_cpu

Waves are output to `dump.vcd`.

The testbench assumes that accesses to the data memory happen in the rtl in the same order as the model.
If this is not true for your design, you may have to turn off the scoreboard and end of test checks for the data memory monitor.
To do this you need to change the configuration of the testbench.
To change the configuration of the testbench and testing, change the values in file tb_config.py.
For example, the number of tests run can be changed by editing `NUM_TESTS` in tb_config.py.

If you change the design file used for the cpu, you may have to clean your build by running:
./clean.sh

Seeds of tests used in the simulation are in sim_logs/seeds.log.

Coverage results can be found in sim_logs.
