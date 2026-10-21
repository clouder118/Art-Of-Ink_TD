import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'TD/src'))
from interaction import Interaction, pointing_index


def hand(label='Left', offset=0):
    xy = [(0.5,.85),(.4,.77),(.33,.68),(.28,.62),(.22,.57),
          (.43,.63),(.43,.46),(.43,.33),(.43,.2),
          (.50,.61),(.51,.50),(.54,.61),(.52,.70),
          (.57,.63),(.59,.54),(.61,.64),(.59,.73),
          (.64,.68),(.66,.60),(.68,.70),(.65,.77)]
    return dict(label=label,confidence=.99,landmarks=[dict(x=x+offset,y=y,z=0) for x,y in xy])


def frame(seq, time, hands):
    return dict(seq=seq,received_at=time,inferenceMs=0,hands=hands)


class GestureTests(unittest.TestCase):
    def test_natural_index_and_free_thumb(self):
        h=hand()
        self.assertTrue(pointing_index(h))
        h['landmarks'][4] = dict(x=.5,y=.8,z=0)
        self.assertTrue(pointing_index(h))

    def test_rotation_preserves_gesture(self):
        h=hand()
        for p in h['landmarks']:
            x,y=p['x']-.5,p['y']-.5
            p.update(x=.5+x*math.cos(.6)-y*math.sin(.6),y=.5+x*math.sin(.6)+y*math.cos(.6))
        self.assertTrue(pointing_index(h))

    def test_second_extended_finger_rejected(self):
        h=hand()
        for i,y in [(10,.44),(11,.30),(12,.17)]:
            h['landmarks'][i]=dict(x=.5,y=y,z=0)
        self.assertFalse(pointing_index(h))

    def test_invalid_points_rejected(self):
        h=hand(); h['landmarks'][8]['x']=float('nan')
        self.assertFalse(pointing_index(h))

    def test_open_palm_rejected(self):
        h=hand()
        for mcp,pip,dip,tip in [(9,10,11,12),(13,14,15,16),(17,18,19,20)]:
            x=h['landmarks'][mcp]['x']
            for i,y in [(pip,.45),(dip,.32),(tip,.18)]:
                h['landmarks'][i]=dict(x=x,y=y,z=0)
        self.assertFalse(pointing_index(h))

    def test_fist_and_low_confidence_rejected(self):
        h=hand()
        h['landmarks'][7]=dict(x=.47,y=.62,z=0)
        h['landmarks'][8]=dict(x=.45,y=.72,z=0)
        self.assertFalse(pointing_index(h))
        h=hand();h['confidence']=.2
        self.assertFalse(pointing_index(h))


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.c=Interaction(activation_seconds=0, smoothing_seconds=0)

    def test_first_sample_has_no_impulse_then_mirror_and_up(self):
        a=self.c.update(frame(1,1,[hand()]),1)
        self.assertEqual((a['dx'],a['dy']),(0,0))
        moved=hand(offset=-.05); moved['landmarks'][8]['y']-=.02
        b=self.c.update(frame(2,1.1,[moved]),1.1)
        self.assertGreater(b['dx'],0); self.assertGreater(b['dy'],0)

    def test_same_frame_is_not_consumed_twice(self):
        self.c.update(frame(1,1,[hand()]),1)
        f=frame(2,1.1,[hand(offset=.03)])
        self.assertNotEqual(self.c.update(f,1.1)['dx'],0)
        self.assertEqual(self.c.update(f,1.12)['dx'],0)

    def test_still_hand_has_zero_impulse(self):
        self.c.update(frame(1,1,[hand()]),1)
        r=self.c.update(frame(2,1.1,[hand()]),1.1)
        self.assertEqual((r['dx'],r['dy']),(0,0))

    def test_dropout_stops_and_return_resets_baseline(self):
        self.c.update(frame(1,1,[hand()]),1)
        self.assertFalse(self.c.update(None,1.1)['active'])
        r=self.c.update(frame(2,1.2,[hand(offset=.2)]),1.2)
        self.assertTrue(r['active']); self.assertEqual(r['dx'],0)

    def test_stale_data_stops_force(self):
        f=frame(1,1,[hand()]); self.c.update(f,1)
        self.assertFalse(self.c.update(f,1.31)['active'])

    def test_other_hand_and_reordering_do_not_steal(self):
        self.c.update(frame(1,1,[hand()]),1)
        r=self.c.update(frame(2,1.1,[hand('Right',.2),hand('Left',.02)]),1.1)
        self.assertEqual(r['hand'],'Left')
        self.assertAlmostEqual(r['dx'],-.02)

    def test_takeover_only_after_release_and_without_cross_screen_impulse(self):
        self.c.update(frame(1,1,[hand()]),1)
        right=hand('Right',.25)
        self.assertFalse(self.c.update(frame(2,1.1,[right]),1.1)['active'])
        self.c.update(frame(3,1.3,[right]),1.3)
        r=self.c.update(frame(4,1.34,[right]),1.34)
        self.assertEqual(r['hand'],'Right'); self.assertTrue(r['active']); self.assertEqual(r['dx'],0)

    def test_activation_delay_and_velocity_limit(self):
        c=Interaction(activation_seconds=.06,smoothing_seconds=0)
        self.assertFalse(c.update(frame(1,1,[hand()]),1)['active'])
        self.assertTrue(c.update(frame(2,1.07,[hand()]),1.07)['active'])
        r=c.update(frame(3,1.08,[hand(offset=.3)]),1.08)
        self.assertLessEqual(abs(r['vx']),3.00001)

    def test_capture_clock_prevents_transport_jitter_from_changing_speed(self):
        velocities=[]
        for i in range(12):
            captured=10+i*.05
            received=captured+(.01 if i%2==0 else .035)
            f=frame(i,received,[hand(offset=-i*.01)])
            f.update(captureMs=captured*1000,inferenceMs=10)
            out=self.c.update(f,received)
            if i:velocities.append(out['vx'])
        for speed in velocities:self.assertAlmostEqual(speed,.2,places=8)

    def test_speed_limit_keeps_position_and_emitted_delta_consistent(self):
        previous=self.c.update(frame(1,1,[hand()]),1)
        for seq,offset in [(2,-.3),(3,0),(4,-.3)]:
            now=1+(seq-1)*.01
            current=self.c.update(frame(seq,now,[hand(offset=offset)]),now)
            self.assertAlmostEqual(current['x']-previous['x'],current['dx'])
            self.assertLessEqual(math.hypot(current['dx'],current['dy']),.030001)
            previous=current


if __name__=='__main__':
    unittest.main()
