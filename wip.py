# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import os
import board
import busio
import digitalio
import ipaddress
import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_ds18x20
import time
from adafruit_onewire.bus import OneWireBus
import supervisor
from displayio import Group
from adafruit_display_text import bitmap_label
import terminalio


### WIFI

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

print("Available WiFi networks:")
for network in wifi.radio.start_scanning_networks():
    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
            network.rssi, network.channel))
wifi.radio.stop_scanning_networks()

print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

ipv4 = ipaddress.ip_address("8.8.4.4")
print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))

pool = socketpool.SocketPool(wifi.radio)

### MQTT

# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to MQTT Broker!")
    # print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))


# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=secrets['mqtt_broker'],
    socket_pool=pool,
)

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_publish = publish

### Probes

probes = []
print("Looking for probes...")
bus = OneWireBus(board.D5)
devices = bus.scan()
for device in devices:
    print("ROM = {} \tFamily = 0x{:02x}".format([hex(i) for i in device.rom], device.family_code))
    probe = adafruit_ds18x20.DS18X20(bus, device)
    probes.append(probe)
if len(probes) != 2:
    print("Didn't find 2 probes, resetting...")
    supervisor.reload()
probes.sort(key=lambda x: x.rom)

### Charger

chg = digitalio.DigitalInOut(board.D13)
chg.direction = digitalio.Direction.INPUT

pgood = digitalio.DigitalInOut(board.D12)
pgood.direction = digitalio.Direction.INPUT

### Display
text_area = bitmap_label.Label(terminalio.FONT, scale=2)
text_area.anchor_point = (0.5, 0.5)
text_area.anchored_position = (board.DISPLAY.width // 2, board.DISPLAY.height // 2)
text_area.text = "Pool Thermometer"

main_group = Group()
main_group.append(text_area)

board.DISPLAY.show(main_group)


def send_probe(n, probe):
    try:
        temp = probe.temperature / 5.0 * 8.0 + 32.0
        print(f"Temperature {n}: {temp}F")
        mqtt_client.publish(f"pool_temp/{n}", f'{{"temp": {temp}}}')
        return temp, None
    except Exception as e:
        err = str(e)
        print(f"Error {n}: {err}")
        mqtt_client.publish("pool_temp/{n}/error", err)
        return None, err


# Main loop to print the temperature every second.
while True:
    try:
        mqtt_client.connect()
        mqtt_client.publish("pool_temp/charger", '{{"chg": {}, "pgood": {}}}'.format(not chg.value, not pgood.value))
        temp0, err0 = send_probe(0, probes[0])
        temp1, err1 = send_probe(1, probes[1])
        mqtt_client.disconnect()
        lines = []
        if temp0:
            lines.append(f"Temp 0: {temp0:0.1f} F")
        else:
            lines.append(f"Temp 0: {err0}")
        if temp1:
            lines.append(f"Temp 1: {temp1:0.1f} F")
        else:
            lines.append(f"Temp 1: {err1}")
        text_area.text = "\n".join(lines)
    except Exception as e:
        print(e)
        try:
            mqtt_client.publish("pool_temp/error", str(e))
            mqtt_client.connect()
            mqtt_client.disconnect()
        except:
            print("Failed to publish error")
        # supervisor.reload()
    time.sleep(10.0)
