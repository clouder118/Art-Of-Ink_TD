// Exercise the actual shipped adapter against browser media-device failures.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

async function startCamera(getUserMedia,search='') {
  const calls=[],messages=[];
  const animationFrames=[];
  const drawing={images:0,clears:0};
  const canvasContext={save(){},restore(){},translate(){},scale(){},
    drawImage(){drawing.images++;},fillRect(){drawing.clears++;}};
  const video={readyState:0,play:async()=>{}};
  const state={};
  const clock={now:0};
  let socket,worker;
  const inferenceRequests=[];
  class InferenceWorker {
    constructor(){worker=this;queueMicrotask(()=>this.onmessage({data:{kind:'ready',delegate:'GPU'}}));}
    postMessage(request){inferenceRequests.push(request);}
  }
  class Socket {
    constructor(){socket=this;}
    static OPEN=1;
    readyState=1;
    send(text) { messages.push(JSON.parse(text)); }
  }
  const context={
    URLSearchParams,WebSocket:Socket,location:{host:'127.0.0.1:17980',search},
    document:{querySelector:selector=>selector==='#camera'?video:selector==='#state'?state:{getContext:()=>canvasContext}},
    requestAnimationFrame:fn=>animationFrames.push(fn),setTimeout:fn=>queueMicrotask(fn),
    performance:{now:()=>clock.now},
    Worker:InferenceWorker,createImageBitmap:async()=>({close(){}}),
    navigator:{mediaDevices:{
      enumerateDevices:async()=>[
        {kind:'videoinput',deviceId:'obs',label:'OBS Virtual Camera'},
        {kind:'videoinput',deviceId:'physical',label:'Built-in Camera'}],
      getUserMedia:async constraints=>{calls.push(constraints);return getUserMedia(constraints,calls.length);}
    }}
  };
  const source=fs.readFileSync(path.join(__dirname,'../TD/web/hand_tracking.js'),'utf8')
    .replace(/^import .*$/m,'');
  vm.runInNewContext(source,context);
  for(let i=0;i<20&&!messages.some(m=>m.state==='ready'||m.state==='error');i++) {
    await new Promise(resolve=>setImmediate(resolve));
  }
  return {calls,messages,drawing,inferenceRequests,
    finishInference:async time=>{
      if(time!==undefined){clock.now=time;video.currentTime=time/1000;}
      await worker.onmessage({data:{kind:'result',inferenceMs:12,
        captureMs:inferenceRequests.at(-1).timestamp,result:{landmarks:[],handedness:[]}}});},
    acknowledge:preview=>socket.onmessage({data:JSON.stringify({ack:true,preview})}),
    nextFrame:async time=>{clock.now=time;video.readyState=2;video.currentTime=time/1000;await animationFrames.shift()(time);}};
}
const stream=()=>({getVideoTracks:()=>[{}]});

test('prefers the physical camera when Windows lists OBS first',async()=>{
  const {calls,messages}=await startCamera(()=>stream());
  assert.equal(calls[0].video.deviceId.exact,'physical');
  assert.ok(messages.some(m=>m.state==='ready'));
});
test('recovers from a transient NotReadableError with bounded retries',async()=>{
  const {calls,messages}=await startCamera((_,n)=>{
    if(n<3)throw Object.assign(new Error('busy'),{name:'NotReadableError'});
    return stream();
  });
  assert.equal(calls.length,3);
  assert.ok(messages.some(m=>m.state==='ready'));
});
test('honors an explicit device and stops after four failed attempts',async()=>{
  const {calls,messages}=await startCamera(()=>{
    throw Object.assign(new Error('busy'),{name:'NotReadableError'});
  },'?camera=chosen');
  assert.equal(calls.length,4);
  assert.ok(calls.every(c=>c.video.deviceId.exact==='chosen'));
  assert.ok(messages.some(m=>m.state==='error'));
});

