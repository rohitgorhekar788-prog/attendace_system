
let recTimer=null, recStream=null, recognizedIds=new Set();

function startStudentCamera(){
 const v=document.getElementById("studentVideo"); if(!v)return;
 navigator.mediaDevices.getUserMedia({video:true}).then(s=>{v.srcObject=s}).catch(e=>msg("captureMsg","Camera permission/error: "+e));
}
async function captureStudent(){
 const v=document.getElementById("studentVideo"), sid=document.getElementById("sid");
 if(!v || !sid || !sid.value){msg("captureMsg","Enter Student ID first.");return}
 const c=document.getElementById("studentCanvas"); c.width=v.videoWidth||640;c.height=v.videoHeight||480;
 c.getContext("2d").drawImage(v,0,0,c.width,c.height);
 const blob=await new Promise(r=>c.toBlob(r,"image/jpeg",.9));
 const fd=new FormData();fd.append("student_id",sid.value);fd.append("image",blob,"sample.jpg");
 const r=await fetch("/students/capture",{method:"POST",body:fd});const j=await r.json();msg("captureMsg",j.message);
}
function msg(id,t){const e=document.getElementById(id);if(e)e.innerText=t}
async function startRecognition(){
 if(recTimer)return;
 const v=document.getElementById("video"); if(!v)return;
 try{recStream=await navigator.mediaDevices.getUserMedia({video:true});v.srcObject=recStream;recognizedIds.clear();recTimer=setInterval(sendFrame,900);msg("recStatus","Camera running. Current slot: "+new Date().toLocaleTimeString())}
 catch(e){msg("recStatus","Camera permission/error: "+e)}
}
async function testRecognition(){await startRecognition()}
async function sendFrame(){
 const v=document.getElementById("video"), c=document.getElementById("canvas");if(!v.videoWidth)return;
 c.width=v.videoWidth;c.height=v.videoHeight;c.getContext("2d").drawImage(v,0,0,c.width,c.height);
 const image=c.toDataURL("image/jpeg",.75);
 try{
  const r=await fetch("/api/recognize",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image})});
  const j=await r.json(); if(!j.ok){msg("recStatus",j.message);return}
  const out=document.getElementById("resultImg");out.src=j.image; document.getElementById("video").style.display="none";out.style.display="block";
  (j.students||[]).forEach(s=>{recognizedIds.add(String(s.id));});
  document.getElementById("recognized").innerText=(j.students||[]).map(s=>`${s.name} | ${s.roll} | ${s.dep}`).join(" • ")||"No recognized student";
 }catch(e){console.error(e)}
}
async function stopRecognition(){
 if(recTimer){clearInterval(recTimer);recTimer=null}
 if(recStream){recStream.getTracks().forEach(t=>t.stop());recStream=null}
 const out=document.getElementById("resultImg");const v=document.getElementById("video");if(v)v.style.display="block";if(out)out.style.display="none";
 if(recognizedIds.size){
  const r=await fetch("/api/attendance",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids:[...recognizedIds]})});
  const j=await r.json();msg("recStatus",j.message||"Attendance saved.");
 }else msg("recStatus","Camera stopped. No recognized student.");
}
function clock(){const e=document.getElementById("clock");if(e)e.innerText=new Date().toLocaleTimeString()}
setInterval(clock,1000);clock();
