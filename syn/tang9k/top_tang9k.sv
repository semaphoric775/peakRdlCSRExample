// Tang Nano 9K synthesis wrapper for top.sv
//
// Board specifics handled here so top.sv stays simulation-clean:
//   - 27 MHz oscillator (pin 52)
//   - 6 active-low LEDs (pins 10,11,13,14,15,16) → led[5:0]
//   - Button S1 active-low reset (pin 3)
//   - SPI on GPIO expansion header
//
// NOTE: Default scalar of 25,000,000 was sized for 50 MHz (0.5 s half-period).
//       At 27 MHz, 0.5 s ≈ 13,500,000 cycles. Write the desired value over SPI
//       after boot or update the RDL default for this target.

`default_nettype none

module top_tang9k (
    input  wire       clk,       // 27 MHz oscillator, pin 52

    input  wire       rst_n,     // Button S1, active low, pin 3

    // SPI interface — GPIO expansion header
    input  wire       spi_sck,   // pin 25
    input  wire       spi_ss_n,  // pin 26
    input  wire       spi_mosi,  // pin 27
    output wire       spi_miso,  // pin 28

    // 6 active-low LEDs
    output wire [5:0] led        // pins 10,11,13,14,15,16
);

    wire led1_active, led2_active;

    top u_top (
        .clk      (clk),
        .rst_n    (rst_n),
        .spi_sck  (spi_sck),
        .spi_ss_n (spi_ss_n),
        .spi_mosi (spi_mosi),
        .spi_miso (spi_miso),
        .led1     (led1_active),
        .led2     (led2_active)
    );

    // Invert for active-low hardware; unused LEDs held off (high)
    assign led = {4'b1111, ~led2_active, ~led1_active};

endmodule

`default_nettype wire
