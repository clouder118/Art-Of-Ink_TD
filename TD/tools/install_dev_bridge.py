"""Run once in TD's Python textport during development, never shipped active."""
from pathlib import Path

dev_root = Path(__file__).resolve().parents[1] / '.runtime'
dev_root.mkdir(exist_ok=True)
bridge = op('/ink_dev') or op('/').create(baseCOMP, 'ink_dev')
callback = bridge.op('execute') or bridge.create(executeDAT, 'execute')
callback.text = '''import time, pathlib, traceback, contextlib, io, json
_last = None
_poll = 0
_root = pathlib.Path(%r)
def onFrameStart(frame):
    global _last, _poll
    now = time.perf_counter()
    if now < _poll:
        return
    _poll = now + 0.25
    source = _root / 'command.py'
    if not source.exists():
        return
    stamp = source.stat().st_mtime_ns
    if stamp == _last:
        return
    _last = stamp
    output = io.StringIO()
    result = {'stamp': stamp, 'ok': True}
    try:
        with contextlib.redirect_stdout(output):
            scope = dict(globals(), __file__=str(source))
            exec(compile(source.read_text(encoding='utf-8-sig'), str(source), 'exec'), scope)
    except Exception:
        result['ok'] = False
        output.write(traceback.format_exc())
    result['output'] = output.getvalue()
    (_root / 'result.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
''' % str(dev_root)
callback.par.framestart = True
print('Art of Ink development bridge ready:', dev_root)
