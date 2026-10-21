"""Run inside TD after verification; save a clean, portable delivery project.

Uses a fresh filename to avoid TD's interactive overwrite dialog. This removes
only this project's temporary probe/bridge and the disabled startup sample.
"""
from pathlib import Path

folder=Path(__file__).resolve().parents[1]
target=folder/'ArtOfInk_TD.toe'
if target.exists():
    raise FileExistsError('Move the previous delivery file aside before exporting: '+str(target))
root=op('/artofink')
if root is None:
    raise RuntimeError('Build and verify /artofink before export')
root.op('runtime').module.stop()
root.op('lifecycle').par.active=False
root.par.Debug=False
root.par.Camera=''
root.par.Gain=24
root.storage.clear()
for name in ('runtime','server_callbacks'):
    root.op(name).text=(folder/'src'/f'{name}.py').read_text(encoding='utf-8')
root.op('output_window').par.size='fill'
root.op('output_window').par.borders=False
project.performOnStart=True
project.performWindowPath=root.op('output_window').path
for path in ('/ink_probe','/ink_dev'):
    temporary=op(path)
    if temporary:
        temporary.destroy()
sample=op('/project1')
if sample and not sample.allowCooking:
    sample.destroy()
root.op('lifecycle').par.active=True
if not project.save(str(target)):
    raise RuntimeError('TD failed to save the delivery project')
root.op('runtime').module.start()
print('Saved clean delivery project:',target)
