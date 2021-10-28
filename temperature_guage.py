import plasma
import time
import machine
import utime
from plasma import plasma2040
from pimoroni import Analog

NUM_LEDS = 60
FPS = 60
SAT = 0.9
BRIGHT = 0.2

led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma2040.DAT)

led_strip.start(FPS)
led_strip.set_hsv(0, 0.0, SAT, BRIGHT)

sense = Analog(plasma2040.CURRENT_SENSE, plasma2040.ADC_GAIN, plasma2040.SHUNT_RESISTOR)
print("Current =", sense.read_current(), "A")

temp_led = 0
offset = 0.95
shift = 16
count = 0

# Create the CRC subr
def crc(data, crcchk, n=8, poly=0x31, crc=0):
    g = 1 << n | poly  # Generator polynomial

    # Loop over the data
    for d in data:
        # XOR the top byte in the CRC with the input byte
        crc ^= d << (n - 8)

        # Loop over all the bits in the byte
        for _ in range(8):
            # Start by shifting the CRC, so we can check for the top bit
            crc <<= 1

            # XOR the CRC if the top bit is 1
            if crc & (1 << n):
                crc ^= g

    # Return the CRC result
    return crc.to_bytes(1, 'big') == crcchk

# calculate temp deg C
def temp_c(tempint):
    return (tempint / 65535) * 165 - 40

# calculate RH %
def rh(rhint):
    return (rhint / 65535) * 100

# Create I2C object
i2c = machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20), freq=400000)

buff8 = bytearray(8)
buff3 = bytearray(3)
obuff = bytes
crcbuff = bytes

d = 64  # Device id 0x40

# print("Serial No.")
# i2c.writeto(d, b'\x0A')
# utime.sleep_ms(5)
# i2c.readfrom_into(d, buff3, True)
# print(int.from_bytes(buff3, 'big'))

def gettemp(d):
    # print("Set conversion resolution")
    i2c.writeto(d, b'\x40')
    utime.sleep_ms(5)

    i2c.writeto(d, b'\x00')
    utime.sleep_ms(5)
    i2c.readfrom_into(d, buff8, True)
    # print([hex(b) for b in buff8])
    obuff = bytes(buff8[0:2])
    crcbuff = bytes({buff8[2]})
    # print("Buffer:", obuff, "CRC:", crcbuff)
    if crc(obuff, crcbuff):
        # print("CRC OK")
        tempdegc = temp_c(int.from_bytes(obuff, 'big'))
        # print('Temp: ', tempdegc, 'C')
        return tempdegc
    else:
        return 0

while True:

    for i in range(NUM_LEDS):
        if i == temp_led:
            led_strip.set_hsv((NUM_LEDS - 1) - temp_led, 0.85, 1.0, 0.4)
        else:
            hue = float(i) / NUM_LEDS / 1.3
            led_strip.set_hsv((NUM_LEDS - 1) - i, hue + offset, SAT, BRIGHT)

    count += 1
    if count >= FPS:
        # Display the current value once every second
        # print("Current =", sense.read_current(), "A")
        temp = round(gettemp(d) * 2)
        count = 0
        temp_led = NUM_LEDS - (temp - shift % NUM_LEDS)
        print(temp, temp_led)

    time.sleep(1.0 / FPS)
