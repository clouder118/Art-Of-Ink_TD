// Uses Google's MediaPipe Tasks Vision (Apache-2.0); all assets are local.
const video = document.querySelector('#camera');
const canvas = document.querySelector('#preview');
const context = canvas.getContext('2d', { alpha: false });
const state = document.querySelector('#state');
const query = new URLSearchParams(location.search);
const targetFps = Math.min(30, Math.max(5, Number(query.get('fps') || 30)));
const deviceId = query.get('camera') || '';
let socket, modelReady = false, sequence = 0, outstanding = false, sentAt = 0;
let inferencePending = false;
let pendingResult = null;
let lastVideoTime = -1, nextInference = 0, lastHeartbeat = 0;
let currentStatus = { state: 'loading', message: '正在加载本地模型' };
let delegate = 'GPU';
let openingCamera = false;

function send(value) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(value));
}
function report(status, message) {
  currentStatus = { ...currentStatus, state: status, message, delegate };
  state.textContent = message;
  send({ kind: 'status', ...currentStatus });
}
function connect() {
  socket = new WebSocket(`ws://${location.host}/tracking`);
  socket.onopen = () => { outstanding = false; pendingResult = null; send({ kind: 'status', ...currentStatus }); };
  socket.onmessage = () => { outstanding = false; flushResult(); };
  socket.onclose = () => { outstanding = false; pendingResult = null; setTimeout(connect, 1000); };
}
function flushResult() {
  const now = performance.now();
  if (!pendingResult || socket?.readyState !== WebSocket.OPEN) return;
  if (outstanding && now - sentAt < 500) return;
  send(pendingResult);
  pendingResult = null;
  outstanding = true;
  sentAt = now;
}
function paint(result) {
  context.save();
  context.translate(640, 0);
  context.scale(-1, 1);
  context.drawImage(video, 0, 0, 640, 480);
  context.lineWidth = 2;
  for (const hand of result.landmarks) {
    for (const finger of [[0,1,2,3,4],[0,5,6,7,8],[0,9,10,11,12],[0,13,14,15,16],[0,17,18,19,20]]) {
      context.strokeStyle = '#99d7ba';
      context.beginPath();
      for (const i of finger) context.lineTo(hand[i].x * 640, hand[i].y * 480);
      context.stroke();
    }
    context.fillStyle = '#f6d777';
    context.beginPath();
    context.arc(hand[8].x * 640, hand[8].y * 480, 5, 0, Math.PI * 2);
    context.fill();
  }
  context.restore();
}
function consumeResult(result, inferenceMs, captureMs) {
  paint(result);
  if (socket?.readyState === WebSocket.OPEN) {
    // One in-flight message plus one replaceable latest result, never a queue.
    pendingResult = { kind: 'hands', seq: ++sequence, inferenceMs, captureMs, sentMs: performance.now(),
      hands: result.landmarks.map((landmarks, i) => ({ landmarks,
        label: result.handedness[i]?.[0]?.categoryName || 'Unknown',
        confidence: result.handedness[i]?.[0]?.score || 0 })) };
    flushResult();
  }
}
async function tick(now) {
  requestAnimationFrame(tick);
  if (now - lastHeartbeat > 1000) {
    send({ kind: 'status', ...currentStatus });
    lastHeartbeat = now;
  }
  flushResult();
  await tryInference(now);
}
async function tryInference(now) {
  if (!modelReady || inferencePending || video.readyState < 2 || now + .1 < nextInference || video.currentTime === lastVideoTime) return;
  lastVideoTime = video.currentTime;
  // Keep the cadence instead of rounding every deadline up to the next repaint.
  // After a long stall restart from now; never build an inference backlog.
  nextInference = Math.max(nextInference + 1000 / targetFps, now);
  inferencePending = true;
  try {
    const image = await createImageBitmap(video);
    worker.postMessage({image, timestamp: now}, [image]);
  } catch (error) {
    inferencePending = false;
    report('error', `识别失败：${error.message}`);
  }
}
connect();
requestAnimationFrame(tick);
async function openCamera() {
  if (openingCamera) return;
  openingCamera = true;
  let lastError;
  try {
    for (let attempt = 0; attempt < 4; attempt++) {
      const devices = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput');
      // Windows can select an unavailable virtual camera as the default.
      const physical = devices.filter(d => d.label && !/virtual|obs/i.test(d.label)).map(d => d.deviceId);
      const candidates = deviceId ? [deviceId] : [...new Set([...physical, ''])];
      for (const candidate of candidates) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: false, video: {
            width: {ideal:640}, height:{ideal:480}, frameRate:{ideal:targetFps,max:30},
            ...(candidate ? {deviceId:{exact:candidate}} : {}) } });
          video.srcObject = stream;
          await video.play();
          lastVideoTime = -1;
          send({kind:'devices',devices:(await navigator.mediaDevices.enumerateDevices())
            .filter(d => d.kind === 'videoinput').map(d => ({id:d.deviceId,label:d.label}))});
          const settings=stream.getVideoTracks()[0].getSettings?.() || {};
          currentStatus.videoSettings={width:settings.width,height:settings.height,frameRate:settings.frameRate};
          report('ready', `摄像头已连接 · ${delegate} · ${targetFps} FPS 目标`);
          stream.getVideoTracks()[0].onended = () => {
            report('camera', '摄像头已断开，正在尝试恢复…');
            video.srcObject = null;
            setTimeout(openCamera, 1000);
          };
          return;
        } catch (error) { lastError = error; }
      }
      if (lastError?.name === 'NotAllowedError') break;
      report('camera', `摄像头暂不可用，正在重试 (${attempt+1}/4)…`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (attempt+1)));
    }
    report('error', `摄像头启动失败：${lastError?.name} · ${lastError?.message}`);
  } finally { openingCamera = false; }
}
const worker = new Worker('./hand_worker.js');
worker.onmessage = async event => {
  const message = event.data;
  if (message.kind === 'ready') {
    modelReady = true;
    delegate = message.delegate;
    report('camera', '正在打开摄像头…');
    await openCamera();
  } else if (message.kind === 'result') {
    inferencePending = false;
    consumeResult(message.result, message.inferenceMs, message.captureMs);
    await tryInference(performance.now());
  } else if (message.kind === 'error') {
    inferencePending = false;
    report('error', `识别失败：${message.message}`);
  }
};
worker.onerror = error => { inferencePending = false; report('error', `识别线程失败：${error.message}`); };
