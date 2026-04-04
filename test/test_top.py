"""CocoTB testbench: verify SPI writes reach hardware registers (hwif_out).

Register map:
  0x00  LED1  bit[0]=enable, bits[31:1]=scalar (half-period, clk cycles)
  0x04  LED2  bit[0]=enable, bits[31:1]=scalar (half-period, clk cycles)

Strategy: drive SPI, check hwif_out internal aliases — no SPI readback needed.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer

LED1_ADDR = 0x00000000
LED2_ADDR = 0x00000004

CMD_WRITE       = 0x00
CMD_READ        = 0x01
SPI_FRAME_BYTES = 11
SPI_HALF_NS     = 100


def pack_led_reg(enable, scalar):
    """Pack enable (bit 0) and scalar (bits 31:1) into a 32-bit LED register value."""
    return ((scalar & 0x7FFFFFFF) << 1) | (enable & 0x1)


async def reset(dut):
    dut.rst_n.value = 0
    dut.spi_ss_n.value = 1
    dut.spi_sck.value  = 0
    dut.spi_mosi.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)


async def spi_transfer(dut, tx_bytes):
    assert len(tx_bytes) == SPI_FRAME_BYTES
    rx_bytes = []
    dut.spi_ss_n.value = 0
    await Timer(SPI_HALF_NS, unit="ns")
    for byte_val in tx_bytes:
        rx_byte = 0
        for bit_idx in range(7, -1, -1):
            dut.spi_mosi.value = (byte_val >> bit_idx) & 0x01
            await Timer(SPI_HALF_NS // 2, unit="ns")
            dut.spi_sck.value = 1
            await Timer(SPI_HALF_NS, unit="ns")
            rx_byte = (rx_byte << 1) | int(dut.spi_miso.value)
            dut.spi_sck.value = 0
            await Timer(SPI_HALF_NS // 2, unit="ns")
        rx_bytes.append(rx_byte)
    dut.spi_ss_n.value = 1
    await Timer(SPI_HALF_NS * 2, unit="ns")
    return rx_bytes


async def spi_write(dut, addr, data):
    tx = [
        CMD_WRITE,
        (addr >> 24) & 0xFF, (addr >> 16) & 0xFF,
        (addr >>  8) & 0xFF, (addr >>  0) & 0xFF,
        (data >> 24) & 0xFF, (data >> 16) & 0xFF,
        (data >>  8) & 0xFF, (data >>  0) & 0xFF,
        0x00, 0x00,
    ]
    cocotb.log.info(f'Requesting transfer with tx bytes {tx}')
    rx     = await spi_transfer(dut, tx)
    status = rx[10]
    return (status >> 2) & 1, status & 0x3   # timeout, bresp


async def spi_read(dut, addr):
    tx = [CMD_READ,
          (addr >> 24) & 0xFF, (addr >> 16) & 0xFF,
          (addr >>  8) & 0xFF, (addr >>  0) & 0xFF,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    rx     = await spi_transfer(dut, tx)
    rdata  = (rx[6] << 24) | (rx[7] << 16) | (rx[8] << 8) | rx[9]
    status = rx[10]
    return rdata, (status >> 2) & 1, status & 0x3


# ---------------------------------------------------------------------------

@cocotb.test()
async def test_led1_enable(dut):
    """SPI write LED1 enable=1, scalar=0; verify hwif_out reflects it."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    await ClockCycles(dut.clk, 400)

    async def watch_fsm():
        prev_bidx = -1
        prev_ss   = -1
        prev_sck  = -1
        count = 0
        for _ in range(20000):
            await RisingEdge(dut.clk)
            bidx    = int(dut.u_spi2axi.spi_rx_byte_idx.value)
            ss_sync = int(dut.u_spi2axi.spi_ss_n_sync.value)
            sck     = int(dut.u_spi2axi.spi_sck_sync.value)
            if bidx != prev_bidx or ss_sync != prev_ss or sck != prev_sck:
                cocotb.log.info(
                    f"@{cocotb.utils.get_sim_time('ns'):.0f}ns "
                    f"byte_idx={bidx} ss_n_sync={ss_sync} sck_sync={sck} "
                    f"bit_idx={int(dut.u_spi2axi.spi_rx_bit_idx.value)}")
                prev_bidx = bidx
                prev_ss   = ss_sync
                prev_sck  = sck
                count += 1
                if count > 30:
                    break

    mon = cocotb.start_soon(watch_fsm())
    timeout, bresp = await spi_write(dut, LED1_ADDR, pack_led_reg(enable=1, scalar=0))
    await ClockCycles(dut.clk, 4)
    mon.cancel()

    spi_addr  = int(dut.u_spi2axi.spi_rx_addr.value)
    spi_wdata = int(dut.u_spi2axi.spi_rx_wdata.value)
    wr_ack    = int(dut.u_blinky_csr.cpuif_wr_ack.value)
    cocotb.log.info(f"spi_rx_addr=0x{spi_addr:08x} spi_rx_wdata=0x{spi_wdata:08x} wr_ack={wr_ack}")
    cocotb.log.info(f"timeout={timeout} bresp={bresp} "
                    f"hwif_out_LED1_enable={int(dut.hwif_out_LED1_enable_value.value)}")

    assert timeout == 0, f"SPI write timed out"
    assert bresp   == 0, f"SPI write BRESP={bresp}"
    assert int(dut.hwif_out_LED1_enable_value.value) == 1, \
        f"LED1.enable should be 1, got {int(dut.hwif_out_LED1_enable_value.value)}"


