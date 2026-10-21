"""Record only the painting after the real controller first activates."""
probe=op('/ink_probe') or op('/').create(baseCOMP,'ink_probe')
selected=probe.op('painting_source') or probe.create(selectTOP,'painting_source')
selected.par.top=op('/artofink/out')
fit=probe.op('recording_size') or probe.create(fitTOP,'recording_size')
fit.inputConnectors[0].connect(selected)
fit.par.outputresolution='custom';fit.par.resolutionw=1280;fit.par.resolutionh=648
fit.par.format='rgba8fixed'
capture=probe.op('capture') or probe.create(moviefileoutTOP,'capture')
capture.inputConnectors[0].connect(fit)
monitor=probe.op('gesture_recording')
if monitor:monitor.destroy()
monitor=probe.create(executeDAT,'gesture_recording')
monitor.text='''import time,json
from pathlib import Path
root=op('/artofink')
folder=Path(project.folder).parent/'docs/validation'
folder.mkdir(parents=True,exist_ok=True)
capture=op('/ink_probe/capture')
capture.par.file=(folder/'real-gesture-demo.mp4').as_posix()
capture.par.videocodec='mpeg4';capture.par.fps=60
waiting_since=time.perf_counter()
started=None
active_frames=0
inactive_frames=0
def onFrameEnd(frame):
    global started,active_frames,inactive_frames
    now=time.perf_counter()
    interaction=root.fetch('interaction_output',{})
    real=type(root.op('runtime').module._controller).__name__=='Interaction'
    if started is None:
        if real and interaction.get('active'):
            started=now;capture.par.record=True
        elif now-waiting_since>900:
            (folder/'real-gesture-recording.json').write_text(json.dumps(dict(recorded=False,reason='No real activation before timeout')),encoding='utf-8')
            me.par.active=False
        return
    active_frames+=bool(interaction.get('active'))
    inactive_frames+=not bool(interaction.get('active'))
    op('/ink_probe/painting_source').cook(force=True)
    op('/ink_probe/recording_size').cook(force=True)
    capture.cook(force=True)
    if now-started>=30:
        capture.par.record=False
        result=dict(recorded=True,seconds=now-started,active_frames=active_frames,
            inactive_frames=inactive_frames,real_controller=real,
            camera_state=root.fetch('camera_status',{}).get('state'))
        (folder/'real-gesture-recording.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        me.par.active=False
'''
monitor.par.frameend=True
print('Waiting for genuine hand activation; then recording 30 seconds of the painting only')
