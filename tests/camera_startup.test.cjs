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
    performance:{now:()=>100},
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
    finishInference:()=>worker.onmessage({data:{kind:'result',inferenceMs:12,result:{landmarks:[],handedness:[]}}}),
    acknowledge:preview=>socket.onmessage({data:JSON.stringify({ack:true,preview})}),
    nextFrame:async time=>{video.readyState=2;video.currentTime=time/1000;await animationFrames.shift()(time);}};
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

test('keeps the live preview and waits for acknowledgement before another result',async()=>{
  const camera=await startCamera(()=>stream());
  await camera.nextFrame(100);
  await camera.nextFrame(150);
  assert.equal(camera.inferenceRequests.length,1);
  assert.equal(camera.drawing.images,0);
  camera.finishInference();
  assert.equal(camera.drawing.images,1);
  await camera.nextFrame(200);
  assert.equal(camera.drawing.images,1);
  camera.acknowledge(true);
  await camera.nextFrame(300);
  camera.finishInference();
  assert.equal(camera.drawing.images,2);
  assert.equal(camera.messages.filter(m=>m.kind==='hands').length,2);
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
});
test('worker reports inference errors and still releases the camera frame',async()=>{
  const worker=await startWorker(()=>({detectForVideo(){throw new Error('frame failed');}}));
  let closed=0;
  worker.send({image:{close(){closed++;}},timestamp:100});
  assert.equal(closed,1);
  assert.equal(worker.messages[1].kind,'error');
  assert.equal(worker.messages[1].message,'frame failed');
});
