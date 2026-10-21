"""Replay the real controller at camera and render clocks independently."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'TD/src'))
from interaction import Interaction, MotionResampler
from test_interaction import hand, frame


def replay(camera_fps=20, render_fps=60):
    controller=Interaction(activation_seconds=0,smoothing_seconds=0)
    motion=MotionResampler()
    next_sample=0;seq=0;latest=None;rows=[]
    for tick in range(round(2.3*render_fps)+1):
        now=tick/render_fps
        if now+1e-9>=next_sample and next_sample<=2+1e-9:
            offset=-.1*min(next_sample,1.5)
            latest=frame(seq,next_sample,[hand(offset=offset)])
            seq+=1;next_sample+=1/camera_fps
        sample=controller.update(latest,now)
        out=motion.update(sample,now)
        rows.append((now,sample,out))
    return rows


class MotionResamplingTests(unittest.TestCase):
    def test_20fps_motion_is_continuous_at_60fps_without_more_total_force(self):
        rows=replay()
        steady=[out['dx'] for now,_,out in rows if .3<now<1.3]
        self.assertTrue(all(delta>0 for delta in steady))
        self.assertLess(max(steady)/(sum(steady)/len(steady)),1.15)
        self.assertAlmostEqual(sum(sample['dx'] for _,sample,_ in rows),
                               sum(out['dx'] for _,_,out in rows),places=8)

    def test_force_is_conserved_across_render_rates_and_stationary_tail_ends(self):
        for hz in (30,60,144):
            with self.subTest(render_fps=hz):
                rows=replay(20,hz)
                self.assertAlmostEqual(sum(out['dx'] for _,_,out in rows),.15,places=6)
                self.assertTrue(all(out['dx']==0 for now,_,out in rows if now>1.7))

    def test_non_divisible_camera_clock_has_no_regular_zero_force_gaps(self):
        steady=[out['dx'] for now,_,out in replay(27,60) if .3<now<1.3]
        self.assertLess(sum(d==0 for d in steady)/len(steady),.1)

    def test_large_detection_jump_cannot_teleport_resampled_injection(self):
        controller=Interaction(activation_seconds=0,smoothing_seconds=0)
        motion=MotionResampler()
        first=frame(0,0,[hand()])
        previous=motion.update(controller.update(first,0),0)
        previous=motion.update(controller.update(first,1/30),1/30)
        jumped=frame(1,.05,[hand(offset=-.3)])
        for now in (.05,1/15,1/12):
            current=motion.update(controller.update(jumped,now),now)
            self.assertAlmostEqual(current['x']-previous['x'],current['dx'])
            self.assertLessEqual(abs(current['vx']),3.00001)
            previous=current

    def test_invalid_gesture_discards_remaining_force_and_reentry_is_zero(self):
        motion=MotionResampler()
        base=dict(active=True,hand='Left',x=.4,y=.5,dx=0,dy=0,vx=0,vy=0)
        motion.update(base,0)
        motion.update(base,.033)
        moving=dict(base,x=.5,dx=.1,vx=2)
        first=motion.update(moving,.05)['dx']
        self.assertGreater(first,0)
        self.assertLess(first,.1)
        invalid=dict(base,active=False)
        self.assertEqual(motion.update(invalid,.06)['dx'],0)
        self.assertEqual(motion.update(dict(base,x=.9),.07)['dx'],0)

    def test_hand_switch_and_reset_cannot_emit_pending_old_hand_motion(self):
        motion=MotionResampler()
        base=dict(active=True,hand='Left',x=.4,y=.5,dx=0,dy=0,vx=0,vy=0)
        motion.update(base,0)
        motion.update(base,.033)
        motion.update(dict(base,x=.5,dx=.1,vx=2),.05)
        switched=motion.update(dict(base,hand='Right',x=.9),.06)
        self.assertEqual((switched['dx'],switched['dy']),(0,0))
        motion.reset()
        self.assertEqual(motion.update(base,.07)['dx'],0)


if __name__=='__main__':
    unittest.main()
