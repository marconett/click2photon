# Comparing four open-source display latency testers

A comparison of this project (**click2photon**) against three tools that fulfil the same purpose:

- [davidramiro/m2p-latency](https://github.com/davidramiro/m2p-latency)
- [S4N-T0S/Open-Source-LDAT](https://github.com/S4N-T0S/Open-Source-LDAT)
- [OSRTT/OSLTT](https://github.com/OSRTT/OSLTT)

**Quick orientation:** all four measure "input event → visible photon" with a light sensor on the screen, but they split into two design philosophies. **m2p-latency** and **Open-Source-LDAT** are *standalone devices*: they time a live threshold crossing on the microcontroller and show summary stats on an OLED — no host software, no raw data. **OSLTT** and **click2photon** are *capture-and-analyze systems*: the firmware records a full ADC waveform per shot and streams it to the PC, where detection happens offline. This project is visibly a hybrid of the other three — it shares OSLTT's capture architecture almost exactly (14-bit ADC, 12,000 samples, 115200 baud, near-identical CSV header), m2p's delta-from-baseline detection algorithm (credited in `analyze.py`), and OSLTT's dedicated black/white test app idea (the Vulkan color-switcher vs. their DirectX window).

## 1. Measurement approach

| | m2p-latency | Open-Source-LDAT | OSLTT | click2photon |
|---|---|---|---|---|
| Input event | Mouse **move** (±127 px) via ATmega32U4 HID | Real-mouse switch injection (transistor) **or** Teensy as 8 kHz HID mouse | HID keyboard space / mouse click / mouse move | `Mouse.press()` via RP2040 HID |
| Detection | Live busy-poll, \|delta from 1-sample baseline\| > 20 (10-bit) | Live busy-poll, fixed threshold w/ hysteresis (>15 / <10 on 8-bit) | Waveform capture → host-side smoothing + slope-confirmation lookaheads | Waveform capture → host-side \|delta from 200-sample baseline\| > 100 (14-bit) |
| Timing location | On MCU (`micros()`) | On MCU (`elapsedMicros`) | MCU captures, host detects | MCU captures, host detects |
| Raw data kept | No | No (only per-run ms to SD, optionally) | Yes (full 12k-sample CSV) | Yes (full 12k-sample CSV) |
| Pre-click baseline | 1 sample | None (fixed thresholds) | None — capture starts *at* the click; baseline inferred from first 50 samples | 2,000 samples (~48 ms) before the click |

The most important architectural differences:

- **What the click includes.** Open-Source-LDAT's "Automatic" mode is unique: it electrically actuates a *real mouse's* switch, so the measurement includes the mouse's own hardware/firmware/debounce latency — true click-to-photon, and anticheat-invisible (the device can run PC-disconnected on a power bank). Everyone else emulates a HID device, which measures system+display latency but excludes real-mouse internals.
- **Pre-click history.** This project is the only one that samples *before* the click (2,000 samples), giving a proper averaged baseline and letting you see ADC drift. OSLTT starts capturing after the HID call returns and adds the call duration back arithmetically; m2p uses one un-averaged sample as baseline; LDAT uses no baseline at all, just fixed thresholds that must be hand-tuned per monitor.
- **Detection sophistication.** OSLTT has the most elaborate detector (10-sample moving average, pulse/rising/falling branches, multi-point lookahead confirmation at +50/+100/+150 samples, adaptive false-trigger handling) — robust but complex. This project's and m2p's simple delta-threshold is easier to reason about but sensitive to threshold choice; LDAT's fixed absolute threshold is the crudest but runs at the highest speed.

## 2. Measurement accuracy

| | m2p-latency | Open-Source-LDAT | OSLTT | click2photon |
|---|---|---|---|---|
| ADC resolution | 10-bit (overclocked, noisy) | 8-bit (deliberately, for speed) | 14-bit | 14-bit |
| Effective sample interval | ~13–20 µs | ~1–3 µs (600 MHz busy-poll) | ~15.27 µs | ~24 µs (20 µs settling + read) |
| Timer resolution | 4 µs | 1 µs | 1 µs | 1 µs |
| Refresh-phase decorrelation | 574 ms delay (non-divisor of refresh) | Entropy-seeded ±10 ms random jitter | Configurable 0.5–8 s delay, no jitter | Fixed interval, no jitter |
| Stats | Mean + sample SD over 20 runs | Running mean/min/max, B→W and W→B tracked separately | Mean/min/max + **median-based outlier rejection** (>3× or <⅓ median dropped) | Mean, sample SD, median, min/max |
| Calibration aids | Live sensor bar for positioning; fixed 40 µs internal-latency subtraction | Boot-time sensor stability self-check; debug live-ADC mode; thresholds need reflash to change | Per-run sample-period self-calibration; frame-time subtraction | Documented 20 µs settling fix; `-t` threshold override |

Accuracy verdicts per tool:

- **Open-Source-LDAT** has the best *temporal* precision (sub-3 µs detection granularity, 1 µs timer, genuine 8 kHz USB polling via a build-time Teensy core patch that cuts HID poll quantization to 0–125 µs) but the worst *amplitude* precision (8-bit ADC, fixed thresholds calibrated for OLED monitors — LCD users must retune). Its README is also the most honest about the latency pipeline: min/max spread of several ms is expected physics (frame timing + scanout), not instrument error.
- **OSLTT** is the only one that decomposes the result: it measures the test window's frame time (~1000 FPS DirectX app, QueryPerformanceCounter) and reports `onDisplayLatency = total − frameTime`, plus a "pretest" mode that subtracts system baseline to isolate game-engine latency. It's also the only one with outlier rejection. Weaknesses admitted in its own code: frame time is logged one frame late, and the moving average shifts the detected transition by 10 samples.
- **m2p-latency** is the roughest: single-sample baseline, ADC clocked 8× beyond its datasheet accuracy limit, 4 µs timer, USB poll jitter of the Pro Micro uncharacterized. The README itself calls it "a rough estimate." Its one clever accuracy feature — the 574 ms inter-cycle delay chosen not to divide the refresh rate — reappears in stronger form as LDAT's randomized jitter.
- **click2photon** has the best amplitude fidelity of the capture-based pair: 14-bit ADC *plus* the 20 µs settling delay (OSLTT reads flat-out with no settling, which compresses dynamic range), and the only real pre-click baseline. Trade-offs: the ~24 µs sample interval quantizes detection slightly coarser than OSLTT's ~15 µs, latency is reconstructed as `index × (timeTaken/sampleCount)` (assumes uniform sample spacing), and there is no refresh-phase jitter/decorrelation between shots — worth stealing from LDAT.

## 3. Hardware choice

| | m2p-latency | Open-Source-LDAT | OSLTT | click2photon |
|---|---|---|---|---|
| MCU | Arduino Pro Micro (ATmega32U4, 16 MHz, ~$8) | Teensy 4.1 (Cortex-M7 @ 600 MHz, ~$35) | Seeeduino XIAO / custom SAMD21 PCB | Adafruit QT Py RP2040 (~$10) |
| Sensor | TEMT6000 phototransistor breakout | TEMT6000 phototransistor breakout | VBPW34SR photodiode + TSV7721 transimpedance amp (1 MΩ) | BPW34 photodiode + TLC271 transimpedance amp |
| Extra hardware | SSD1306 OLED, MX button | SSD1306 OLED, button, BC547 mouse-injection circuit, microSD logging | Mic input + amp, 2-pin/3-pin trigger inputs, button, LED; sold as assembled kit | KiCad PCB, breadboard layout, 3D-printed enclosure |
| Approx. cost | ~$15–20 | ~$45–55 + donor mouse | Commercial kit (osrtt.com); ~$10–20 BOM class | ~$15–25 |

Two meaningful splits here. First, **phototransistor vs. photodiode+amp**: the TEMT6000 (m2p, LDAT) is a $2 plug-and-play breakout — simple but slower and less linear. This project and OSLTT independently chose the harder path of a PIN photodiode with a transimpedance amplifier, which gives faster, more linear response at the cost of analog design work (BPW34+TLC271 vs. their VBPW34SR+TSV7721 are essentially the same circuit with different parts). Second, **MCU horsepower**: LDAT's Teensy 4.1 is wildly overpowered on purpose — the 600 MHz core is what buys the ~1 µs detection loop. The other three all use ~$5–10 hobby boards where USB HID support was the actual selection criterion. OSLTT is the only one that graduated to a custom manufactured PCB sold as a product.

## 4. Ease of use

- **m2p-latency** is the easiest to *operate*: plug in USB, point at testufo.com/flicker or a game, press the button, read mean±σ off the OLED 20 clicks later. No software, OS-agnostic. But it's the least flexible — changing anything (cycle count, threshold) means recompiling, and there's no data export at all.
- **Open-Source-LDAT** is the hardest to *build* (soldering, sacrificing a mouse for Automatic mode, per-monitor threshold tuning that requires editing `config.h` and reflashing via PlatformIO) but pleasant to run: one-button on-device menu, run limits of 10/100/300/500/unlimited, live stats, optional CSV to microSD. It needs a third-party "latency marker" on screen (NVIDIA Reflex flash indicator, RTSS FCAT bar, or Aperture Grille) — those tools are Windows-centric even though the device itself is OS-agnostic. Documentation is excellent.
- **OSLTT** is the most polished end-user experience by far — it's a commercial product: Windows installer, GUI that auto-installs drivers and auto-flashes firmware updates, built-in ~1000 FPS DirectX test window, up to 990 automated shots, result charts, CSV export of both raw and processed data, and extra modes nobody else has (peripheral click latency via microphone/electrical tap, audio latency, controller latency). The cost: Windows-only, closed ecosystem feel, and a large codebase its own author calls imperfect.
- **click2photon** is the most developer/researcher-oriented: CLI workflow (`uv run main.py`, `uv run analyze.py`), full raw waveforms in versioned CSVs, a purpose-built low-latency Vulkan test app, and macOS support — which none of the other three targets (OSLTT is Windows-only; the standalone devices are OS-agnostic but their recommended marker apps are Windows tools). The trade-off is that it's a three-part manual workflow (start Vulkan app, run terminal UI, run analyzer) with no GUI and no on-device operation.

## Takeaways

Ideas worth borrowing: **LDAT's randomized inter-shot jitter** (decorrelating from display refresh) is a cheap accuracy win the fixed-interval firmware currently lacks; **OSLTT's frame-time subtraction and median-based outlier rejection** would let `analyze.py` separate display response from pipeline latency; and **LDAT's real-mouse switch injection** is the only approach here that captures true click-to-photon including mouse hardware latency. Conversely, the combination of pre-click baseline sampling, 14-bit ADC with settling delay, and full waveform retention gives this project better post-hoc analyzability than any of the three references — none of them can re-analyze old runs with a different detection algorithm, and this one can.
