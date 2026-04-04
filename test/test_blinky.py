"""CocoTB testbench for the blinky module.

Tests:
  1. LED stays low when enable=0
  2. LED toggles at the correct half-period set by scalar
  3. LED resets when enable is de-asserted mid-blink
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


async def reset(dut):
    dut.rst.value = 1
    dut.enable.value = 0
    dut.scalar.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_led_off_when_disabled(dut):
    """LED must remain low when enable=0."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    dut.scalar.value = 4
    dut.enable.value = 0
    await ClockCycles(dut.clk, 20)
    assert dut.led.value == 0, "LED should be off when enable=0"


@cocotb.test()
async def test_led_toggles_at_scalar(dut):
    """LED must toggle every `scalar` clock cycles when enabled."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    scalar = 8
    dut.scalar.value = scalar
    dut.enable.value = 1

    # Wait for the first rising edge of LED
    for _ in range(scalar * 4):
        await RisingEdge(dut.clk)
        if dut.led.value == 1:
            break
    assert dut.led.value == 1, "LED should have gone high"

    # Measure how long LED stays high (one half-period)
    cycles_high = 0
    while dut.led.value == 1:
        await RisingEdge(dut.clk)
        cycles_high += 1

    assert cycles_high == scalar, (
        f"LED half-period should be {scalar} cycles, got {cycles_high}"
    )


@cocotb.test()
async def test_led_resets_on_disable(dut):
    """LED must go low immediately when enable is de-asserted."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    dut.scalar.value = 10
    dut.enable.value = 1

    # Let it run for a few cycles
    await ClockCycles(dut.clk, 5)

    # Disable
    dut.enable.value = 0
    await ClockCycles(dut.clk, 2)
    assert dut.led.value == 0, "LED should go low after enable de-asserted"
