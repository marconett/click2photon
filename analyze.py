#!/usr/bin/env python3
"""Latency analyzer using m2p-latency's delta-from-baseline threshold approach.

For each CSV row: averages the pre-click baseline, scans post-click samples
until |sample - baseline| exceeds a threshold, and records that as the latency.
After all rows: computes mean and sample standard deviation (Bessel's correction),
matching m2p-latency's computeStatsMs.
"""
import argparse
import csv
import math
import sys

csv.field_size_limit(sys.maxsize)

DEFAULT_THRESHOLD = 100  # 14-bit ADC units; ~20mV at 3.3V/16383


def compute_latency(row, threshold):
    """Detect screen change using delta-from-baseline, return latency in µs or None."""
    samples = [int(s) for s in row['samples'].split(';') if s.strip()]
    n = len(samples)
    pre_click = int(row.get('preClickSamples', 0))
    duration_us = int(row['timeTaken'])
    us_per_sample = duration_us / n

    # baseline: average of last 200 pre-click samples (or all pre-click if fewer)
    bl_start = max(0, pre_click - 200)
    bl_end = pre_click
    if bl_end <= bl_start:
        return None
    baseline = sum(samples[bl_start:bl_end]) / (bl_end - bl_start)

    # scan post-click samples for threshold crossing
    for i in range(pre_click, n):
        if abs(samples[i] - baseline) > threshold:
            latency_us = (i - pre_click) * us_per_sample
            return latency_us

    return None


def compute_stats_ms(latencies_us):
    """Mean and sample standard deviation in ms (mirrors m2p computeStatsMs)."""
    n = len(latencies_us)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return latencies_us[0] / 1000.0, 0.0

    mean_us = sum(latencies_us) / n
    variance_us = sum((x - mean_us) ** 2 for x in latencies_us) / (n - 1)
    sd_us = math.sqrt(variance_us)

    return mean_us / 1000.0, sd_us / 1000.0


def analyze(path, threshold):
    latencies_us = []
    skipped = 0

    with open(path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            latency = compute_latency(row, threshold)
            if latency is not None:
                latencies_us.append(latency)
                print(f"  #{i+1:<3d} {latency / 1000:.2f} ms")
            else:
                skipped += 1
                print(f"  #{i+1:<3d} no transition detected")

    if not latencies_us:
        print(f"No valid measurements in {path}")
        return

    mean_ms, sd_ms = compute_stats_ms(latencies_us)
    latencies_ms = sorted(l / 1000 for l in latencies_us)
    n = len(latencies_ms)
    median_ms = (latencies_ms[n // 2] if n % 2 else
                 (latencies_ms[n // 2 - 1] + latencies_ms[n // 2]) / 2)

    print(f"\n{path}")
    print(f"  measurements: {n} ({skipped} skipped)")
    print(f"  mean:   {mean_ms:.2f} ms")
    print(f"  sd:     {sd_ms:.2f} ms")
    print(f"  median: {median_ms:.2f} ms")
    print(f"  min:    {latencies_ms[0]:.2f} ms")
    print(f"  max:    {latencies_ms[-1]:.2f} ms")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze latency CSVs (m2p-style)')
    parser.add_argument('files', nargs='+', help='CSV file(s) to analyze')
    parser.add_argument('-t', '--threshold', type=int, default=DEFAULT_THRESHOLD,
                        help=f'ADC delta threshold (default: {DEFAULT_THRESHOLD})')
    args = parser.parse_args()

    for path in args.files:
        analyze(path, args.threshold)
