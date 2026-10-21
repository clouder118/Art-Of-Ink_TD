"""Five-minute measurement of the real camera-controlled presentation.

Never replaces the controller or injects input. A 10-second settling interval
is excluded. Keep the Perform window in front for a presentation measurement.
"""
probe=op('/ink_probe') or op('/').create(baseCOMP,'ink_probe')
old=probe.op('real_performance')
if old:old.destroy()
monitor=probe.create(executeDAT,'real_performance')
monitor.text='''import time,json,statistics
from pathlib import Path
root=op('/artofink')
started=time.perf_counter()
previous=started
intervals=[]
inferences=[]
active_frames=0
camera_frames=0
last_seq=None
next_report=30
def report(finished=False):
    ordered=sorted(intervals)
    result=dict(finished=finished,measured_seconds=sum(intervals),frames=len(intervals),
        fps=len(intervals)/sum(intervals) if intervals else 0,
        p50_ms=statistics.median(intervals)*1000 if intervals else 0,
        p95_ms=ordered[int(len(ordered)*.95)]*1000 if ordered else 0,
        p99_ms=ordered[int(len(ordered)*.99)]*1000 if ordered else 0,
        over_20ms_fraction=sum(v>.020 for v in intervals)/len(intervals) if intervals else 0,
        active_frames=active_frames,camera_frames=camera_frames,
        inference_mean_ms=statistics.mean(inferences) if inferences else None,
        inference_p95_ms=sorted(inferences)[int(len(inferences)*.95)] if inferences else None,
        camera_state=root.fetch('camera_status',{}).get('state'),
        real_controller=type(root.op('runtime').module._controller).__name__=='Interaction',
        errors={n.path:n.errors() for n in root.children if n.errors()})
    folder=Path(project.folder).parent/'docs/validation'
    temporary=folder/'real-performance.json.tmp'
    temporary.write_text(json.dumps(result,indent=2),encoding='utf-8')
    temporary.replace(folder/'real-performance.json')
def onFrameEnd(frame):
    global previous,active_frames,camera_frames,last_seq,next_report
    now=time.perf_counter();elapsed=now-started
    interval=now-previous;previous=now
    if elapsed<10:return
    intervals.append(interval)
    active_frames+=bool(root.fetch('interaction_output',{}).get('active'))
    latest=root.fetch('latest_frame',{}) or {}
    if latest.get('seq')!=last_seq:
        last_seq=latest.get('seq');camera_frames+=1
        inferences.append(latest.get('inferenceMs',0))
    if elapsed>=310:report(True);me.par.active=False
    elif elapsed>=next_report:report();next_report+=30
'''
monitor.par.frameend=True
print('Measuring genuine camera input for 300 seconds after 10-second settling; no simulated input')
