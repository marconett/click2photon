#! /bin/sh
set -e

# https://docs.arduino.cc/arduino-cli/

# The rp2040:rp2040 core (earlephilhower/arduino-pico) lives in a third-party
# index, so it must be installed with the board manager URL on a fresh machine.
RP2040_INDEX_URL="https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json"

if ! arduino-cli core list | grep -q '^rp2040:rp2040'; then
    arduino-cli core update-index --additional-urls "$RP2040_INDEX_URL"
    arduino-cli core install rp2040:rp2040 --additional-urls "$RP2040_INDEX_URL"
fi

if ! arduino-cli lib list "Adafruit NeoPixel" | grep -q 'Adafruit NeoPixel'; then
    arduino-cli lib install "Adafruit NeoPixel"
fi

# Port: first CLI arg, else first matching device (macOS: cu.usbmodem*, Linux: ttyACM*)
PORT="${1:-$(ls /dev/cu.usbmodem* /dev/ttyACM* 2>/dev/null | head -n 1)}"
if [ -z "$PORT" ]; then
    echo "error: no serial port found (/dev/cu.usbmodem* or /dev/ttyACM*); pass one as first arg" >&2
    exit 1
fi

arduino-cli compile --fqbn rp2040:rp2040:adafruit_qtpy arduino
arduino-cli upload -p "$PORT" --fqbn rp2040:rp2040:adafruit_qtpy arduino
