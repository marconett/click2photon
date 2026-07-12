# analyze.py output explained

Each value describes the click-to-photon latencies of one file or one pooled folder (all clicks from all its CSV files together).

- **measurements** — number of clicks with a detected screen change. *skipped* = clicks where no change crossed the threshold (bad sample, missed click); they are excluded from all stats.

- **mean ± … (95% CI)** — average latency. The ± is the uncertainty of that average: rerunning the same test would land the mean inside this range 95% of the time. Two cases whose ranges don't overlap are genuinely different. For folders, the margin is widened if the individual sessions disagree with each other.

- **median** — the middle click: half were faster, half slower. Like the mean but immune to a few extreme values.

- **p5** — the fast tail: 5% of clicks were faster than this. Approximates the best-case pipeline latency (click landed at the luckiest moment of the refresh cycle). A robust version of *min*.

- **p95** — the slow tail: 5% of clicks were slower than this. The "feels laggy" number — worst cases players actually notice. Where frame-pacing features should show their effect.

- **spread (p95 − p5)** — consistency: how wide the typical latency range is. Smaller = more predictable feel. More meaningful than sd, which is inflated the same way everywhere.

- **min / max** — single fastest and slowest click. Sanity checks only; each is one sample, so don't base conclusions on them.

- **histogram** — latency distribution in 0.5 ms bins; each row shows a bin's count as a bar. Shows the shape a single number can't: whether the whole block shifts between cases, whether a case has a longer tail, or whether clicks clump at multiples of the 2 ms frame period.
