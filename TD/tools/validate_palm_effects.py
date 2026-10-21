"""Run inside TD: synthetic palm-field validation, landscape-only stills.

Restores real camera control on completion/error. No camera frames or landmarks
are recorded. The diagnostic TOP uses the actual GLSL palmVelocity function.
"""
from pathlib import Path

root=op('/artofink')
probe=op('/ink_probe') or op('/').create(baseCOMP,'ink_probe')
field=probe.op('palm_field') or probe.create(glslTOP,'palm_field')
source=(Path(project.folder)/'shaders/ink.frag').read_text(encoding='utf-8')
field.par.pixeldat.eval().text=source.split('void main(){')[0]+'''
void main(){fragColor=TDOutputSwizzle(vec4(palmVelocity(vUV.st),0,1));}
'''
field.par.outputresolution='custom'
field.par.resolutionw=384;field.par.resolutionh=194
field.par.format='rgba32float'
field.seq.vec.numBlocks=1;field.par.vec0name='uPalm'
monitor=probe.op('palm_validation') or probe.create(executeDAT,'palm_validation')
monitor.par.active=False
monitor.text='''import time,json,traceback
from pathlib import Path
import numpy as np
r=op('/artofink');runtime=r.op('runtime').module
original_controller=runtime._controller;original_palm=runtime._palm
folder=Path(project.folder).parent/'docs/validation/palm-effects'
folder.mkdir(parents=True,exist_ok=True)
stages=[('wave',5),('restore_wave',8),('spiral',5),('restore_spiral',8),('ripple',5),('restore_ripple',8)]
phase=0;started=time.perf_counter();results=[]
names=('none','wave','spiral','ripple')
class Idle:
 smoothing_seconds=0
 def reset(self):pass
 def update(self,frame,now):return dict(active=False,x=.5,y=.5,dx=0,dy=0,vx=0,vy=0,hand='',reason='synthetic-palm-validation',gesture='none')
class Driver:
 def reset(self,**kwargs):pass
 def tracking_reset(self):pass
 def update(self,obs,frame,now):
  name,duration=stages[phase];mode=name.replace('restore_','');t=now-started;rest=name.startswith('restore_')
  strength=np.exp(-t/.45) if rest else 1-np.exp(-t/(.25/3))
  return dict(gesture='none' if rest else 'palm',effect=mode,effect_id=names.index(mode),next_effect=names[names.index(mode)%3+1],effect_time=t+5 if rest else t,effect_strength=float(strength),palm_active=not rest)
runtime._controller=Idle();runtime._palm=Driver();runtime.reset()
original=r.op('original').numpyArray(delayed=False).copy()

def field_at(mode,t):
 node=op('/ink_probe/palm_field')
 for axis,value in zip('xyzw',(mode,t,1,1)):getattr(node.par,'vec0value'+axis).val=value
 node.cook(force=True)
 return node.numpyArray(delayed=False)[:,:,:2].copy()

def directions():
 field=field_at(1,.8);h,w=field.shape[:2]
 xx,yy=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
 p=np.stack(((xx-.5)*(1280/647),yy-.5),axis=-1)
 d=np.array([1280/647,1]);d=d/np.linalg.norm(d)
 def center(t):
  f=field_at(1,t)*np.array([1280/647,1]);weight=np.linalg.norm(f,axis=-1)
  return float(np.sum(np.sum(p*d,axis=-1)*weight)/np.sum(weight))
 wave_start=center(.8);wave_end=center(2.8)
 spiral=field_at(2,2)*np.array([1280/647,1])
 ripple=field_at(3,1)*np.array([1280/647,1])
 mask=(np.linalg.norm(p,axis=-1)>.08)&(np.linalg.norm(p,axis=-1)<.8)
 def dots(f):return np.sum(p*f,axis=-1)
 def cross(f):return p[:,:,0]*f[:,:,1]-p[:,:,1]*f[:,:,0]
 values=dict(wave_start=wave_start,wave_end=wave_end,
  spiral_radial_mean=float(dots(spiral)[mask].mean()),spiral_cross_mean=float(cross(spiral)[mask].mean()),
  ripple_radial_mean=float(dots(ripple)[mask].mean()),ripple_cross_max=float(np.abs(cross(ripple)).max()),
  fields_finite=bool(all(np.isfinite(f).all() for f in (field,spiral,ripple))))
 values['pass']=bool(values['fields_finite'] and wave_end>wave_start+.5 and values['spiral_radial_mean']>0 and values['spiral_cross_mean']<0 and values['ripple_radial_mean']>0 and values['ripple_cross_max']<1e-6)
 return values

direction_report={}
def finish(error=None):
 runtime._controller=original_controller;runtime._palm=original_palm
 original_controller.reset();original_palm.reset();runtime._motion.reset()
 by_name={x['phase']:x for x in results}
 passed=not error and direction_report['pass'] and len(results)==6
 if passed:
  passed=all(x['finite'] for x in results) and all(by_name[n]['mean_difference']>.0005 and by_name['restore_'+n]['mean_difference']<by_name[n]['mean_difference']*.1 for n in ('wave','spiral','ripple'))
 report=dict(input='synthetic programmatic palm effects; not manual gesture acceptance',directions=direction_report,segments=results,error=error,passed=bool(passed),errors={n.path:n.errors() for n in r.children if n.errors()})
 (folder/'native-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 me.par.active=False

def onFrameEnd(frame):
 global phase,started,direction_report
 try:
  if not direction_report:direction_report=directions()
  now=time.perf_counter();name,duration=stages[phase]
  if now-started<duration:return
  image=r.op('out').numpyArray(delayed=False).copy()
  delta=np.abs(image[:,:,:3]-original[:,:,:3])
  results.append(dict(phase=name,seconds=now-started,mean_difference=float(delta.mean()),changed_fraction=float(np.mean(delta.max(axis=-1)>.02)),finite=bool(np.isfinite(image).all())))
  r.op('out').save(str(folder/(name+'.png')))
  phase+=1
  if phase==len(stages):finish();return
  started=now
  if not stages[phase][0].startswith('restore_'):runtime.reset()
 except Exception:finish(traceback.format_exc())
'''
monitor.par.frameend=True
monitor.par.active=True
print('Started 39-second synthetic palm validation; real hand control restores automatically')
