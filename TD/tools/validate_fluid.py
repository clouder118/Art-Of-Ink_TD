"""TD integration test and landscape-only recording; restores real input on exit.

Injects a temporary controller at the real runtime boundary. Camera inference
stays running; the test requires /ink_probe/capture (Movie File Out TOP).
"""
root=op('/artofink')
probe=op('/ink_probe') or op('/').create(baseCOMP,'ink_probe')
capture=probe.op('capture') or probe.create(moviefileoutTOP,'capture')
selected=probe.op('painting_source') or probe.create(selectTOP,'painting_source')
selected.par.top=root.op('out')
recording=probe.op('recording_size') or probe.create(fitTOP,'recording_size')
recording.inputConnectors[0].connect(selected)
recording.par.outputresolution='custom'
recording.par.resolutionw=1280;recording.par.resolutionh=648
recording.par.format='rgba8fixed'
capture.inputConnectors[0].connect(recording)
monitor=probe.op('flow_validation') or probe.create(executeDAT,'flow_validation')
monitor.par.active=False
monitor.text='''import time,json,traceback
from pathlib import Path
import numpy as np
root=op('/artofink')
runtime=root.op('runtime').module
original_controller=runtime._controller
folder=Path(project.folder).parent/'docs/validation'
folder.mkdir(parents=True,exist_ok=True)
segments=[('baseline',.6),('slow',4),('restore_slow',8),('fast',1),('restore_fast',8)]
phase=0
started=time.perf_counter()
baseline=None
results=[]
class Driver:
    smoothing_seconds=0
    def reset(self): self.previous=None
    def update(self,frame,now):
        mode,duration=segments[phase]
        moving=mode in ('slow','fast')
        u=min(1,max(0,(now-started)/duration)) if moving else 0
        position=(.25+.5*u,.5)
        delta=0 if not moving or self.previous is None else position[0]-self.previous[0]
        self.previous=position
        return dict(active=moving,x=position[0],y=position[1],dx=delta,dy=0,
                    vx=delta*60,vy=0,hand='',reason='validation-replay')
driver=Driver();driver.reset()
runtime._controller=driver
runtime.reset()
capture=op('/ink_probe/capture')
capture.par.file=(folder/'flow-comparison.mp4').as_posix()
capture.par.videocodec='mpeg4'
capture.par.outputresolution='custom'
capture.par.resolutionw=1280;capture.par.resolutionh=648
capture.par.fps=60
capture.par.record=True
def finish(error=None):
    capture.par.record=False
    runtime._controller=original_controller
    original_controller.reset()
    result={'segments':results,'camera':root.fetch('camera_status',{}).get('state'),'error':error}
    if not error:
        by_name={r['phase']:r for r in results}
        result['pass']=(all(r['finite'] for r in results)
            and by_name['slow']['changed_fraction']>.001
            and by_name['fast']['max_velocity']>by_name['slow']['max_velocity']*1.2
            and by_name['restore_slow']['mean_difference']<by_name['slow']['mean_difference']*.1
            and by_name['restore_fast']['mean_difference']<by_name['fast']['mean_difference']*.1)
    (folder/'flow-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    me.par.active=False
def onFrameEnd(frame):
    global phase,started,baseline
    try:
        now=time.perf_counter()
        op('/ink_probe/painting_source').cook(force=True)
        op('/ink_probe/recording_size').cook(force=True)
        capture.cook(force=True)
        if now-started<segments[phase][1]:return
        image=root.op('out').numpyArray(delayed=False).copy()
        velocity=root.op('project_velocity').numpyArray(delayed=False)
        if baseline is None:baseline=image
        difference=np.abs(image[:,:,:3]-baseline[:,:,:3])
        mode=segments[phase][0]
        results.append(dict(phase=mode,mean_difference=float(difference.mean()),
            changed_fraction=float((difference.max(axis=2)>.005).mean()),
            max_velocity=float(np.abs(velocity[:,:,:2]).max()),
            finite=bool(np.isfinite(image).all() and np.isfinite(velocity).all()),
            impulse=float(abs(root.fetch('interaction_output',{}).get('dx',0)))))
        root.op('out').save(str(folder/(mode+'.png')))
        phase+=1
        if phase==len(segments):finish();return
        if segments[phase][0] in ('slow','fast'):runtime.reset()
        driver.reset();started=now
    except Exception:finish(traceback.format_exc())
'''
monitor.par.frameend=True
monitor.par.active=True
print('Running slow / recovery / fast / recovery validation (about 22 seconds)')
