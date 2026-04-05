// Top-level design: SPI -> AXI4-Lite -> CSR -> Blinky x2
//
// Software interface: SPI master -> spi2axi -> AXI4-Lite -> blinky_csr
// Hardware interface: hwif_in / hwif_out are purely internal signals
//
// Register map:
//   0x00  LED1        [0]=enable  [31:1]=scalar (half-period, clk cycles)
//   0x04  LED2        [0]=enable  [31:1]=scalar (half-period, clk cycles)
//   0x08  MAX_PERIOD  [31:1]=max(LED1.scalar, LED2.scalar)  [RO]

`default_nettype none

module top (
    input  wire clk,
    input  wire rst_n,

    // SPI interface (software path)
    input  wire spi_sck,
    input  wire spi_ss_n,
    input  wire spi_mosi,
    output wire spi_miso,

    // LED outputs
    output wire led1,
    output wire led2
);

    //--------------------------------------------------------------------------
    // AXI4-Lite interconnect wires (spi2axi -> blinky_csr)
    //--------------------------------------------------------------------------
    localparam AXI_ADDR_WIDTH = 4;

    wire [AXI_ADDR_WIDTH-1:0] axil_awaddr;
    wire [2:0]                axil_awprot;
    wire                      axil_awvalid;
    wire                      axil_awready;

    wire [31:0]               axil_wdata;
    wire [3:0]                axil_wstrb;
    wire                      axil_wvalid;
    wire                      axil_wready;

    wire [1:0]                axil_bresp;
    wire                      axil_bvalid;
    wire                      axil_bready;

    wire [AXI_ADDR_WIDTH-1:0] axil_araddr;
    wire [2:0]                axil_arprot;
    wire                      axil_arvalid;
    wire                      axil_arready;

    wire [31:0]               axil_rdata;
    wire [1:0]                axil_rresp;
    wire                      axil_rvalid;
    wire                      axil_rready;

    //--------------------------------------------------------------------------
    // Hardware interface structs (internal)
    //--------------------------------------------------------------------------
    blinky_csr_pkg::blinky_csr__in_t  hwif_in;
    blinky_csr_pkg::blinky_csr__out_t hwif_out;

    // No external hardware writes to LED regs; tie all hwif_in fields to 0
    assign hwif_in.LED1.enable.next = 1'b0;
    assign hwif_in.LED1.enable.we   = 1'b0;
    assign hwif_in.LED1.scalar.next = 31'b0;
    assign hwif_in.LED1.scalar.we   = 1'b0;
    assign hwif_in.LED2.enable.next = 1'b0;
    assign hwif_in.LED2.enable.we   = 1'b0;
    assign hwif_in.LED2.scalar.next = 31'b0;
    assign hwif_in.LED2.scalar.we   = 1'b0;

    // MAX_PERIOD: combinatorially track the larger of the two LED scalars
    assign hwif_in.MAX_PERIOD.max_period.next =
        (hwif_out.LED1.scalar.value >= hwif_out.LED2.scalar.value)
            ? hwif_out.LED1.scalar.value
            : hwif_out.LED2.scalar.value;

    // Internal aliases for hierarchical probing in simulation
    wire        hwif_out_LED1_enable_value      = hwif_out.LED1.enable.value;
    wire [30:0] hwif_out_LED1_scalar_value      = hwif_out.LED1.scalar.value;
    wire        hwif_out_LED2_enable_value      = hwif_out.LED2.enable.value;
    wire [30:0] hwif_out_LED2_scalar_value      = hwif_out.LED2.scalar.value;
    wire [30:0] hwif_out_MAX_PERIOD_value       = hwif_out.MAX_PERIOD.max_period.value;

    //--------------------------------------------------------------------------
    // SPI to AXI4-Lite bridge
    //--------------------------------------------------------------------------
    spi2axi #(
        .SPI_CPOL       (0),
        .SPI_CPHA       (0),
        .AXI_ADDR_WIDTH (AXI_ADDR_WIDTH)
    ) u_spi2axi (
        .spi_sck        (spi_sck),
        .spi_ss_n       (spi_ss_n),
        .spi_mosi       (spi_mosi),
        .spi_miso       (spi_miso),
        .axi_aclk       (clk),
        .axi_aresetn    (rst_n),
        .s_axi_awaddr   (axil_awaddr),
        .s_axi_awprot   (axil_awprot),
        .s_axi_awvalid  (axil_awvalid),
        .s_axi_awready  (axil_awready),
        .s_axi_wdata    (axil_wdata),
        .s_axi_wstrb    (axil_wstrb),
        .s_axi_wvalid   (axil_wvalid),
        .s_axi_wready   (axil_wready),
        .s_axi_bresp    (axil_bresp),
        .s_axi_bvalid   (axil_bvalid),
        .s_axi_bready   (axil_bready),
        .s_axi_araddr   (axil_araddr),
        .s_axi_arprot   (axil_arprot),
        .s_axi_arvalid  (axil_arvalid),
        .s_axi_arready  (axil_arready),
        .s_axi_rdata    (axil_rdata),
        .s_axi_rresp    (axil_rresp),
        .s_axi_rvalid   (axil_rvalid),
        .s_axi_rready   (axil_rready)
    );

    //--------------------------------------------------------------------------
    // Blinky CSR block
    //   Software interface : AXI4-Lite (s_axil_*)
    //   Hardware interface : hwif_in / hwif_out
    //--------------------------------------------------------------------------
    blinky_csr u_blinky_csr (
        .clk            (clk),
        .rst            (~rst_n),
        .s_axil_awaddr  (axil_awaddr),
        .s_axil_awprot  (axil_awprot),
        .s_axil_awvalid (axil_awvalid),
        .s_axil_awready (axil_awready),
        .s_axil_wdata   (axil_wdata),
        .s_axil_wstrb   (axil_wstrb),
        .s_axil_wvalid  (axil_wvalid),
        .s_axil_wready  (axil_wready),
        .s_axil_bresp   (axil_bresp),
        .s_axil_bvalid  (axil_bvalid),
        .s_axil_bready  (axil_bready),
        .s_axil_araddr  (axil_araddr),
        .s_axil_arprot  (axil_arprot),
        .s_axil_arvalid (axil_arvalid),
        .s_axil_arready (axil_arready),
        .s_axil_rdata   (axil_rdata),
        .s_axil_rresp   (axil_rresp),
        .s_axil_rvalid  (axil_rvalid),
        .s_axil_rready  (axil_rready),
        .hwif_in        (hwif_in),
        .hwif_out       (hwif_out)
    );

    //--------------------------------------------------------------------------
    // LED drivers
    //--------------------------------------------------------------------------
    blinky u_blinky1 (
        .clk    (clk),
        .rst    (~rst_n),
        .enable (hwif_out.LED1.enable.value),
        .scalar (hwif_out.LED1.scalar.value),
        .led    (led1)
    );

    blinky u_blinky2 (
        .clk    (clk),
        .rst    (~rst_n),
        .enable (hwif_out.LED2.enable.value),
        .scalar (hwif_out.LED2.scalar.value),
        .led    (led2)
    );

endmodule

`default_nettype wire
