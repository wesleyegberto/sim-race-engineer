"""Estimates per-tyre wear percentage from the geometric rolling radius.

GT7 UDP exposes the game-computed tyre radius at offsets 0xB4–0xC0 (one f32
per wheel). On a fresh tyre this equals the nominal geometric radius; as rubber
wears the game shrinks it progressively.

A 300-sample rolling buffer uses the MEDIAN rather than the mean, making the
estimator robust against momentary deformation spikes. Sampling is gated by
`sample_every` (default 6): only 1 in every 6 frames is recorded, so the
buffer covers ~30 s of driving at 60 Hz.

Sampling is skipped when `speed_ms < _MIN_SPEED_MS` because GT7 sends 0.0 (or
the static nominal radius) for radius while the car is stationary or loading.

The first full buffer locks R_baseline as the median of those readings. All
subsequent readings compute wear relative to that baseline using the configured
wear_range_m depth.

Reset on new race/stint via reset().
"""

import logging
import statistics
from collections import deque

log = logging.getLogger(__name__)

_BUFFER_SIZE = 300
_VALID_RADIUS = (0.25, 0.40)   # metres — clamp outliers
_MIN_SPEED_MS = 5.0             # ignore samples while nearly stopped
_NEW_TYRE_TOLERANCE = 0.003     # 3 mm jump above baseline → tyre replaced


class TireWearEstimator:
    def __init__(self, wear_range_m: float = 0.007, sample_every: int = 6) -> None:
        self._wear_range_m = wear_range_m
        self._sample_every = max(1, sample_every)
        self._buffers: list[deque[float]] = [deque(maxlen=_BUFFER_SIZE) for _ in range(4)]
        self._r_baseline: list[float | None] = [None] * 4
        self._frame_counter: int = 0

    def reset(self) -> None:
        for buf in self._buffers:
            buf.clear()
        self._r_baseline = [None] * 4
        self._frame_counter = 0

    @property
    def wear_range_m(self) -> float:
        return self._wear_range_m

    @wear_range_m.setter
    def wear_range_m(self, value: float) -> None:
        self._wear_range_m = max(0.001, value)

    def update(
        self,
        radii: list[float],
        speed_ms: float,
    ) -> list[float]:
        """Update buffers and return wear fractions [0=new … 1=bald] for each tyre.

        Args:
            radii: Per-wheel geometric rolling radius in metres from GT7 UDP (4 values).
            speed_ms: Car absolute speed in m/s — used to gate sampling.
        """
        labels = ("FL", "FR", "RL", "RR")
        result: list[float] = []
        self._frame_counter += 1
        should_sample = (self._frame_counter % self._sample_every == 0)

        for i, rad in enumerate(radii):
            if should_sample and speed_ms >= _MIN_SPEED_MS and _VALID_RADIUS[0] <= rad <= _VALID_RADIUS[1]:
                r_baseline = self._r_baseline[i]

                # Detect tyre change: median jumped above locked baseline
                if r_baseline is not None:
                    current_med = statistics.median(self._buffers[i]) if self._buffers[i] else rad
                    if current_med > r_baseline + _NEW_TYRE_TOLERANCE:
                        log.info(
                            "wear[%s] tyre change detected — resetting (median %.4f > baseline %.4f)",
                            labels[i], current_med, r_baseline,
                        )
                        self._buffers[i].clear()
                        self._r_baseline[i] = None
                        r_baseline = None

                self._buffers[i].append(rad)

                if r_baseline is None and len(self._buffers[i]) == _BUFFER_SIZE:
                    self._r_baseline[i] = statistics.median(self._buffers[i])
                    log.info(
                        "wear[%s] baseline locked  r_baseline=%.4f m",
                        labels[i], self._r_baseline[i],
                    )

            r_baseline_val = self._r_baseline[i]
            if r_baseline_val is None or len(self._buffers[i]) < _BUFFER_SIZE:
                log.debug(
                    "wear[%s] warming up  buf=%d/%d  speed=%.1f m/s  radius=%.4f",
                    labels[i], len(self._buffers[i]), _BUFFER_SIZE, speed_ms, rad,
                )
                result.append(0.0)
                continue

            smoothed = statistics.median(self._buffers[i])
            wear = (r_baseline_val - smoothed) / self._wear_range_m
            wear_clamped = max(0.0, min(1.0, wear))
            log.debug(
                "wear[%s] baseline=%.4f  smoothed=%.4f  delta=%.3f mm  wear=%.1f%%",
                labels[i], r_baseline_val, smoothed,
                (r_baseline_val - smoothed) * 1000, wear_clamped * 100,
            )
            result.append(wear_clamped)

        return result