@cocotb.test()
async def test_led1_scalar(dut):
    """SPI write LED1 scalar=8; verify hwif_out reflects it."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    scalar = 8
    timeout, bresp = await spi_write(dut, LED1_ADDR, pack_led_reg(enable=0, scalar=scalar))
    await ClockCycles(dut.clk, 4)

    cocotb.log.info(f"timeout={timeout} bresp={bresp} "
                    f"hwif_out_LED1_scalar=0x{int(dut.hwif_out_LED1_scalar_value.value):08x}")

    assert timeout == 0, f"SPI write timed out"
    assert bresp   == 0, f"SPI write BRESP={bresp}"
    assert int(dut.hwif_out_LED1_scalar_value.value) == scalar, \
        f"LED1.scalar: expected {scalar}, got {int(dut.hwif_out_LED1_scalar_value.value)}"


@cocotb.test()
async def test_led2_enable_and_scalar(dut):
    """SPI write LED2 enable=1, scalar=16; verify hwif_out reflects it."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    scalar = 16
    timeout, bresp = await spi_write(dut, LED2_ADDR, pack_led_reg(enable=1, scalar=scalar))
    await ClockCycles(dut.clk, 4)

    cocotb.log.info(f"timeout={timeout} bresp={bresp} "
                    f"hwif_out_LED2_enable={int(dut.hwif_out_LED2_enable_value.value)} "
                    f"hwif_out_LED2_scalar=0x{int(dut.hwif_out_LED2_scalar_value.value):08x}")

    assert timeout == 0, f"SPI write timed out"
    assert bresp   == 0, f"SPI write BRESP={bresp}"
    assert int(dut.hwif_out_LED2_enable_value.value) == 1, \
        f"LED2.enable should be 1, got {int(dut.hwif_out_LED2_enable_value.value)}"
    assert int(dut.hwif_out_LED2_scalar_value.value) == scalar, \
        f"LED2.scalar: expected {scalar}, got {int(dut.hwif_out_LED2_scalar_value.value)}"


@cocotb.test()
async def test_led1_write_then_blink(dut):
    """Full path: SPI sets LED1 scalar+enable, LED1 toggles at correct rate."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    scalar = 8
    await spi_write(dut, LED1_ADDR, pack_led_reg(enable=1, scalar=scalar))
    await ClockCycles(dut.clk, 4)

    assert int(dut.hwif_out_LED1_enable_value.value) == 1
    assert int(dut.hwif_out_LED1_scalar_value.value) == scalar

    for _ in range(scalar * 6):
        await RisingEdge(dut.clk)
        if dut.led1.value == 1:
            break
    assert dut.led1.value == 1, "LED1 never went high"

    cycles_high = 0
    while dut.led1.value == 1:
        await RisingEdge(dut.clk)
        cycles_high += 1
    assert cycles_high == scalar, f"LED1 half-period: expected {scalar}, got {cycles_high}"


@cocotb.test()
async def test_led2_independent(dut):
    """LED2 blinks independently at a different rate from LED1."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    scalar1 = 8
    scalar2 = 16
    await spi_write(dut, LED1_ADDR, pack_led_reg(enable=1, scalar=scalar1))
    await spi_write(dut, LED2_ADDR, pack_led_reg(enable=1, scalar=scalar2))
    await ClockCycles(dut.clk, 4)

    assert int(dut.hwif_out_LED1_scalar_value.value) == scalar1
    assert int(dut.hwif_out_LED2_scalar_value.value) == scalar2

    # Wait for LED2 to go high
    for _ in range(scalar2 * 6):
        await RisingEdge(dut.clk)
        if dut.led2.value == 1:
            break
    assert dut.led2.value == 1, "LED2 never went high"

    cycles_high = 0
    while dut.led2.value == 1:
        await RisingEdge(dut.clk)
        cycles_high += 1
    assert cycles_high == scalar2, f"LED2 half-period: expected {scalar2}, got {cycles_high}"
