import board
import adafruit_ds18x20
import time
from adafruit_onewire.bus import OneWireBus

probes = []
for pin in (board.D5, board.D6):
    bus = OneWireBus(pin)
    devices = bus.scan()
    for device in devices:
        print("ROM = {} \tFamily = 0x{:02x}".format([hex(i) for i in device.rom], device.family_code))
        probe = adafruit_ds18x20.DS18X20(bus, device)
        probes.append(probe)

# Main loop to print the temperature every second.
while True:
    for n, probe in enumerate(probes):
        print("{} Temperature: {}C".format(n, probe.temperature))
    time.sleep(1.0)

# ROM = ['0x28', '0x64', '0x58', '0x5', '0xf', '0x0', '0x0', '0x74']      Family = 0x28
# ROM = ['0x28', '0x50', '0x7d', '0x5', '0xf', '0x0', '0x0', '0x6f']      Family = 0x28
