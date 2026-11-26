"""Temporal mechanism assay for a video super-resolution history-fusion block.

Synthetic, stdlib-only stand-in. A sequence is a list of 1-D frames (lists of
floats in [0, 1]) whose content translates by a constant sub-pixel shift per
frame. Each model aligns the previous frame to the current one with a motion
offset and the assay scores alignment error (mean squared error, lower is
better). Models either take motion offsets from the assay ("warp-*") or
estimate their own ("self-offset").

The assay is run per model with a motion source (`flow`: "block" quarter-pixel
search or "coarse" integer search) and with or without oracle (true) motion.
"""

import random

MODELS = {
    "warp-linear": {"self_offsets": False, "interp": "linear"},
    "warp-nearest": {"self_offsets": False, "interp": "nearest"},
    "self-offset": {"self_offsets": True, "interp": "linear"},
}
FLOWS = ("block", "coarse")
ROOT_CAUSES = (
    "offsets-none-treated-as-zero-motion",
    "flow-estimator-wrong-sign",
    "metric-wrong-reduction",
    "sequence-generator-off-by-one",
    "interpolation-boundary-wrap",
)

# Fill in after investigating results/reported.json (see TASK.md).
DIAGNOSIS = {
    "root_cause": None,
    "invalid_results": [],
    "retracted_conclusions": [],
}


def sample(frame, position, interp):
    width = len(frame)
    if interp == "nearest":
        return frame[int(round(position)) % width]
    left = int(position // 1)
    frac = position - left
    return frame[left % width] * (1 - frac) + frame[(left + 1) % width] * frac


def make_sequence(shift, frames=6, width=64, seed=0):
    rng = random.Random(seed)
    raw = [rng.random() for _ in range(width)]
    base = [(raw[i - 1] + 2 * raw[i] + raw[(i + 1) % width]) / 4 for i in range(width)]
    return [[sample(base, x - shift * t, "linear") for x in range(width)] for t in range(frames)]


def warp(frame, offset, interp):
    """Shift `frame` forward by `offset` pixels."""
    offset = offset or 0.0
    return [sample(frame, x - offset, interp) for x in range(len(frame))]


def mse(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right)) / len(left)


def estimate_flow(prev, cur, flow, max_shift=4):
    if flow not in FLOWS:
        raise ValueError(f"unknown flow source {flow!r}")
    step = 0.25 if flow == "block" else 1.0
    candidates = [i * step for i in range(int(-max_shift / step), int(max_shift / step) + 1)]
    return min(candidates, key=lambda d: (mse(warp(prev, d, "linear"), cur), abs(d)))


def run_assay(model, sequence, flow="block", oracle=True, true_shift=None):
    spec = MODELS[model]
    offsets = true_shift if oracle else None
    errors = []
    for t in range(1, len(sequence)):
        prev, cur = sequence[t - 1], sequence[t]
        if spec["self_offsets"]:
            step_offsets = estimate_flow(prev, cur, "block")
        else:
            step_offsets = offsets
        errors.append(mse(warp(prev, step_offsets, spec["interp"]), cur))
    return {"model": model, "flow": flow, "oracle": oracle, "mse": sum(errors) / len(errors)}


def run_grid(sequence, true_shift):
    rows = []
    for model in MODELS:
        for flow in FLOWS:
            for oracle in (True, False):
                rows.append(run_assay(model, sequence, flow, oracle, true_shift))
    return rows


if __name__ == "__main__":
    for row in run_grid(make_sequence(1.5, seed=7), 1.5):
        print(row)
