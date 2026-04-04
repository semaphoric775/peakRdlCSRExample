# Tang Nano 9K (GW1NR-LV9QN88PC6/I5) implementation
# Toolchain: Yosys + nextpnr-himbaechel (Apicula) + gowin_pack + openFPGALoader

DEVICE = GW1NR-LV9QN88PC6/I5
BOARD  = tangnano9k
TOP    = top_tang9k

SRC_DIR = ../../src
SRC = \
	$(SRC_DIR)/blinky_csr_pkg.sv \
	$(SRC_DIR)/blinky_csr.sv \
	$(SRC_DIR)/blinky.sv \
	$(SRC_DIR)/spi2axi.sv \
	$(SRC_DIR)/top.sv \
	top_tang9k.sv

CST   = constraints/top.cst
BUILD = build

# ── Targets ──────────────────────────────────────────────────────────────────

.PHONY: all synth pnr pack prog flash clean

all: pack

synth: $(BUILD)/$(TOP).json
pnr:   $(BUILD)/$(TOP)_pnr.json
pack:  $(BUILD)/$(TOP).fs

# Synthesis
$(BUILD)/$(TOP).json: $(SRC) | $(BUILD)
	yosys -p "read_verilog -sv $^; synth_gowin -top $(TOP) -json $@" \
	      2>&1 | tee $(BUILD)/synth.log

# Place & route
$(BUILD)/$(TOP)_pnr.json: $(BUILD)/$(TOP).json $(CST) | $(BUILD)
	nextpnr-himbaechel \
	    --json  $< \
	    --write $@ \
	    --device $(DEVICE) \
	    --vopt cst=$(CST) \
	    --vopt family=GW1N-9C \
	    2>&1 | tee $(BUILD)/pnr.log

# Pack bitstream
$(BUILD)/$(TOP).fs: $(BUILD)/$(TOP)_pnr.json | $(BUILD)
	gowin_pack -d $(DEVICE) -o $@ $<

# Program to SRAM (lost on power cycle)
prog: $(BUILD)/$(TOP).fs
	openFPGALoader -b $(BOARD) $<

# Write to flash (survives power cycle)
flash: $(BUILD)/$(TOP).fs
	openFPGALoader -b $(BOARD) --write-flash $<

$(BUILD):
	mkdir -p $(BUILD)

clean:
	rm -rf $(BUILD)
