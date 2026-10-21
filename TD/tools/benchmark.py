"""TD-only 5.5 minute benchmark; inference and audio remain enabled.

Uses a temporary 20 Hz trajectory controller and restores the real controller.
No camera images or landmarks are written. Keep Perform mode in the foreground.
"""
probe=op('/ink_probe') or op('/').create(baseCOMP,'ink_probe')
old=probe.op('benchmark')
if old:
    if old.par.active.eval():old.module.finish('Restarted benchmark')
    old.destroy()
monitor=probe.create(executeDAT,'benchmark')
monitor.text='''import time,math,json,statistics,traceback
from pathlib import Path
root=op('/artofink')
runtime=root.op('runtime').module
original=runtime._controller
original_mute=root.par.Mute.eval()
started=time.perf_counter()
previous=started
samples=[]
latencies=[]
inferences=[]
audio_checks=[]
next_check=0
audio_loops=0
previous_audio=0
mute_pass=False
last_report=0
stages=[('idle',60),('slow',60),('fast',60),('recovery',60),('mixed',90)]
def phase_at(elapsed):
    for name,duration in stages:
        if elapsed<duration:return name,elapsed
        elapsed-=duration
    return 'done',0
class Driver:
    smoothing_seconds=0
    def reset(self):self.position=(.5,.5);self.sample=-1;self.active=False
    def update(self,frame,now):
        mode,t=phase_at(max(0,now-started-5))
        active=mode in ('slow','fast','mixed') and now-started>=5
        slot=int((now-started)*root.par.Inferencefps.eval())
        delta=(0,0)
        if active and (slot!=self.sample or not self.active):
            speed=.35 if mode=='slow' or (mode=='mixed' and int(t/15)%2==0) else 1.2
            position=(.5+.25*math.sin(t*speed),.5+.15*math.cos(t*speed))
            if self.active:delta=tuple(a-b for a,b in zip(position,self.position))
            self.position=position
        self.sample=slot
        self.active=active
        return dict(active=active,x=self.position[0],y=self.position[1],dx=delta[0],dy=delta[1],
                    vx=delta[0]*20,vy=delta[1]*20,hand='',reason='benchmark-replay')
driver=Driver();driver.reset();runtime._controller=driver
root.op('music').par.cuepoint=0
root.op('music').par.cuepulse.pulse()
audio=op('/ink_probe/audio_info') or op('/ink_probe').create(infoCHOP,'audio_info')
audio.par.op=root.op('music')
def summary(values):
    if not values:return {}
    ordered=sorted(values)
    return dict(frames=len(values),seconds=sum(values),fps=len(values)/sum(values),
                p50_ms=statistics.median(values)*1000,
                p95_ms=ordered[int(len(values)*.95)]*1000,
                p99_ms=ordered[int(len(values)*.99)]*1000,
                over_20ms_fraction=sum(v>.020 for v in values)/len(values))
def report(error=None,finished=False):
    result=dict(finished=finished,error=error,seconds=time.perf_counter()-started,
        overall=summary([s[1] for s in samples]),
        stages={name:summary([s[1] for s in samples if s[0]==name]) for name,_ in stages},
        inference_mean_ms=statistics.mean(inferences) if inferences else None,
        inference_p95_ms=sorted(inferences)[int(len(inferences)*.95)] if inferences else None,
        latest_result_age_p95_ms=sorted(latencies)[int(len(latencies)*.95)] if latencies else None,
        audio_loops=audio_loops,mute_parameter_pass=mute_pass,audio_checks=audio_checks,
        settings={name:getattr(root.par,name).eval() for name in ('Gain','Gridwidth','Iterations','Inferencefps','Damping','Smoothing')},
        camera_state=root.fetch('camera_status',{}).get('state'),
        painting_format=str(root.op('advect_ink').pixelFormat),
        errors={n.path:n.errors() for n in root.children if n.errors()})
    folder=Path(project.folder).parent/'docs/validation'
    folder.mkdir(parents=True,exist_ok=True)
    temporary=folder/'benchmark.json.tmp'
    temporary.write_text(json.dumps(result,indent=2),encoding='utf-8')
    temporary.replace(folder/'benchmark.json')
def finish(error=None):
    runtime._controller=original
    original.reset()
    root.par.Mute=original_mute
    report(error,finished=True)
    me.par.active=False
def onFrameEnd(frame):
    global previous,next_check,audio_loops,previous_audio,mute_pass,last_report
    try:
        now=time.perf_counter();elapsed=now-started
        interval=now-previous;previous=now
        if elapsed<2:
            root.par.Mute=True
            mute_pass=root.op('speakers').par.volume.eval()==0
        elif elapsed<5:root.par.Mute=original_mute
        mode,_=phase_at(max(0,elapsed-5))
        if mode=='done':finish();return
        if elapsed>=5:samples.append((mode,interval))
        if elapsed>=next_check:
            next_check=elapsed+1
            audio.cook(force=True)
            fraction=float(audio['fraction'][0])
            if previous_audio-fraction>.5:audio_loops+=1
            previous_audio=fraction
            audio_checks.append(dict(second=round(elapsed,1),fraction=round(fraction,5),open=float(audio['open'][0])))
            latest=root.fetch('latest_frame',{}) or {}
            inferences.append(latest.get('inferenceMs',0))
            if latest.get('received_at'):latencies.append(max(0,(now-latest['received_at'])*1000))
        if elapsed-last_report>30:last_report=elapsed;report()
    except Exception:finish(traceback.format_exc())
'''
monitor.par.frameend=True
print('Benchmark live: 5 second warmup + 330 seconds idle/slow/fast/recovery/mixed; camera and audio stay on')
