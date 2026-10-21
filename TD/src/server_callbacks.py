"""Local static assets and latest-only hand results for TD's Web Server DAT."""
import json
import mimetypes
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit


def onHTTPRequest(webServerDAT, request, response):
    root = (Path(project.folder) / 'web').resolve()
    uri = unquote(urlsplit(request['uri']).path).lstrip('/') or 'index.html'
    path = (root / uri).resolve()
    response['Cache-Control'] = 'no-store'
    if not path.is_relative_to(root) or not path.is_file():
        response.update(statusCode=404, statusReason='Not Found', data='Not found')
        return response
    mime = {'.mjs': 'application/javascript', '.wasm': 'application/wasm',
            '.task': 'application/octet-stream'}.get(path.suffix)
    response['Content-Type'] = mime or mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
    response.update(statusCode=200, statusReason='OK', data=path.read_bytes())
    return response


def onWebSocketOpen(webServerDAT, client, uri):
    parent().store('tracking_session', time.perf_counter())
    parent().store('latest_frame', None)


def onWebSocketReceiveText(webServerDAT, client, data):
    try:
        message = json.loads(data)
        root = parent()
        if message.get('kind') == 'hands':
            message['received_at'] = time.perf_counter()
            root.store('latest_frame', message)
            webServerDAT.webSocketSendText(client, '{"ack":true}')
        elif message.get('kind') == 'status':
            root.store('camera_status', message)
        elif message.get('kind') == 'devices':
            root.store('camera_devices', message['devices'])
    except (ValueError, KeyError, TypeError):
        parent().store('camera_status', {'state': 'error', 'message': 'Invalid camera result'})


def onWebSocketClose(webServerDAT, client):
    parent().store('latest_frame', None)
    parent().store('camera_status', {'state': 'disconnected', 'message': '识别连接已断开'})
