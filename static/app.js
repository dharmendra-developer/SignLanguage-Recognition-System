import { FilesetResolver, HandLandmarker, DrawingUtils } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";
const $=id=>document.getElementById(id);
const video=$("video"),canvas=$("canvas"),ctx=canvas.getContext("2d");
let stream=null,landmarker=null,running=false,raf=null,language="en",capturing=false,samples=[],lastSent=0,lastLabel="",stable=0,lastAppend=0;
const API="";
function normalize(points){
 const wrist=points[0],p=points.map(v=>[v.x-wrist.x,v.y-wrist.y,v.z-wrist.z]);
 const scale=Math.max(...p.map(v=>Math.hypot(...v)),0.0001);
 return p.flatMap(v=>v.map(n=>n/scale));
}
async function api(path,options={}){const r=await fetch(API+path,{headers:{"Content-Type":"application/json"},...options});const d=await r.json();if(!r.ok)throw new Error(d.error||"Request failed");return d;}
function dualHandFeatures(hands,handedness){
 const left=new Array(63).fill(0),right=new Array(63).fill(0);
 hands.forEach((pts,index)=>{
  const label=handedness?.[index]?.[0]?.categoryName?.toLowerCase()||"";
  const normalized=normalize(pts);
  if(label==="left")left.splice(0,63,...normalized);
  else if(label==="right")right.splice(0,63,...normalized);
  else if(left.every(v=>v===0))left.splice(0,63,...normalized);
  else if(right.every(v=>v===0))right.splice(0,63,...normalized);
 });
 return [...left,...right];
}
async function refresh(){
 try{const d=await api("/api/health");$("statusDot").style.background="#65e0c0";$("statusText").textContent="Backend connected";$("sampleCount").textContent=d.samples+" samples";$("statSamples").textContent=d.samples;$("statClasses").textContent=d.labels.length;
 $("classList").innerHTML=d.labels.length?d.labels.map(x=>`<span class="class-chip">${escapeHtml(x.label)} · ${x.n}</span>`).join(""):'<p class="muted">No gesture classes collected yet.</p>';
 }catch(e){$("statusText").textContent="Backend offline";$("statusDot").style.background="#ef7777";}
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
async function start(){
 try{
  if(!window.isSecureContext){
   throw new Error("This page is not secure. Open http://127.0.0.1:5000, not an IP address or http://0.0.0.0.");
  }
  if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
   throw new Error("Camera API unavailable. Open this page in Chrome or Edge.");
  }

 $("statusText").textContent="Loading AI vision…";
  const constraints=[
   {video:{facingMode:"user",width:{ideal:1280},height:{ideal:720}},audio:false},
   {video:{facingMode:"user"},audio:false},
   {video:true,audio:false}
  ];
  let cameraError=null;
  for(const constraint of constraints){
   try{
    stream=await navigator.mediaDevices.getUserMedia(constraint);
    cameraError=null;
    break;
   }catch(error){
    cameraError=error;
    if(error.name==="NotAllowedError"||error.name==="SecurityError")break;
   }
  }
  if(!stream)throw cameraError||new Error("A camera could not be found.");

  video.srcObject=stream;
  await video.play();

  const vision=await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm");
  const landmarkerOptions={
   baseOptions:{
    modelAssetPath:"https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    delegate:"GPU"
   },
   runningMode:"VIDEO",
   numHands:2,
   minHandDetectionConfidence:0.3,
   minHandPresenceConfidence:0.3,
   minTrackingConfidence:0.3
  };
  try{
   landmarker=await HandLandmarker.createFromOptions(vision,landmarkerOptions);
  }catch(gpuError){
   landmarkerOptions.baseOptions.delegate="CPU";
   landmarker=await HandLandmarker.createFromOptions(vision,landmarkerOptions);
  }

  running=true;$("cameraEmpty").style.display="none";$("cameraBadge").textContent="CAMERA LIVE";$("startBtn").disabled=true;$("stopBtn").disabled=false;$("captureBtn").disabled=false;document.querySelector(".camera-panel").classList.add("camera-on");loop();
 }catch(e){
  if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
  let message=e.message||"Camera could not start.";
  if(e.name==="NotAllowedError"||e.name==="PermissionDeniedError"){
   message="Camera permission denied. Allow Camera access in the Chrome/Edge site settings, then click Start camera again.";
  }else if(e.name==="NotFoundError"||e.name==="DevicesNotFoundError"){
   message="No camera was found. Connect a webcam and check Windows Privacy & security > Camera.";
  }else if(e.name==="NotReadableError"||e.name==="TrackStartError"){
   message="Camera is busy or blocked by another app. Close other camera apps, then try again.";
  }else if(e.name==="OverconstrainedError"){
   message="The camera cannot use the requested settings. Try another camera or browser.";
  }
  $("statusText").textContent="Camera/model error";$("cameraBadge").textContent="CAMERA ERROR";
  $("cameraHelp").textContent=message;
  $("captureHelp").textContent=message;
 }
}
function stop(){running=false;if(raf)cancelAnimationFrame(raf);if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;ctx.clearRect(0,0,canvas.width,canvas.height);$("cameraEmpty").style.display="grid";$("cameraBadge").textContent="CAMERA OFF";$("startBtn").disabled=false;$("stopBtn").disabled=true;$("captureBtn").disabled=true;document.querySelector(".camera-panel").classList.remove("camera-on");}
async function loop(){
 if(!running)return;
 if(video.readyState>=2){
  try{
   const result=landmarker.detectForVideo(video,performance.now());
   canvas.width=video.videoWidth;
   canvas.height=video.videoHeight;
   ctx.clearRect(0,0,canvas.width,canvas.height);
   const hands=result.landmarks||[];
   if(hands.length){
    const draw=new DrawingUtils(ctx);
    hands.forEach(pts=>{
     draw.drawConnectors(pts,HandLandmarker.HAND_CONNECTIONS,{color:"#89a8ff",lineWidth:4});
     draw.drawLandmarks(pts,{color:"#65e0c0",lineWidth:1,radius:4});
    });
    const features=dualHandFeatures(hands,result.handedness);
    $("confidence").textContent=hands.length===2?"Two hands detected":"One hand detected";
    if(capturing){samples.push(features);$("captureCount").textContent=`${samples.length} / 40 samples`;$("progressBar").style.width=(samples.length/40*100)+"%";if(samples.length>=40)await saveSamples();}
    else if(Date.now()-lastSent>140){
     lastSent=Date.now();try{const d=await api("/api/predict",{method:"POST",body:JSON.stringify({features})});
       if(d.accepted){$("prediction").textContent=language==="hi"?d.hindi:d.label;$("confidence").textContent=`${d.confidence}% model confidence`;
        if(d.label===lastLabel)stable++;else{lastLabel=d.label;stable=0;}
        if(stable>=4&&Date.now()-lastAppend>1100){appendWord(d);lastAppend=Date.now();stable=0;}
       }else{$("prediction").textContent="…";$("confidence").textContent="Low confidence — hold the sign steady";}
     }catch(e){$("confidence").textContent=e.message.includes("not trained")?"Train a model to start recognition":e.message;}
    }
   }else{$("prediction").textContent="—";$("confidence").textContent="Show one or both hands clearly in the camera";}
  }catch(error){
   $("cameraHelp").textContent="Hand tracking stopped: "+(error.message||"MediaPipe detection error");
   $("confidence").textContent="Hand tracking error";
  }
 }
 raf=requestAnimationFrame(loop);
}
function appendWord(d){const word=language==="hi"?d.hindi:d.label;const el=$("sentence");el.value=el.value.trim()?el.value.trim()+" "+word:word;}
async function saveSamples(){
 capturing=false;$("captureBtn").disabled=false;$("captureBtn").textContent="Capture 40 samples";
 try{const d=await api("/api/samples",{method:"POST",body:JSON.stringify({label:$("englishLabel").value.trim(),hindi_label:$("hindiLabel").value.trim(),samples})});$("captureHelp").textContent=`Saved ${d.saved} samples for ${d.label}. Capture more classes, then train.`;samples=[];$("captureCount").textContent="0 / 40 samples";$("progressBar").style.width="0%";await refresh();}
 catch(e){$("captureHelp").textContent=e.message;samples=[];}
}
$("startBtn").onclick=start;$("stopBtn").onclick=stop;
$("captureBtn").onclick=()=>{
 if(!$("englishLabel").value.trim()||!$("hindiLabel").value.trim()){$("captureHelp").textContent="Enter both English label and Hindi meaning.";return;}
 samples=[];capturing=true;$("captureBtn").disabled=true;$("captureBtn").textContent="Capturing…";$("captureHelp").textContent="Hold the gesture steadily; 40 frames will be collected.";
};
$("trainBtn").onclick=async()=>{const b=$("trainBtn");b.disabled=true;b.textContent="Training model…";try{const d=await api("/api/train",{method:"POST",body:"{}"});$("modelResult").textContent=`Model trained · ${d.accuracy}% holdout accuracy · ${d.samples} samples · Classes: ${d.classes.join(", ")}. ${d.note}`;$("statAccuracy").textContent=d.accuracy+"%";await refresh();}catch(e){$("modelResult").textContent=e.message;}finally{b.disabled=false;b.textContent="Train AI model";}};
$("resetBtn").onclick=async()=>{
 if(!window.confirm("Delete every collected gesture and the trained model?"))return;
 const b=$("resetBtn");b.disabled=true;b.textContent="Resetting…";
 try{const d=await api("/api/samples",{method:"DELETE"});$("modelResult").textContent=`Data reset · ${d.deleted} samples deleted`;$("statAccuracy").textContent="—";await refresh();}
 catch(e){$("modelResult").textContent=e.message;}
 finally{b.disabled=false;b.textContent="Reset all collected data";}
};
document.querySelectorAll(".lang").forEach(b=>b.onclick=()=>{language=b.dataset.lang;document.querySelectorAll(".lang").forEach(x=>x.classList.toggle("active",x===b));});
$("speakBtn").onclick=()=>{const t=$("sentence").value.trim();if(!t)return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang=language==="hi"?"hi-IN":"en-IN";speechSynthesis.speak(u);};
$("undoBtn").onclick=()=>{$("sentence").value=$("sentence").value.trim().split(/\s+/).slice(0,-1).join(" ");};
$("clearBtn").onclick=()=>{$("sentence").value="";};
window.addEventListener("beforeunload",stop);refresh();setInterval(refresh,10000);
