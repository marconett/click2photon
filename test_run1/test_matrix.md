# Test Matrix

Three dimensions, two values each → **8 test cases**.

**Dimensions**
- **Display server:** X11 / Wayland
- **`PROTON_DXVK_LOWLATENCY`:** ON / OFF
- **VRR:** ON / OFF

- Plus another 2 special test cases for XWayland

---

## Test Cases

| #  | Display | LOWLATENCY | VRR | Special case | Done |
|----|---------|------------|-----|--------------|------|
| 1  | X11     | ON         | ON  | -            | [x]  |
| 2  | X11     | ON         | OFF | -            | [x]  |
| 3  | X11     | OFF        | ON  | -            | [x]  |
| 4  | X11     | OFF        | OFF | -            | [x]  |
| 5  | Wayland | ON         | ON  | -            | [x]  |
| 6  | Wayland | ON         | OFF | -            | [x]  |
| 7  | Wayland | OFF        | ON  | -            | [x]  |
| 8  | Wayland | OFF        | OFF | -            | [x]  |
| 9  | Wayland | ON         | OFF | XWayland     | [x]  |
| 10 | Wayland | OFF        | OFF | XWayland     | [x]  |

---


## Per-Case Notes

### Case 1 — X11 · LOWLATENCY ON · VRR ON
- stable 480 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 480
dxvk.lowLatencyOffset = 70
dxvk.framePace = "low-latency-vrr-500"
dxvk.lowLatencyAllowCpuFramesOverlap = False
```

### Case 2 — X11 · LOWLATENCY ON · VRR OFF
- stable 500 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 500
```

### Case 3 — X11 · LOWLATENCY OFF · VRR ON
- stable 497 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 497
```

### Case 4 — X11 · LOWLATENCY OFF · VRR OFF
- stable 500 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 500
```

### Case 5 — Wayland · LOWLATENCY ON · VRR ON
- stable 480 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 480
dxvk.lowLatencyOffset = 70
dxvk.framePace = "low-latency-vrr-500"
dxvk.lowLatencyAllowCpuFramesOverlap = False
```

### Case 6 — Wayland · LOWLATENCY ON · VRR OFF
- stable 500 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 500
```

### Case 7 — Wayland · LOWLATENCY OFF · VRR ON
- stable 497 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 497
```

### Case 8 — Wayland · LOWLATENCY OFF · VRR OFF
- stable 500 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 500
```

### Case 9 — Wayland · LOWLATENCY ON · VRR OFF · XWayland
- special case: comparing XWayland vs native wayland
- stable 500 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 500
```

### Case 10 — Wayland · LOWLATENCY OFF · VRR OFF · XWayland
- special case: comparing XWayland vs native wayland
- stable 500 fps

```conf
# dxvk.conf
dxgi.maxFrameRate = 500
```