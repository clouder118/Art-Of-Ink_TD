"""Pure, replayable hand-to-fluid interaction; no TD or camera dependency."""
import math
from collections import deque


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


def open_palm(hand):
    """Five extended, spread fingers; distances/angles tolerate hand rotation."""
    try:
        points = [_point(p) for p in hand['landmarks']]
        if len(points) != 21 or not all(math.isfinite(v) for p in points for v in p):
            return False
        palm = _distance(points[0], points[9])
        if float(hand.get('confidence', 1)) < .5 or palm < .025:
            return False
        for mcp, pip, dip, tip in [(5,6,7,8),(9,10,11,12),(13,14,15,16),(17,18,19,20)]:
            if (_angle(points[mcp],points[pip],points[dip]) < 150
                    or _angle(points[pip],points[dip],points[tip]) < 150
                    or _distance(points[tip],points[0]) < 1.12*_distance(points[pip],points[0])):
                return False
        thumb = (_angle(points[2],points[3],points[4]) > 145
                 and _distance(points[4],points[5]) > .65*palm
                 and _distance(points[4],points[0]) > 1.1*_distance(points[2],points[0]))
        spread = (_distance(points[8],points[20]) > 1.1*_distance(points[5],points[17])
                  and all(_distance(points[a],points[b]) > .22*palm for a,b in [(8,12),(12,16),(16,20)]))
        return thumb and spread
    except (TypeError, ValueError, KeyError, IndexError):
        return False


def gesture_kind(hand):
    if pointing_index(hand):
        return 'index'
    return 'palm' if open_palm(hand) else 'none'


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
        self.gesture = 'none'
        self._baseline = False

    def _result(self, delta=(0.0, 0.0), velocity=(0.0, 0.0), reason='idle'):
        return dict(active=self.active, x=self.position[0], y=self.position[1],
                    dx=delta[0], dy=delta[1], vx=velocity[0], vy=velocity[1],
                    hand=self.label or '', reason=reason, gesture=self.gesture)

    def _invalid(self, now, reason):
        self.active = False
        self.gesture = 'none'
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
            chosen = next((h for h in hands if gesture_kind(h) != 'none'), None)
            if chosen:
                self.label = chosen.get('label', 'Unknown')
                self.wrist = _point(chosen['landmarks'][0])
        kind = gesture_kind(chosen) if chosen else 'none'
        if kind == 'none':
            return self._invalid(now, 'gesture-inactive')
        if kind != self.gesture:
            self.valid_since = None
            self._baseline = False
            self.active = False
        self.gesture = kind
        self.wrist = _point(chosen['landmarks'][0])
        self.invalid_since = None
        if kind == 'palm':
            return self._result(reason='palm')
        if self.valid_since is None:
            self.valid_since = now
        if now - self.valid_since + 1e-9 < self.activation_seconds:
            return self._result(reason='activating')
        tip = chosen['landmarks'][8]
        position = (max(0, min(1, 1-float(tip['x']))), max(0, min(1, 1-float(tip['y']))))
        captured = frame.get('captureMs')
        # Browser and TD clocks have different origins; only differences within
        # the capture clock are used. Receipt time still governs stale input.
        sample_time = (captured/1000 if isinstance(captured,(int,float)) and math.isfinite(captured)
                       else frame['received_at'] - max(0, float(frame.get('inferenceMs', 0))) / 1000)
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
        self.active = True
        length = _distance(delta, (0, 0))
        if length <= self.deadband:
            return self._result(reason='active')
        cap = self.max_speed * dt
        if length > cap:
            delta = tuple(v*cap/length for v in delta)
        # The cursor and its displacement must follow the same limited path.
        # Otherwise the resampler starts a segment at a different location and
        # a single noisy detection can teleport the fluid's injection point.
        self.position = tuple(old+step for old,step in zip(self.position,delta))
        return self._result(delta=delta, velocity=tuple(v/dt for v in delta), reason='active')


