# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an end-to-end display latency measurement tool. It measures the time from a mouse click to visible screen change using custom hardware (photodiode + RP2040 microcontroller). The system has three layers: firmware, host software, and hardware.

## Architecture

**Measurement flow:** The RP2040 sends a USB HID mouse click → color-switcher app toggles screen black/white → photodiode detects the change → ADC samples are sent over serial → `main.py` logs to CSV → `analyze.py` calculates latency.

### Firmware (`arduino/arduino.ino`)
- Runs on Adafruit QT Py RP2040 (`rp2040:rp2040:adafruit_qtpy`)
- 14-bit ADC on pin A1 reads photodiode via transimpedance amplifier (BPW34 + TLC271IP)
- Collects 12,000 ADC samples per test run with 20µs settling delay between reads (~288ms window), sends as CSV-prefixed serial line
- Uses `Mouse.press()`/`Mouse.release()` instead of blocking `Mouse.click()` — press is non-blocking (~15µs), sampling starts immediately
- 20µs ADC settling delay is critical: without it, the sample-and-hold capacitor doesn't fully discharge, compressing dynamic range (black reads ~1238 instead of ~950)
- `Serial.flush()` after each CSV line ensures USB bus is idle before next measurement (HID and CDC share the bus)
- Serial protocol: lines starting with `CSV` are data rows; all other output is debug/status

### Host Control Software (`main.py`)
- Async serial terminal using `prompt_toolkit` for interactive control
- Auto-detects the device by USB VID/PID (0x239A/0x80F7, Adafruit QT Py RP2040) at 115200 baud; falls back to `/dev/cu.usbmodem*`/`/dev/ttyACM*` name matching. Pass a port as first CLI arg to override (`uv run main.py /dev/ttyACM1`). Ports are re-scanned on every connect, so Linux re-enumeration (ttyACM0 → ttyACM1) is handled automatically.
- Commands: `start`, `stop`, `debug`/`d`, `interval <n>`/`i <n>`, `clicks <n>`/`c <n>`, `connect`, `disconnect`
- CSV output goes to `output/` with timestamp-based filenames

### Color Switcher (`color-switcher-vulkan/`)
- C++ Vulkan app for low-latency rendering. Toggles the screen black/white on mouse click.

### Data Processing
- `analyze.py`: Latency analyzer using m2p-latency's delta-from-baseline threshold approach. Per CSV row: averages the last 200 pre-click samples as baseline, scans post-click samples for a threshold crossing (default 100 ADC units, `-t` to override), reports mean (± 95% margin of error), median, p5, p95, p95−p5 spread, min, max, plus an ASCII histogram (0.5ms bins). Arguments can be CSV files or folders: a folder is scanned recursively for `.csv` files and pooled into one result, with the margin of error design-effect adjusted across files (each file = one session); single files get the naive 1.96·sd/√n margin. Terminal output only, no plotting. `--json` prints the stats as a JSON array instead; the stats logic is importable via `collect_stats()`.
- `analyze_all.py`: chart-JSON wrapper — analyzes every direct subfolder of a given folder (`uv run analyze_all.py test_run/output`) via `collect_stats()` and prints chart-ready JSON with two top-level keys: `main` (labels = subfolder names, datasets = median/margin of error/p5/p95, sorted fastest median first) and `histogram` (0.5ms bins shared across all cases; labels = bin lower edges in ms, one dataset of counts per case).

### Hardware (`hardware/`)
- KiCad PCB files, breadboard layout (`breadboard.diy`), 3D-printable enclosure

## Commands

### Python environment
Managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`):
```
uv sync
```

### Run host software
```
uv run main.py
```

### Process latency data
```
uv run analyze.py <csv_file_or_folder> [<csv_file_or_folder> ...] [-t <threshold>]
```

### Firmware compile and flash
```
./flash_rp2040.sh                 # installs the rp2040 core on first run, auto-detects the port
./flash_rp2040.sh /dev/ttyACM1    # or pass the port explicitly
# or manually (the rp2040:rp2040 core comes from a third-party index, not Arduino's default):
arduino-cli core install rp2040:rp2040 --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli compile --fqbn rp2040:rp2040:adafruit_qtpy arduino
arduino-cli upload -p /dev/cu.usbmodem101 --fqbn rp2040:rp2040:adafruit_qtpy arduino
```

### Vulkan color switcher
```
# Dependencies (macOS): brew install vulkan-headers vulkan-loader molten-vk glfw cmake
./build_vulkan.sh
./run_vulkan.sh
```

## CSV Format

```
clickTime,timeTaken,sampleCount,preClickSamples,samples
20,720500,12000,2000,1280;1284;1284;...
```

- `clickTime`: microseconds for Mouse.press() call (~15-20µs)
- `timeTaken`: total ADC sampling duration in microseconds (pre-click + post-click)
- `sampleCount`: total number of ADC samples
- `preClickSamples`: number of samples collected before the mouse click (pre-click baseline)
- `samples`: semicolon-separated 14-bit ADC values (0-16383)
