"""TD-only integration probe: fixed motion must transport the actual painting."""
from pathlib import Path
import time

root=op('/artofink')
root.op('runtime').module.reset()
probe=op('/ink_probe') or op('/').create(baseCOMP,'ink_probe')
monitor=probe.op('fluid_probe') or probe.create(executeDAT,'fluid_probe')
monitor.text='''import time,json
import numpy as np
from pathlib import Path
started=time.perf_counter()
phase='reset'
baseline=None
def onFrameEnd(frame):
    global phase,baseline,started
    now=time.perf_counter()
    root=op('/artofink')
    if phase=='reset' and now-started>.3:
        baseline=root.op('out').numpyArray(delayed=False).copy()
        root.store('replay_start',now)
        started=now
        phase='drive'
    elif phase=='drive' and now-started>3:
        image=root.op('out').numpyArray(delayed=False).copy()
        velocity=root.op('project_velocity').numpyArray(delayed=False)
        difference=np.abs(image[:,:,:3]-baseline[:,:,:3])
        result={'mean_difference':float(difference.mean()),
                'max_difference':float(difference.max()),
                'changed_fraction':float((difference.max(axis=2)>.005).mean()),
                'max_velocity':float(np.abs(velocity[:,:,:2]).max())}
        result['pass']=result['mean_difference']>.0001 and result['changed_fraction']>.001
        folder=Path(project.folder)/'.runtime'
        (folder/'fluid_probe.json').write_text(json.dumps(result),encoding='utf-8')
        root.op('out').save(str(folder/'fluid_probe.png'))
        root.unstore('replay_start');root.unstore('replay_previous')
        phase='done'
        me.par.active=False
'''
monitor.par.frameend=True
print('Fixed-trajectory painting probe started')