class PalmEffects:
    """Global edge-triggered cycle, independent of which hand owns control.

    The envelope represents residual transport after release, not new forcing.
    Counts advance only when a newly confirmed palm episode actually starts.
    """
    names = ('none', 'wave', 'spiral', 'ripple')

    def __init__(self):
        self.reset()

    def reset(self, block_until_release=False):
        self.next_effect = 1
        self.effect = 0
        self.phase = 0.0
        self.strength = 0.0
        self.episode = False
        self.blocked = block_until_release
        self.hand = None
        self.palm_since = None
        self.samples = 0
        self.release_since = None
        self.last_seq = None
        self.previous_time = None

    def tracking_reset(self):
        # A camera reconnect ends the episode but preserves the global cycle.
        self.episode = False
        # Reconnecting is not evidence that a reset-held palm was released.
        self.palm_since = None
        self.samples = 0
        self.release_since = None
        self.last_seq = None

    def update(self, observation, frame, now):
        dt = 0 if self.previous_time is None else max(0,min(.1,now-self.previous_time))
        self.previous_time = now
        fresh = bool(frame) and frame.get('seq') != self.last_seq
        if fresh:
            self.last_seq = frame.get('seq')
        if self.release_since is not None and now-self.release_since >= .25-1e-9:
            self.episode = False
            self.blocked = False
        stale = not frame or now-frame.get('received_at',-math.inf) > .30
        palm = not stale and observation.get('gesture') == 'palm'
        if stale:
            self.tracking_reset()
        elif not palm:
            self.palm_since = None
            self.samples = 0
            if self.release_since is None:
                self.release_since = now
            if now-self.release_since >= .25-1e-9:
                self.episode = False
                self.blocked = False
        else:
            # A confirmed takeover cannot continue the previous hand's episode.
            if self.episode and observation['hand'] != self.hand:
                self.episode = False
                self.palm_since = None
                self.samples = 0
            self.release_since = None
            if not self.episode and not self.blocked and fresh:
                if self.palm_since is None:
                    self.palm_since = now
                self.samples += 1
                if self.samples >= 3 and now-self.palm_since >= .20-1e-9:
                    self.effect = self.next_effect
                    self.next_effect = self.effect % 3 + 1
                    self.episode = True
                    self.hand = observation['hand']
                    self.phase = 0.0
                    self.strength = 0.0
        active = palm and self.episode and not self.blocked
        target = 1.0 if active else 0.0
        tau = .25/3 if active else .45
        self.strength = target+(self.strength-target)*math.exp(-dt/tau)
        if self.strength < .0001:
            self.strength = 0.0
        if self.strength > 0:
            self.phase += dt
        return dict(gesture=observation.get('gesture','none'), effect=self.names[self.effect],
                    effect_id=self.effect, next_effect=self.names[self.next_effect],
                    effect_time=self.phase, effect_strength=self.strength, palm_active=active)


class MotionResampler:
    """Spend each observed displacement once, across the intervening render frames.

    Only confirmed movement is interpolated: no velocity extrapolation. Gesture
    loss, reset or hand takeover immediately discards unfinished movement.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.segments=deque()
        self.hand=None
        self.previous_time=None
        self.position=(.5,.5)

    def update(self, observation, now):
        result=dict(observation,dx=0.0,dy=0.0,vx=0.0,vy=0.0)
        if not observation['active']:
            self.reset()
            return result
        if self.hand!=observation['hand'] or self.previous_time is None:
            self.reset()
            self.hand=observation['hand']
            self.previous_time=now
            self.position=(observation['x'],observation['y'])
            return result
        elapsed=max(0,now-self.previous_time)
        self.previous_time=now
        # Interaction already turns repeated camera results into zero delta.
        delta=(observation['dx'],observation['dy'])
        distance=math.hypot(*delta)
        speed=math.hypot(observation['vx'],observation['vy'])
        if distance>0:
            interval=distance/speed if speed>1e-9 else 1/20
            duration=max(1/120,min(.1,interval))
            start=(observation['x']-delta[0],observation['y']-delta[1])
            self.segments.append([start,delta,duration,0.0])
        budget=min(elapsed,.1)
        emitted=[0.0,0.0]
        while self.segments and budget>1e-9:
            start,delta,duration,used=self.segments[0]
            step=min(budget,duration-used)
            fraction=step/duration
            for axis in range(2):emitted[axis]+=delta[axis]*fraction
            used+=step;budget-=step
            self.position=tuple(start[i]+delta[i]*min(1,used/duration) for i in range(2))
            if used>=duration-1e-9:self.segments.popleft()
            else:self.segments[0][3]=used
        result.update(x=self.position[0],y=self.position[1],dx=emitted[0],dy=emitted[1],
                      vx=emitted[0]/max(elapsed,1e-6),vy=emitted[1]/max(elapsed,1e-6))
        return result
