# CocoTB Makefile for blinky testbench

TOPLEVEL_LANG = verilog
SIM           = verilator

VERILOG_SOURCES = $(shell pwd)/../src/blinky.sv

TOPLEVEL = blinky
MODULE   = test_blinky

include $(shell cocotb-config --makefiles)/Makefile.sim

# Full SPI integration test (top-level: SPI -> AXI4-Lite -> CSR -> Blinky)
SRC := $(abspath ../src)
.PHONY: sim_top
sim_top:
	$(MAKE) \
	  SIM=verilator \
	  TOPLEVEL_LANG=verilog \
	  TOPLEVEL=top \
	  MODULE=test_top \
	  EXTRA_ARGS="--timing --assert --unroll-count 256 -Wno-MULTIDRIVEN -Wno-WIDTHCONCAT -Wno-SELRANGE -Wno-WIDTHTRUNC -Wno-IMPLICITSTATIC -Wno-WIDTHEXPAND --trace --trace-fst --trace-structs" \
	  WAVES=1 \
	  VERILOG_SOURCES="$(SRC)/blinky_csr_pkg.sv $(SRC)/blinky_csr.sv $(SRC)/blinky.sv $(SRC)/spi2axi.sv $(SRC)/top.sv" \
	  SIM_BUILD=sim_build_top \
	  sim
