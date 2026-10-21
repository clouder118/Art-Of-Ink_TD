"""TD application lifecycle and the thin adapter around the pure controller."""
import importlib.util
import json
from pathlib import Path
import time
from collections import deque

_controller = None
_last_time = None
_session = None
_reset_frames = 0
_metrics = deque(maxlen=600)
_report_at = 0


def start():
    global _controller, _last_time, _session, _reset_frames, _report_at
    root = me.parent()
    folder = Path(project.folder)
    stop()
    required=['src/interaction.py','assets/ink_painting3.png','assets/龚一 - 山居吟.mp3',
              'web/index.html','web/hand_tracking.js','web/hand_worker.js','web/vendor/vision_bundle.mjs',
              'web/models/hand_landmarker.task','web/vendor/wasm/vision_wasm_internal.js',
              'web/vendor/wasm/vision_wasm_internal.wasm']
    missing=[name for name in required if not (folder/name).is_file()]
    try:
        if missing:
            raise FileNotFoundError('缺失工程资源：'+', '.join(missing))
        spec = importlib.util.spec_from_file_location('ink_interaction', folder / 'src/interaction.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except (OSError, ImportError, SyntaxError) as error:
        status={'state':'error','message':str(error)}
        root.store('camera_status',status)
        root.op('status_text').par.text='Art of Ink · STARTUP ERROR\n\n'+str(error)
        _publish(dict(camera=status,input={'active':False},errors={'startup':str(error)}))
        root.op('output_window').par.performance.pulse()
        return
    _controller = module.Interaction()
    _last_time = time.perf_counter()
    _session = None
    _reset_frames = 4
    _report_at = 0
    _metrics.clear()
    for key in ['latest_frame', 'tracking_session', 'camera_devices', 'interaction_output', 'replay_start']:
        root.unstore(key)
    root.store('camera_status', {'state':'loading','message':'正在加载本地手部识别'})
    root.op('local_server').par.active = True
    root.op('hand_camera').par.active = True
    root.op('music').par.cuepulse.pulse()
    root.op('output_window').par.performance.pulse()
    root.par.Preview=True


def reset():
    global _reset_frames
    _reset_frames = 4
    if _controller:
        _controller.reset()


def fullscreen():
    window = me.parent().op('output_window')
    full = window.par.size.eval() != 'fill'
    window.par.size = 'fill' if full else 'custom'
    window.par.borders = not full
    window.par.update.pulse()


def _vector(node, index, values):
    for axis, value in zip('xyzw', values):
        getattr(node.par, 'vec%dvalue%s' % (index, axis)).val = value


def _publish(report):
    try:
        report_dir=Path(project.folder)/'.runtime'
        report_dir.mkdir(exist_ok=True)
        temporary=report_dir/'status.json.tmp'
        temporary.write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8')
        temporary.replace(report_dir/'status.json')
    except OSError:
        # Diagnostics must not interrupt the artwork, including a read-only copy.
        pass


def tick():
    global _last_time, _session, _reset_frames, _report_at
    if _controller is None:
        return
    root = me.parent()
    now = time.perf_counter()
    elapsed = max(0.0001, now - _last_time)
    _last_time = now
    dt = min(1/30, max(1/240, elapsed))
    _metrics.append(elapsed)
    root.op('hand_camera').cook(force=True)
    session = root.fetch('tracking_session', None)
    if session != _session:
        _controller.reset()
        _session = session
    frame = root.fetch('latest_frame', None)
    _controller.smoothing_seconds = root.par.Smoothing.eval()
    interaction = _controller.update(frame, now)
    root.store('interaction_output', interaction)
    pointer = (interaction['x'],interaction['y'],interaction['dx'],interaction['dy'])
    step = (dt,root.par.Gain.eval(),root.par.Radius.eval(),root.par.Vorticity.eval())
    _vector(root.op('advect_velocity'),0,pointer)
    for name in ['advect_velocity','vorticity','advect_ink']:
        node = root.op(name)
        index = 1 if name == 'advect_velocity' else 0
        _vector(node,index,step)
    _vector(root.op('advect_velocity'),2,(int(_reset_frames>0),))
    _vector(root.op('advect_velocity'),3,(root.par.Damping.eval(),))
    _vector(root.op('advect_ink'),1,(int(_reset_frames>0),))
    _vector(root.op('advect_ink'),2,(root.par.Restore.eval(),))
    root.op('out').cook(force=True)
    _reset_frames = max(0,_reset_frames-1)
    if now >= _report_at:
        _report_at = now+1
        values=sorted(_metrics)
        fps=1/(sum(values)/len(values)) if values else 0
        p95=values[min(len(values)-1,int(len(values)*.95))]*1000
        status=root.fetch('camera_status',{})
        root.op('status_text').par.text = ('Art of Ink · DEBUG\n\n'
            'Camera: %s\n%s\n\nInput: %s\nHand: %s\nPosition: %.3f, %.3f\n'
            'Frame rate: %.1f FPS\nP95 interval: %.1f ms\nInference: %.1f ms\n\n'
            'Use the component parameters for debug, mute and fullscreen.' %
            (status.get('state','loading'),status.get('message',''),interaction['reason'],
             interaction['hand'],interaction['x'],interaction['y'],fps,p95,
             (frame or {}).get('inferenceMs',0)))
        report=dict(camera=status,input=interaction,fps=fps,p95_ms=p95,
                    inference_ms=(frame or {}).get('inferenceMs',0),
                    hand_count=len((frame or {}).get('hands',[])),
                    output=[root.op('out').width,root.op('out').height],
                    errors={n.path:n.errors() for n in root.children if n.errors()})
        _publish(report)


def stop():
    global _controller
    root=me.parent()
    root.op('hand_camera').par.active=False
    root.op('local_server').par.active=False
    root.par.Preview=False
    root.unstore('latest_frame')
    if _controller:
        _controller.reset()
    _controller=None
    _vector(root.op('advect_velocity'),0,(.5,.5,0,0))
    _vector(root.op('advect_velocity'),2,(1,))
    _vector(root.op('advect_ink'),1,(1,))
