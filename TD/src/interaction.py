"""Pure, replayable hand-to-fluid interaction; no TD or camera dependency."""
import math


def _distance(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))


def _point(landmark):
    return (float(landmark['x']), float(landmark['y']), float(landmark.get('z', 0)))


def _angle(a, b, c):
    ab = [a[i] - b[i] for i in range(3)]
    cb = [c[i] - b[i] for i in range(3)]
    length = math.sqrt(sum(x*x for x in ab) * sum(x*x for x in cb))
    if length < 1e-10:
        return 0
    cosine = max(-1, min(1, sum(x*y for x, y in zip(ab, cb)) / length))
    return math.degrees(math.acos(cosine))


def pointing_index(hand):
    """Rotation-independent index extension; thumb intentionally unrestricted."""
    try:
        points = [_point(p) for p in hand['landmarks']]
        if len(points) != 21 or not all(math.isfinite(v) for p in points for v in p):
            return False
        if float(hand.get('confidence', 1)) < 0.5:
            return False
        if _distance(points[0], points[9]) < 0.025:
            return False
        index = (_angle(points[5], points[6], points[7]) > 155
                 and _angle(points[6], points[7], points[8]) > 150
                 and _distance(points[8], points[0]) > _distance(points[6], points[0]) * 1.1)
        def folded(mcp, pip, dip, tip):
            return (_angle(points[mcp], points[pip], points[dip]) < 145
                    or _distance(points[tip], points[0]) < _distance(points[pip], points[0]) * 1.08)
        return index and all(folded(*f) for f in [(9,10,11,12), (13,14,15,16), (17,18,19,20)])
    except (TypeError, ValueError, KeyError, IndexError):
        return False


class Interaction:
    def __init__(self, activation_seconds=0.06, release_seconds=0.18,
                 stale_seconds=0.30, smoothing_seconds=0.035, deadband=0.0012,
                 max_speed=3.0):
        self.activation_seconds = activation_seconds
        self.release_seconds = release_seconds
        self.stale_seconds = stale_seconds
        self.smoothing_seconds = smoothing_seconds
        self.deadband = deadband
        self.max_speed = max_speed
        self.reset()

    def reset(self):
        self.last_seq = None
        self.label = None
        self.wrist = None
        self.valid_since = None
        self.invalid_since = None
        self.previous_time = None
        self.position = (0.5, 0.5)
        self.active = False
        self._baseline = False

    def _result(self, delta=(0.0, 0.0), velocity=(0.0, 0.0), reason='idle'):
        return dict(active=self.active, x=self.position[0], y=self.position[1],
                    dx=delta[0], dy=delta[1], vx=velocity[0], vy=velocity[1],
                    hand=self.label or '', reason=reason)

    def _invalid(self, now, reason):
        self.active = False
        self._baseline = False
        self.valid_since = None
        if self.invalid_since is None:
            self.invalid_since = now
        if now - self.invalid_since >= self.release_seconds:
            self.label = None
            self.wrist = None
        return self._result(reason=reason)

    def update(self, frame, now):
        if not frame or now - frame.get('received_at', -math.inf) > self.stale_seconds:
            return self._invalid(now, 'stale')
        if frame.get('seq') == self.last_seq:
            return self._result(reason='waiting')
        self.last_seq = frame.get('seq')
        hands = [h for h in frame.get('hands', []) if len(h.get('landmarks', [])) == 21]
        chosen = None
        if self.label is not None:
            same = [h for h in hands if h.get('label', 'Unknown') == self.label]
            if same:
                chosen = min(same, key=lambda h: _distance(_point(h['landmarks'][0]), self.wrist))
                if _distance(_point(chosen['landmarks'][0]), self.wrist) > 0.45:
                    chosen = None
        else:
            chosen = next((h for h in hands if pointing_index(h)), None)
            if chosen:
                self.label = chosen.get('label', 'Unknown')
                self.wrist = _point(chosen['landmarks'][0])
        if not chosen or not pointing_index(chosen):
            return self._invalid(now, 'gesture-inactive')
        self.wrist = _point(chosen['landmarks'][0])
        self.invalid_since = None
        if self.valid_since is None:
            self.valid_since = now
        if now - self.valid_since + 1e-9 < self.activation_seconds:
            return self._result(reason='activating')
        tip = chosen['landmarks'][8]
        position = (max(0, min(1, 1-float(tip['x']))), max(0, min(1, 1-float(tip['y']))))
        sample_time = frame['received_at'] - max(0, float(frame.get('inferenceMs', 0))) / 1000
        if not self._baseline:
            self.position = position
            self.previous_time = sample_time
            self._baseline = True
            self.active = True
            return self._result(reason='active')
        dt = max(0.001, min(self.stale_seconds, sample_time - self.previous_time))
        self.previous_time = sample_time
        alpha = 1.0 if self.smoothing_seconds <= 0 else 1-math.exp(-dt/self.smoothing_seconds)
        filtered = tuple(old + (new-old)*alpha for old, new in zip(self.position, position))
        delta = tuple(new-old for old, new in zip(self.position, filtered))
        self.position = filtered
        self.active = True
        length = _distance(delta, (0, 0))
        if length <= self.deadband:
            return self._result(reason='active')
        cap = self.max_speed * dt
        if length > cap:
            delta = tuple(v*cap/length for v in delta)
        return self._result(delta=delta, velocity=tuple(v/dt for v in delta), reason='active')
