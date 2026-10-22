// Keep synchronous MediaPipe inference off the camera preview's UI thread.
let model;
async function initialize() {
  const {FilesetResolver, HandLandmarker} = await import('./vendor/vision_bundle.mjs');
  const vision = await FilesetResolver.forVisionTasks(new URL('./vendor/wasm', self.location.href).href);
  const options = {baseOptions: {
    modelAssetPath: new URL('./models/hand_landmarker.task', self.location.href).href,
    delegate: 'GPU'}, runningMode: 'VIDEO', numHands: 2,
    minHandDetectionConfidence: .55, minHandPresenceConfidence: .55,
    minTrackingConfidence: .55};
  let delegate = 'GPU';
  try { model = await HandLandmarker.createFromOptions(vision, options); }
  catch (error) {
    delegate = 'CPU';
    options.baseOptions.delegate = delegate;
    model = await HandLandmarker.createFromOptions(vision, options);
  }
  self.postMessage({kind: 'ready', delegate});
}
self.onmessage = event => {
  const {image, timestamp} = event.data;
  try {
    const start = performance.now();
    const result = model.detectForVideo(image, timestamp);
    self.postMessage({kind: 'result', result, captureMs: timestamp, inferenceMs: performance.now() - start});
  } catch (error) {
    self.postMessage({kind: 'error', message: error.message});
  } finally { image.close(); }
};
initialize().catch(error => self.postMessage({kind: 'error', message: `${error.name} · ${error.message}`}));
