// Uses Google's MediaPipe Tasks Vision (Apache-2.0); all assets are local.
import { FilesetResolver, HandLandmarker } from './vendor/vision_bundle.mjs';

const video = document.querySelector('#camera');
const canvas = document.querySelector('#preview');
const context = canvas.getContext('2d', { alpha: false });
const state = document.querySelector('#state');
const query = new URLSearchParams(location.search);
const targetFps = Math.min(30, Math.max(5, Number(query.get('fps') || 30)));
const deviceId = query.get('camera') || '';
let socket, model, sequence = 0, outstanding = false, sentAt = 0;
let lastVideoTime = -1, nextInference = 0, lastHeartbeat = 0;
let currentStatus = { state: 'loading', message: '正在加载本地模型' };
let delegate = 'GPU';

function send(value) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(value));
}
function report(status, message) {
  currentStatus = { state: status, message, delegate };
  state.textContent = message;
  send({ kind: 'status', ...currentStatus });
}
function connect() {
  socket = new WebSocket(`ws://${location.host}/tracking`);
  socket.onopen = () => { outstanding = false; send({ kind: 'status', ...currentStatus }); };
  socket.onmessage = () => { outstanding = false; };
  socket.onclose = () => { outstanding = false; setTimeout(connect, 1000); };
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
function tick(now) {
  requestAnimationFrame(tick);
  if (now - lastHeartbeat > 1000) {
    send({ kind: 'status', ...currentStatus });
    lastHeartbeat = now;
  }
  if (!model || video.readyState < 2 || now < nextInference || video.currentTime === lastVideoTime) return;
  if (outstanding && now - sentAt < 500) return;
  lastVideoTime = video.currentTime;
  nextInference = now + 1000 / targetFps;
  try {
    const start = performance.now();
    const result = model.detectForVideo(video, start);
    const inferenceMs = performance.now() - start;
    paint(result);
    if (socket?.readyState === WebSocket.OPEN) {
      send({ kind: 'hands', seq: ++sequence, inferenceMs, sentMs: performance.now(),
        hands: result.landmarks.map((landmarks, i) => ({ landmarks,
          label: result.handedness[i]?.[0]?.categoryName || 'Unknown',
          confidence: result.handedness[i]?.[0]?.score || 0 })) });
      outstanding = true;
      sentAt = performance.now();
    }
  } catch (error) {
    report('error', `识别失败：${error.message}`);
  }
}
connect();
requestAnimationFrame(tick);
async function start() {
  try {
    const vision = await FilesetResolver.forVisionTasks('./vendor/wasm');
    const options = { baseOptions: { modelAssetPath: './models/hand_landmarker.task', delegate },
      runningMode: 'VIDEO', numHands: 2, minHandDetectionConfidence: 0.55,
      minHandPresenceConfidence: 0.55, minTrackingConfidence: 0.55 };
    try { model = await HandLandmarker.createFromOptions(vision, options); }
    catch (error) {
      delegate = 'CPU';
      options.baseOptions.delegate = delegate;
      model = await HandLandmarker.createFromOptions(vision, options);
    }
    report('camera', '正在打开摄像头…');
    const constraints = { audio: false, video: { width: {ideal:640}, height:{ideal:480},
      frameRate: { ideal: targetFps, max: 30 }, ...(deviceId ? { deviceId: { exact: deviceId } } : {}) } };
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    await video.play();
    const devices = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput')
      .map(d => ({ id: d.deviceId, label: d.label }));
    send({ kind: 'devices', devices });
    report('ready', `摄像头已连接 · ${delegate} · ${targetFps} FPS 目标`);
    stream.getVideoTracks()[0].onended = () => report('error', '摄像头已断开，请重新连接并重启识别');
  } catch (error) {
    report('error', `启动失败：${error.name} · ${error.message}`);
  }
}
start();
