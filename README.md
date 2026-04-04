# csrExample

A minimal FPGA design demonstrating a software-accessible CSR (Control/Status Register) block driving two independent LED blinky controllers.

## Architecture

```
SPI master
    │
    ▼
spi2axi          (SPI → AXI4-Lite bridge, CPOL=0 CPHA=0)
    │  AXI4-Lite
    ▼
blinky_csr       (PeakRDL-generated register block)
    │  hwif_out
    ├──▶ blinky1 ──▶ led1
    └──▶ blinky2 ──▶ led2
```

Software writes register values over SPI. The CSR block exposes them to the blinky modules via a typed `hwif_out` struct. The `hwif_in` struct is tied to zero (no hardware writes in this design).

## Register Map

| Address | Register | Bits   | Field  | Description                          |
|---------|----------|--------|--------|--------------------------------------|
| `0x00`  | LED1     | `[0]`  | enable | 1 = blink, 0 = LED off               |
| `0x00`  | LED1     | `[31:1]`| scalar | Half-period in clock cycles          |
| `0x04`  | LED2     | `[0]`  | enable | 1 = blink, 0 = LED off               |
| `0x04`  | LED2     | `[31:1]`| scalar | Half-period in clock cycles          |

Default scalar value: `25_000_000` (0.5 s half-period at 50 MHz).

## SPI Frame Format

Each transaction is 11 bytes, MSB first, CPOL=0 CPHA=0:

**Write:**
```
[CMD=0x00] [ADDR 31:24] [ADDR 23:16] [ADDR 15:8] [ADDR 7:0]
[DATA 31:24] [DATA 23:16] [DATA 15:8] [DATA 7:0] [0x00] [0x00]
```

**Read:**
```
[CMD=0x01] [ADDR 31:24] [ADDR 23:16] [ADDR 15:8] [ADDR 7:0]
[0x00] [0x00] [0x00] [0x00] [0x00] [0x00]
```
Response bytes 6–9 carry the read data; byte 10 is the status byte (`bit[2]`=timeout, `bits[1:0]`=BRESP).

## Source Files

```
csr/
  blinky.rdl          Register description (PeakRDL source)

src/
  blinky_csr_pkg.sv   Generated package — hwif struct typedefs
  blinky_csr.sv       Generated CSR block (AXI4-Lite slave)
  spi2axi.sv          SPI-to-AXI4-Lite bridge (© Guy Eschemann, Apache-2.0)
  blinky.sv           LED blinky controller
  top.sv              Top-level integration

test/
  test_blinky.py      CocoTB unit tests for the blinky module
  test_top.py         CocoTB integration tests (SPI → CSR → LED)
  Makefile            Simulation targets
```

## Dependencies

| Tool | Purpose |
|------|---------|
| [Verilator](https://verilator.org) ≥ 5.0 | RTL simulation |
| [CocoTB](https://cocotb.org) ≥ 2.0 | Python testbench framework |
| [PeakRDL](https://github.com/SystemRDL/PeakRDL) | CSR regeneration from RDL |

Install Python dependencies:
```bash
pip install cocotb peakrdl-regblock
```

## Running Simulations

All commands run from the `test/` directory.

**Blinky unit tests** (standalone blinky module):
```bash
cd test
make
```

**Full integration tests** (SPI → AXI4-Lite → CSR → LED):
```bash
cd test
make sim_top
```

**Clean all simulation outputs:**
```bash
cd test
make clean
```

Results are written to `test/results.xml`. Waveforms are captured to `test/dump.fst` (open with GTKWave).

## Regenerating the CSR Block

After editing `csr/blinky.rdl`:
```bash
peakrdl regblock csr/blinky.rdl -o src/ --cpuif axi4-lite-flat
```

> **Note:** The generated `blinky_csr.sv` requires one manual fix for Verilator compatibility — replace the PeakRDL struct-array response buffer with the flat single-slot version already present in the file. See the comment block in `src/blinky_csr.sv` for details.
