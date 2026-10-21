"""Sample diagnostics from an unmodified delivery .toe, without injecting input.

FPS and P95 are the runtime's rolling 600-frame statistics, not independent
per-second frame counters. No camera images, coordinates or landmarks are saved.
"""
import argparse
import json
from pathlib import Path
import statistics
import time


def monitor(folder, seconds, output):
    started = time.monotonic()
    previous_stamp = None
    samples = []
    failures = 0
    while time.monotonic() - started < seconds:
        status = folder / '.runtime/status.json'
        try:
            stamp = status.stat().st_mtime_ns
            if stamp != previous_stamp:
                value = json.loads(status.read_text(encoding='utf-8'))
                samples.append(dict(second=round(time.monotonic()-started, 2),
                    fps=value.get('fps'), p95_ms=value.get('p95_ms'),
                    inference_ms=value.get('inference_ms'),
                    camera=value.get('camera', {}).get('state'),
                    active=value.get('input', {}).get('active', False),
                    palm_active=value.get('input', {}).get('palm_active', False),
                    effect=value.get('input', {}).get('effect', 'none'),
                    hands=value.get('hand_count', 0), errors=value.get('errors', {})))
                previous_stamp = stamp
        except (OSError, ValueError):
            failures += 1
        time.sleep(1)
    fps = [s['fps'] for s in samples if s['fps'] is not None]
    report = dict(seconds=time.monotonic()-started,
        method='one-second sampling of overlapping rolling 600-frame runtime statistics',
        sample_count=len(samples), read_failures=failures,
        min_rolling_fps=min(fps) if fps else None,
        mean_rolling_fps=statistics.mean(fps) if fps else None,
        max_rolling_p95_ms=max((s['p95_ms'] for s in samples if s['p95_ms'] is not None), default=None),
        samples_with_active_input=sum(bool(s['active']) for s in samples),
        samples_with_palm_input=sum(bool(s['palm_active']) for s in samples),
        palm_effects_seen=sorted({s['effect'] for s in samples if s['palm_active']}),
        samples_with_hands=sum(bool(s['hands']) for s in samples), samples=samples)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'samples'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--seconds', type=float, default=300)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    monitor(args.folder, args.seconds, args.output)
