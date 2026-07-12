#!/usr/bin/env python3
"""Latency analyzer using m2p-latency's delta-from-baseline threshold approach.

For each CSV row: averages the pre-click baseline, scans post-click samples
until |sample - baseline| exceeds a threshold, and records that as the latency.
After all rows: computes mean and sample standard deviation (Bessel's correction),
matching m2p-latency's computeStatsMs.

Arguments may be CSV files or folders. A folder is scanned recursively for
.csv files and analyzed as one pooled group: stats are computed across all
clicks from all files, and the margin of error is design-effect adjusted,
treating each file as a session (cluster). Single files get the naive margin
of error, since between-session variance can't be estimated from one session.
"""
import argparse
import csv
import math
import os
import sys

csv.field_size_limit(sys.maxsize)

DEFAULT_THRESHOLD = 100  # 14-bit ADC units; ~20mV at 3.3V/16383
Z_95 = 1.96


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


def margin_of_error_ms(sessions_us):
    """95% margin of error of the mean, in ms.

    sessions_us: list of per-file latency lists (µs). Naive CI (1.96·sd/√n),
    inflated by √(design effect) when ≥2 sessions allow estimating
    between-session variance via one-way ANOVA. Sessions that drift produce a
    wider margin; statistically identical sessions leave the naive CI intact.
    """
    all_us = [x for s in sessions_us for x in s]
    n = len(all_us)
    if n < 2:
        return 0.0
    _, sd_ms = compute_stats_ms(all_us)
    naive_ms = Z_95 * sd_ms / math.sqrt(n)

    sessions = [s for s in sessions_us if s]
    k = len(sessions)
    if k < 2 or n <= k:
        return naive_ms

    grand = sum(all_us) / n
    means = [sum(s) / len(s) for s in sessions]
    ss_between = sum(len(s) * (m - grand) ** 2 for s, m in zip(sessions, means))
    ss_within = sum(sum((x - m) ** 2 for x in s) for s, m in zip(sessions, means))
    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (n - k)
    if ms_within == 0:
        return naive_ms

    m_avg = n / k
    icc = max(0.0, (ms_between - ms_within) / (ms_between + (m_avg - 1) * ms_within))
    deff = 1 + (m_avg - 1) * icc
    return naive_ms * math.sqrt(deff)


def read_latencies(path, threshold):
    """Latencies (µs) and skipped-row count for one CSV file."""
    latencies_us = []
    skipped = 0
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            latency = compute_latency(row, threshold)
            if latency is not None:
                latencies_us.append(latency)
            else:
                skipped += 1
    return latencies_us, skipped


def analyze(path, threshold):
    if not os.path.exists(path):
        print(f"No such file or directory: {path}")
        return
    if os.path.isdir(path):
        files = sorted(
            os.path.join(root, name)
            for root, _, names in os.walk(path)
            for name in names
            if name.endswith('.csv')
        )
        if not files:
            print(f"No CSV files found in {path}")
            return
        label = f"{path} ({len(files)} files)"
    else:
        files = [path]
        label = path

    sessions_us = []
    skipped = 0
    for f in files:
        lats, skip = read_latencies(f, threshold)
        sessions_us.append(lats)
        skipped += skip

    latencies_us = [x for s in sessions_us for x in s]
    if not latencies_us:
        print(f"No valid measurements in {path}")
        return

    mean_ms, sd_ms = compute_stats_ms(latencies_us)
    moe_ms = margin_of_error_ms(sessions_us)
    latencies_ms = sorted(l / 1000 for l in latencies_us)
    n = len(latencies_ms)
    median_ms = (latencies_ms[n // 2] if n % 2 else
                 (latencies_ms[n // 2 - 1] + latencies_ms[n // 2]) / 2)

    print(f"\n{label}")
    print(f"  measurements: {n} ({skipped} skipped)")
    print(f"  mean:   {mean_ms:.2f} ms ± {moe_ms:.2f} ms (95% CI)")
    print(f"  sd:     {sd_ms:.2f} ms")
    print(f"  median: {median_ms:.2f} ms")
    print(f"  min:    {latencies_ms[0]:.2f} ms")
    print(f"  max:    {latencies_ms[-1]:.2f} ms")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze latency CSVs (m2p-style)')
    parser.add_argument('files', nargs='+',
                        help='CSV file(s) and/or folder(s); folders are scanned '
                             'recursively and pooled into one result each')
    parser.add_argument('-t', '--threshold', type=int, default=DEFAULT_THRESHOLD,
                        help=f'ADC delta threshold (default: {DEFAULT_THRESHOLD})')
    args = parser.parse_args()

    for path in args.files:
        analyze(path, args.threshold)
