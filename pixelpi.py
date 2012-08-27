import sys
import RPi.GPIO as GPIO
import time
import argparse
import socket

#3 bytes per pixel
PIXEL_SIZE = 3

gamma = bytearray(256)

# Apply Gamma Correction and RGB / GRB reordering
# Optionally perform brightness adjustment
def filter_pixel(input_pixel, brightness):
    input_pixel[0] = int(brightness * input_pixel[0])
    input_pixel[1] = int(brightness * input_pixel[1])
    input_pixel[2] = int(brightness * input_pixel[2])
    output_pixel = bytearray(PIXEL_SIZE)
    if args.chip_type == "LDP8806":
        # Convert RGB into GRB bytearray list.
        output_pixel[0] = gamma[input_pixel[1]]
        output_pixel[1] = gamma[input_pixel[0]]
        output_pixel[2] = gamma[input_pixel[2]]
    else:
        output_pixel[0] = gamma[input_pixel[0]]
        output_pixel[1] = gamma[input_pixel[1]]
        output_pixel[2] = gamma[input_pixel[2]]
    return output_pixel


parser = argparse.ArgumentParser(add_help=True,version='1.0')
parser.add_argument('--chip',
        action='store',
        dest='chip_type',
        default='WS2801',
        choices=['WS2801', 'LDP8806'],
        help='Specify chip type LDP8806 or WS2801')
parser.add_argument('--mode',
        action='store',
        dest='mode',
        required=True,
        choices=['pixelinvaders', 'all_off', 'all_on'],
        help='Choose the display mode')
parser.add_argument('--verbose',
        action='store_true',
        dest='verbose',
        default=True,
        help='enable verbose mode')
parser.add_argument('--array_width',
        action='store',
        dest='array_width',
        required=False,
        type=int,
        default='7',
        help='Set the X dimension of your pixel array (width)')
parser.add_argument('--array_height',
        action='store',
        dest='array_height',
        required=False,
        type=int,
        default='7',
        help='Set the Y dimension of your pixel array (height)')
parser.add_argument('--spi_dev',
        action='store',
        dest='spi_dev_name',
        required=False,
        default='/dev/spidev0.0',
        help='Set the SPI device descriptor')
parser.add_argument('--refresh_rate',
        action='store',
        dest='refresh_rate',
        required=False,
        default=500,
        type=int,
        help='Set the refresh rate in ms (default 500ms)')
parser.add_argument('--num_leds',
        action='store',
        dest='num_leds',
        required=False,
        default=50,
        type=int,  help='Set the  number of LEDs in the string (used in fade and chase mode)')
parser.add_argument('--udp-ip',
	action='store',
	dest='UDP_IP',
	required=False,
	default='192.168.1.1',
	help='Used for PixelInvaders mode, listening address')
parser.add_argument('--udp-port',
	action='store',
	dest='UDP_PORT',
	required=False,
	default=6803,
	type=int,
	help='Used for PixelInvaders mode, listening port')
args = parser.parse_args()

print "Chip Type             = %s" % args.chip_type
print "Display Mode          = %s" % args.mode
print "SPI Device Descriptor = %s" % args.spi_dev_name
print "Refresh Rate          = %sms" % args.refresh_rate
print "Array Dimensions      = %dx%d" % (args.array_width, args.array_height)

# Open SPI device, load image in RGB format and get dimensions:
spidev = file(args.spi_dev_name, "wb")

# Calculate gamma correction table. This includes
# LPD8806-specific conversion (7-bit color w/high bit set).
if args.chip_type == "LDP8806":
    for i in range(256):
        gamma[i] = 0x80 | int(pow(float(i) / 255.0, 2.5) * 127.0 + 0.5)

if args.chip_type == "WS2801":
    for i in range(256):
        gamma[i] = int(pow(float(i) / 255.0, 2.5) * 255.0 )

if args.mode == 'pixelinvaders':
	print ("Start PixelInvaders listener at "+args.UDP_IP+":"+str(args.UDP_PORT))
	sock = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
	sock.bind( (args.UDP_IP,args.UDP_PORT) )
	while True:
		data, addr = sock.recvfrom( 1024 ) # buffer size is 1024 bytes blocking call
        send_data_to_spi(data)

if args.mode == 'all_off':
    pixel_output = bytearray(args.num_leds * PIXEL_SIZE + 3)
    print "Turning all LEDs Off"
    send_data_to_spi(pixel_output)    

if args.mode == 'all_on':
    pixel_output = bytearray(args.num_leds * PIXEL_SIZE + 3)
    print "Turning all LEDs On"
    for led in range(args.num_leds):
        pixel_output[led*PIXEL_SIZE:] = filter_pixel(WHITE, 1)
    send_data_to_spi(pixel_output)

def send_data_to_spi(pixel_output):
                spidev.write(pixel_output)
                spidev.flush()

