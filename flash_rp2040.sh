#! /bin/sh

# https://docs.arduino.cc/arduino-cli/

arduino-cli compile --fqbn rp2040:rp2040:adafruit_qtpy arduino
arduino-cli upload -p /dev/cu.usbmodem101 --fqbn rp2040:rp2040:adafruit_qtpy arduino