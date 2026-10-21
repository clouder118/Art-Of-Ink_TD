"""Rebuild the authored TD network in TD's Python environment.

Execute through tools/install_dev_bridge.py while developing. Delivery .toe is
saved separately after runtime verification; this file is the readable source.
"""
from pathlib import Path

folder = Path(__file__).resolve().parent
if Path(project.folder).resolve() != folder:
    raise RuntimeError('First save an empty TD project inside '+str(folder))
old = op('/artofink')
if old:
    old.destroy()
root = op('/').create(baseCOMP, 'artofink')
root.nodeX=0
root.nodeY=0
root.comment='Art of Ink TD · camera-driven interactive landscape'
page=root.appendCustomPage('Art of Ink')
for name,label,value in [('Debug','Debug view',False),('Preview','Camera preview window',True),('Mute','Mute music',False)]:
    p=page.appendToggle(name,label=label)[0];p.default=value;p.val=value
for name,label,value,low,high in [('Gain','Movement strength',24,0,80),
        ('Palmstrength','Open palm effect strength',1,0,3),
        ('Radius','Brush radius / image height',.03125,.005,.15),
        ('Restore','Original restoration / second',.54,.05,3),
        ('Damping','Velocity dissipation / second',7.67,.3,20),
        ('Smoothing','Hand smoothing / seconds',.035,0,.2),
        ('Vorticity','Vorticity',.5,0,10),('Volume','Music volume',.35,0,1)]:
    p=page.appendFloat(name,label=label)[0];p.default=value;p.val=value;p.min=low;p.max=high;p.clampMin=True;p.clampMax=True
for name,label,value,low,high in [('Gridwidth','Simulation width',384,128,640),
        ('Iterations','Pressure iterations',14,4,20),('Inferencefps','Recognition FPS',20,5,30)]:
    p=page.appendInt(name,label=label)[0];p.default=value;p.val=value;p.min=low;p.max=high;p.clampMin=True;p.clampMax=True
p=page.appendStr('Camera',label='Camera device ID (empty = default)')[0];p.default='';p.val=''
for name,label in [('Reset','Reset painting'),('Fullscreen','Toggle fullscreen'),('Restartcamera','Restart camera')]:
    page.appendPulse(name,label=label)


def text(name,source):
    n=root.create(textDAT,name)
    n.text=(folder/source).read_text(encoding='utf-8')
    return n


def shader(name,source,inputs,uniforms=()):
    n=root.create(glslTOP,name)
    n.par.pixeldat.eval().text=(folder/'shaders'/source).read_text(encoding='utf-8')
    n.par.format='rgba16float'
    n.seq.vec.numBlocks=max(1,len(uniforms))
    for i,name in enumerate(uniforms):
        getattr(n.par,'vec%dname'%i).val=name
    for i,source_node in enumerate(inputs):
        n.inputConnectors[i].connect(source_node)
    n.viewer=False
    return n


zero=root.create(constantTOP,'zero_field')
for name in ['colorr','colorg','colorb']:
    getattr(zero.par,name).val=0
zero.par.format='rgba16float'
zero.par.resolutionw.expr='parent().par.Gridwidth'
zero.par.resolutionh.expr='round(parent().par.Gridwidth*647/1280)'
velocity_history=root.create(feedbackTOP,'velocity_history')
velocity_history.inputConnectors[0].connect(zero)
velocity=shader('advect_velocity','velocity.frag',[velocity_history],['uPointer','uStep','uReset','uDamping'])
curl=shader('curl','curl.frag',[velocity])
vorticity=shader('vorticity','vorticity.frag',[velocity,curl],['uStep'])
divergence=shader('divergence','divergence.frag',[vorticity])
pressure=zero
pressure_selector=root.create(switchTOP,'pressure_iterations')
for i in range(20):
    pressure=shader('pressure_%02d'%(i+1),'pressure.frag',[pressure,divergence])
    pressure_selector.inputConnectors[i].connect(pressure)
pressure_selector.par.index.expr='parent().par.Iterations-1'
projected=shader('project_velocity','project.frag',[vorticity,pressure_selector])
velocity_history.par.top=projected
original=root.create(moviefileinTOP,'original')
original.par.file='assets/ink_painting3.png'
original.par.outputresolution='custom'
original.par.resolutionw=1280
original.par.resolutionh=647
ink_history=root.create(feedbackTOP,'ink_history')
ink_history.inputConnectors[0].connect(original)
ink=shader('advect_ink','ink.frag',[ink_history,projected,original],['uStep','uReset','uRestore','uPalm'])
ink.par.format='rgba32float'
ink.par.outputresolution='custom'
ink.par.resolutionw=1280
ink.par.resolutionh=647
ink_history.par.top=ink
out=root.create(nullTOP,'out')
out.inputConnectors[0].connect(ink)

server_code=text('server_callbacks','src/server_callbacks.py')
server=root.create(webserverDAT,'local_server')
server.par.active=False
server.par.callbacks=server_code
server.par.port=17980
camera=root.create(webrenderTOP,'hand_camera')
camera.par.active=False
camera.par.mediastream=True
camera.par.resolutionw=640
camera.par.resolutionh=480
camera.par.maxrenderrate=30
camera.par.url.expr="'http://127.0.0.1:'+str(parent().op('local_server').par.port.eval())+'/?fps='+str(parent().par.Inferencefps.eval())+'&camera='+__import__('urllib.parse',fromlist=['quote']).quote(parent().par.Camera.eval())"