test('starts the next inference without waiting for repaint and publishes only the latest pending result',async()=>{
  const camera=await startCamera(()=>stream());
  await camera.nextFrame(0);
  await camera.nextFrame(33);
  assert.equal(camera.inferenceRequests.length,1);
  assert.equal(camera.drawing.images,0);
  await camera.finishInference(40);
  assert.equal(camera.inferenceRequests.length,2);
  assert.equal(camera.drawing.images,1);
  await camera.finishInference(80);
  await camera.finishInference(120);
  assert.equal(camera.messages.filter(m=>m.kind==='hands').length,1);
  camera.acknowledge(true);
  const published=camera.messages.filter(m=>m.kind==='hands');
  assert.equal(camera.drawing.images,3);
  assert.equal(published.length,2);
  assert.equal(published[1].seq,3);
});

test('20 FPS target does not collapse to 15 FPS on a 30 FPS preview clock',async()=>{
  const camera=await startCamera(()=>stream(),'?fps=20');
  for(let i=0;i<30;i++){
    const before=camera.inferenceRequests.length;
    await camera.nextFrame(i*1000/30);
    if(camera.inferenceRequests.length>before){await camera.finishInference();camera.acknowledge();}
  }
  assert.ok(camera.inferenceRequests.length>=19,
    `only ${camera.inferenceRequests.length} inferences were scheduled`);
});

test('30 FPS captures stay bounded and carry the original capture timestamp',async()=>{
  const camera=await startCamera(()=>stream(),'?fps=30');
  for(let i=0;i<30;i++){
    const before=camera.inferenceRequests.length;
    await camera.nextFrame(i*1000/30);
    if(camera.inferenceRequests.length>before){await camera.finishInference();camera.acknowledge();}
  }
  assert.equal(camera.inferenceRequests.length,30);
  const frames=camera.messages.filter(m=>m.kind==='hands');
  assert.equal(frames.length,30);
  assert.equal(frames[10].captureMs,camera.inferenceRequests[10].timestamp);
  assert.equal(camera.calls[0].video.frameRate.ideal,30);
});

async function startWorker(createModel) {
  const messages=[],delegates=[];
  const context={URL,performance:{now:()=>100},self:{
    location:{href:'http://127.0.0.1:17980/hand_worker.js'},
    postMessage:value=>messages.push(value)},
    mockVision:async()=>({FilesetResolver:{forVisionTasks:async()=>({})},
      HandLandmarker:{createFromOptions:async(_,options)=>{
        delegates.push(options.baseOptions.delegate);
        return createModel(options);
      }}})};
  const source=fs.readFileSync(path.join(__dirname,'../TD/web/hand_worker.js'),'utf8')
    .replace("await import('./vendor/vision_bundle.mjs')",'await mockVision()');
  vm.runInNewContext(source,context);
  await new Promise(resolve=>setImmediate(resolve));
  return {messages,delegates,send:data=>context.self.onmessage({data})};
}
test('worker falls back to CPU and releases each transferred camera frame',async()=>{
  const result={landmarks:[],handedness:[]};
  const worker=await startWorker(options=>{
    if(options.baseOptions.delegate==='GPU')throw new Error('GPU unavailable');
    return {detectForVideo:()=>result};
  });
  assert.deepEqual(worker.delegates,['GPU','CPU']);
  assert.equal(worker.messages[0].delegate,'CPU');
  let closed=0;
  worker.send({image:{close(){closed++;}},timestamp:100});
  assert.equal(closed,1);
  assert.equal(worker.messages[1].result,result);
  assert.equal(worker.messages[1].captureMs,100);
});
test('worker reports inference errors and still releases the camera frame',async()=>{
  const worker=await startWorker(()=>({detectForVideo(){throw new Error('frame failed');}}));
  let closed=0;
  worker.send({image:{close(){closed++;}},timestamp:100});
  assert.equal(closed,1);
  assert.equal(worker.messages[1].kind,'error');
  assert.equal(worker.messages[1].message,'frame failed');
});
