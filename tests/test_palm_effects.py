import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'TD/src'))
from interaction import Interaction, MotionResampler, PalmEffects, open_palm, gesture_kind
from test_interaction import hand, frame


def palm(label='Left', offset=0):
    h=hand(label,offset)
    for mcp,pip,dip,tip,dx,dy in [(5,6,7,8,-.01,-.13),(9,10,11,12,0,-.14),
                                  (13,14,15,16,.025,-.12),(17,18,19,20,.05,-.10)]:
        base=h['landmarks'][mcp]
        for i,multiple in [(pip,1),(dip,1.7),(tip,2.3)]:
            h['landmarks'][i]=dict(x=base['x']+dx*multiple,y=base['y']+dy*multiple,z=0)
    return h


class PalmGestureTests(unittest.TestCase):
    def test_open_palm_rotates_and_mirrors(self):
        for angle,mirror in [(0,1),(.8,1),(-.6,-1)]:
            h=palm()
            for p in h['landmarks']:
                x,y=(p['x']-.5)*mirror,p['y']-.5
                p.update(x=.5+x*math.cos(angle)-y*math.sin(angle),
                         y=.5+x*math.sin(angle)+y*math.cos(angle))
            self.assertTrue(open_palm(h))
            self.assertEqual(gesture_kind(h),'palm')

    def test_index_fist_partial_and_bad_data_are_not_palm(self):
        self.assertFalse(open_palm(hand()))
        fist=hand()
        fist['landmarks'][8]=dict(x=.43,y=.73,z=0)
        self.assertEqual(gesture_kind(fist),'none')
        for change in ('thumb','middle','confidence','nan','missing'):
            h=palm()
            if change=='thumb':h['landmarks'][4]=dict(x=.5,y=.75,z=0)
            if change=='middle':h['landmarks'][12]=dict(x=.5,y=.7,z=0)
            if change=='confidence':h['confidence']=.2
            if change=='nan':h['landmarks'][0]['x']=float('nan')
            if change=='missing':h['landmarks'].pop()
            self.assertFalse(open_palm(h),change)

    def test_owner_survives_index_to_palm_and_back_without_impulse(self):
        c=Interaction(activation_seconds=0,smoothing_seconds=0)
        c.update(frame(0,0,[hand()]),0)
        out=c.update(frame(1,.05,[palm('Right',.1),palm()]),.05)
        self.assertEqual((out['hand'],out['gesture'],out['active']),('Left','palm',False))
        out=c.update(frame(2,.1,[hand(offset=.1)]),.1)
        self.assertEqual(out['gesture'],'index')
        self.assertEqual(out['dx'],0)


class PalmCycleTests(unittest.TestCase):
    def setUp(self):
        self.c=Interaction(activation_seconds=0)
        self.m=MotionResampler()
        self.p=PalmEffects()
        self.seq=0
        self.now=-.05
        self.latest=None

    def tick(self,hands=None,advance=.05,new=True):
        self.now+=advance
        if new:
            self.latest=frame(self.seq,self.now,hands or [])
            self.seq+=1
        obs=self.m.update(self.c.update(self.latest,self.now),self.now)
        out=dict(obs,**self.p.update(obs,self.latest,self.now))
        return out

    def hold(self,hands,seconds):
        return [self.tick(hands) for _ in range(round(seconds/.05))]

    def test_six_distinct_episodes_cycle_and_hold_never_advances(self):
        modes=[]
        for _ in range(6):
            held=self.hold([palm()],1)
            modes.append(held[-1]['effect'])
            self.assertEqual(len(set(x['effect'] for x in held if x['palm_active'])),1)
            self.assertGreater(held[-1]['effect_strength'],.99)
            self.hold([], .4)
        self.assertEqual(modes,['wave','spiral','ripple']*2)

    def test_activation_requires_time_and_fresh_samples(self):
        first=self.tick([palm()])
        self.assertFalse(first['palm_active'])
        for _ in range(12):
            self.assertFalse(self.tick(new=False,advance=1/60)['palm_active'])
        self.assertEqual(self.p.next_effect,1)

    def test_short_loss_resumes_same_episode_long_loss_advances(self):
        self.hold([palm()],.5)
        released=self.tick([])
        self.assertFalse(released['palm_active'])
        resumed=self.tick([palm()])
        self.assertTrue(resumed['palm_active'])
        self.assertEqual(resumed['effect'],'wave')
        self.hold([],.4)
        self.assertEqual(self.hold([palm()],.5)[-1]['effect'],'spiral')

    def test_stale_input_stops_and_releases_then_next_episode(self):
        self.hold([palm()],.5)
        for _ in range(25):out=self.tick(new=False,advance=1/60)
        self.assertFalse(out['palm_active'])
        self.assertEqual(self.hold([palm()],.5)[-1]['effect'],'spiral')

    def test_hand_takeover_and_camera_restart_preserve_cycle(self):
        self.hold([palm()],.5)
        self.hold([],.5)
        out=self.hold([palm('Right')],.6)[-1]
        self.assertEqual((out['hand'],out['effect']),('Right','spiral'))
        self.p.tracking_reset();self.c.reset()
        self.assertEqual(self.hold([palm('Right')],.5)[-1]['effect'],'ripple')

    def test_reset_while_open_requires_release_and_returns_to_wave(self):
        self.hold([palm()],.5)
        self.p.reset(block_until_release=True)
        self.assertFalse(self.hold([palm()],.6)[-1]['palm_active'])
        self.hold([],.4)
        self.assertEqual(self.hold([palm()],.5)[-1]['effect'],'wave')

    def test_fist_adds_no_new_effect_and_residual_dies_away(self):
        self.hold([palm()],.5)
        fist=hand();fist['landmarks'][8]=dict(x=.43,y=.73,z=0)
        rows=self.hold([fist],5)
        self.assertTrue(all(not x['palm_active'] and x['dx']==0 and x['dy']==0 for x in rows))
        self.assertEqual(rows[-1]['effect_strength'],0)
        self.assertEqual(rows[-1]['next_effect'],'spiral')

    def test_camera_restart_cannot_bypass_reset_release_requirement(self):
        self.hold([palm()],.5)
        self.p.reset(block_until_release=True)
        self.p.tracking_reset();self.c.reset()
        self.assertFalse(self.hold([palm()],.6)[-1]['palm_active'])
        self.hold([],.4)
        self.assertEqual(self.hold([palm()],.5)[-1]['effect'],'wave')


if __name__=='__main__':unittest.main()
