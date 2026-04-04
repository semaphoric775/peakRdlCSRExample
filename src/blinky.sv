// Blinky module: toggles an LED based on CSR-configured period and enable
//
// The `scalar` register defines the half-period in clock cycles.
// When enable=1, the LED toggles every `scalar` clock cycles.
// When enable=0, the LED is driven low.

`default_nettype none

module blinky (
    input  wire        clk,
    input  wire        rst,
    input  wire        enable,       // from CSR LED*.enable
    input  wire [30:0] scalar,       // from CSR LED*.scalar (half-period in cycles)
    output logic       led
);

    logic [30:0] counter;

    always_ff @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            led     <= 1'b0;
        end else if (!enable) begin
            counter <= 32'd0;
            led     <= 1'b0;
        end else begin
            if (counter >= scalar - 1) begin
                counter <= 32'd0;
                led     <= ~led;
            end else begin
                counter <= counter + 1;
            end
        end
    end

endmodule

`default_nettype wire
