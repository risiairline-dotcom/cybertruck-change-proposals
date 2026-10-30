"""Offline synthetic review. No camera, serial, network or robot commands."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import warnings

import cv2
import numpy as np

from reviewed_ring_candidates import refine_ring_v1, refine_ring_v2


def evaluate(fn, img, args, truth):
    record = {}
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        try:
            result = fn(img, *args)
            record['status'] = 'REJECTED' if result is None else 'RETURNED'
            record['result'] = None if result is None else [float(v) for v in result]
            record['center_error_px'] = (None if result is None or truth is None else
                                         float(np.hypot(result[0]-truth[0], result[1]-truth[1])))
        except Exception as exc:
            record.update(status='EXCEPTION', exception=type(exc).__name__, detail=str(exc))
        record['warnings'] = [str(w.message) for w in captured]
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    blank = np.full((400, 400), 255, np.uint8)
    circle = blank.copy()
    cv2.circle(circle, (200, 200), 80, 0, 2, cv2.LINE_AA)
    half = circle.copy()
    half[:, 200:] = 255
    cases = [
        ('blank', blank, (204, 197, 80, 20), None, ['v1', 'v2']),
        ('full_circle', circle, (204, 197, 80, 20), (200, 200), ['v1', 'v2']),
        ('half_circle', half, (204, 197, 80, 20), (200, 200), ['v1', 'v2']),
        ('narrow_full_circle', circle, (205, 200, 80, 8), (200, 200), ['v2']),
    ]
    for axes in [(70, 58), (80, 60)]:
        ellipse = blank.copy()
        cv2.ellipse(ellipse, (200, 200), axes, 12, 0, 360, 0, 2, cv2.LINE_AA)
        cases.append((f'ellipse_{axes[0]}_{axes[1]}', ellipse,
                      (205, 203, sum(axes)/2, 8), (200, 200), ['v2']))
    cases.append(('invalid_zero_dr', circle, (200, 200, 80, 0), (200, 200), ['v2']))
    functions = {'v1': refine_ring_v1, 'v2': refine_ring_v2}
    records = []
    for name, img, params, truth, versions in cases:
        records.append(dict(case=name, image_shape=list(img.shape),
                            image_raw_sha256=hashlib.sha256(img.tobytes()).hexdigest(),
                            parameters=dict(cx=params[0], cy=params[1], r0=params[2], dr=params[3]),
                            true_center=truth,
                            algorithms={v: evaluate(functions[v], img, params, truth) for v in versions}))
    by_name = {r['case']: r['algorithms'] for r in records}
    checks = {
        'v1_blank_returns_spurious_result': by_name['blank']['v1']['status'] == 'RETURNED',
        'v1_half_error_over_5px': (by_name['half_circle']['v1'].get('center_error_px') or 0) > 5,
        'v2_blank_rejected': by_name['blank']['v2']['status'] == 'REJECTED',
        'v2_half_rejected': by_name['half_circle']['v2']['status'] == 'REJECTED',
        'v2_full_circle_error_under_0_1px': (by_name['full_circle']['v2']['status'] == 'RETURNED' and
                                          by_name['full_circle']['v2']['center_error_px'] < .1),
        'v2_ellipse_accepts_error_over_0_8px': (by_name['ellipse_70_58']['v2']['status'] == 'RETURNED' and
                                             by_name['ellipse_70_58']['v2']['center_error_px'] > .8),
        'v2_invalid_dr_raises': by_name['invalid_zero_dr']['v2']['status'] == 'EXCEPTION',
    }
    fixture = Path(__file__).with_name('reviewed_ring_candidates.py')
    report = dict(schema_version=1, domain='synthetic_algorithm_review', physical_acceptance=False,
                  environment=dict(python=platform.python_version(), opencv=cv2.__version__, numpy=np.__version__),
                  fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  limitations=['Synthetic geometry only; no physical accuracy or Pi latency claim.',
                               'Preserved algorithms contain known defects; not production implementations.',
                               'Checks reproduce observed strengths and defects, not release acceptance.'],
                  cases=records, checks=checks, reproduction_checks_passed=all(checks.values()))
    payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8', newline='\n')
    print(json.dumps(dict(environment=report['environment'], checks=checks,
                          reproduction_checks_passed=report['reproduction_checks_passed']), indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