presentation=root.create(containerCOMP,'presentation')
presentation.par.w=1280;presentation.par.h=647
presentation.par.top=out
presentation.par.topfill='best'
presentation.par.bgalpha=1
presentation.par.sizefromwindow=True
presentation.par.cursor='invisible'

preview=presentation.create(containerCOMP,'camera_preview')
preview.par.w.expr='min(480,max(240,parent().width*.28))'
preview.par.h.expr='me.width*.75+24'
preview.par.x.expr='max(0,parent().width-me.width-20)'
preview.par.y.expr='max(0,parent().height-me.height-20)'
preview.par.display.expr='int(parent(2).par.Preview)'
preview.par.layer=1;preview.par.bgalpha=1;preview.par.cursor='pointer'
image_panel=preview.create(containerCOMP,'image')
image_panel.par.w.expr='parent().width';image_panel.par.h.expr='parent().height-24'
image_panel.par.top=camera;image_panel.par.topfill='best'
title=root.create(textTOP,'preview_title')
title.par.text='摄像头预览';title.par.resolutionw=480;title.par.resolutionh=24
title.par.outputresolution='custom'
title.par.fontsizex=12;title.par.fontsizey=12
header=preview.create(containerCOMP,'header')
header.par.w.expr='parent().width';header.par.h=24
header.par.y.expr='parent().height-24'
header.par.top=title;header.par.topfill='best';header.par.bgalpha=1
cross=root.create(textTOP,'preview_cross')
cross.par.text='×';cross.par.resolutionw=28;cross.par.resolutionh=24
cross.par.outputresolution='custom'
cross.par.fontsizex=16;cross.par.fontsizey=16
close=preview.create(containerCOMP,'close')
close.par.w=28;close.par.h=24;close.par.layer=2
close.par.x.expr='parent().width-me.width';close.par.y.expr='parent().height-me.height'
close.par.top=cross;close.par.topfill='best';close.par.bgalpha=1
close_action=root.create(panelexecuteDAT,'preview_close')
close_action.par.panels=close;close_action.par.panelvalue='lselect'
close_action.par.offtoon=True
close_action.text="def onOffToOn(panelValue):\n    parent().par.Preview=False\n"

status=root.create(textTOP,'status_text')
status.par.text='Starting local hand tracking…'
status.par.resolutionw=640;status.par.resolutionh=647
status.par.outputresolution='custom'
debug=root.create(containerCOMP,'debug_view')
debug.par.w=1280;debug.par.h=647;debug.par.sizefromwindow=True
for name,top,x,y,w,h in [('art',out,0,0,860,647),('camera',camera,860,323,420,324),('status',status,860,0,420,323)]:
    panel=debug.create(containerCOMP,name)
    panel.par.x=x;panel.par.y=y;panel.par.w=w;panel.par.h=h
    panel.par.top=top;panel.par.topfill='best';panel.par.bgalpha=1
window=root.create(windowCOMP,'output_window')
window.par.winop.expr="parent().op('debug_view') if parent().par.Debug else parent().op('presentation')"
window.par.title='Art of Ink · Interactive landscape'
window.par.size='fill';window.par.winw=1280;window.par.winh=647
window.par.borders=False
window.par.justifyh='center';window.par.justifyv='center'
window.par.interact=True
music=root.create(audiofileinCHOP,'music')
music.par.file='assets/龚一 - 山居吟.mp3';music.par.repeat='on'
audio=root.create(audiodeviceoutCHOP,'speakers')
audio.inputConnectors[0].connect(music)
audio.par.volume.expr='0 if parent().par.Mute else parent().par.Volume'

runtime=text('runtime','src/runtime.py')
execute=root.create(executeDAT,'lifecycle')
execute.text='''def onStart():
    op('runtime').module.start()
def onFrameStart(frame):
    op('runtime').module.tick()
def onExit():
    op('runtime').module.stop()
'''
execute.par.start=True;execute.par.framestart=True;execute.par.exit=True
parameters=root.create(parameterexecuteDAT,'maintenance')
parameters.par.op=root
parameters.par.pars='Reset Fullscreen Restartcamera Debug Preview Inferencefps Camera'
parameters.par.onpulse=True
parameters.par.valuechange=True
parameters.text='''def onPulse(par):
    app=op('runtime').module
    if par.name=='Reset': app.reset()
    elif par.name=='Fullscreen': app.fullscreen()
    elif par.name=='Restartcamera': op('hand_camera').par.reload.pulse()
def onValueChange(par,prev):
    if par.name in ('Camera','Inferencefps'): op('hand_camera').par.reload.pulse()
    if par.name=='Debug': op('output_window').par.update.pulse()
'''
for i,n in enumerate(root.children):
    n.nodeX=(i%8)*180;n.nodeY=-(i//8)*120;n.viewer=False
if op('/project1'):
    op('/project1').allowCooking=False
runtime.module.start()
print('Art of Ink native network created:',root.path)
