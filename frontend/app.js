const chat=document.getElementById("chat");
const menu=document.getElementById("menu");

function scrollBottom(){
  window.scrollTo({top:document.body.scrollHeight,behavior:"smooth"});
}

function addUser(text){
  chat.innerHTML += `<div class="user"><div class="bubble">${text}</div></div>`;
  scrollBottom();
}

function addCard(html){
  chat.innerHTML += `<div class="card">${html}</div>`;
  scrollBottom();
}

function createLoader(text="Thinking..."){
  const loaderCard=document.createElement("div");
  loaderCard.className="card";
  loaderCard.innerHTML=`
      <div class="typing">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div class="loader-text">${text}</div>
  `;
  chat.appendChild(loaderCard);
  scrollBottom();
  return loaderCard;
}

function toggleMenu(){
  menu.style.display = menu.style.display==="block" ? "none":"block";
}

/* TEXT CHAT */
async function send(){
  const input=document.getElementById("msg");
  const text=input.value.trim();
  if(!text) return;

  addUser(text);
  input.value="";
  const loader=createLoader("Thinking...");

  try{
    const res=await fetch("http://127.0.0.1:8000/chat",{
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ message:text })
    });

    const data=await res.json();
    loader.innerHTML=data.reply || data.error || "No response";
  }
  catch{
    loader.innerHTML="❌ Cannot connect to server";
  }
}

/* IMAGE UPLOAD */
function triggerPhoto(){
  toggleMenu();
  document.getElementById("photo").click();
}

document.getElementById("photo").onchange=async function(){
  const file=this.files[0];
  if(!file) return;

  addUser("📷 Image uploaded");
  addCard(`<img src="${URL.createObjectURL(file)}">`);

  const loader=createLoader("Analyzing image...");

  const formData=new FormData();
  formData.append("file",file);
  formData.append("question","Describe this image");

  const res=await fetch("http://127.0.0.1:8000/analyze-image",{method:"POST",body:formData});
  const data=await res.json();

  loader.innerHTML=data.result || data.error;
};

/* IMAGE GENERATION */
async function generateImage(){
  toggleMenu();
  const input=document.getElementById("msg");
  const prompt=input.value.trim();

  if(!prompt){ alert("Type image description"); return; }

  addUser("🎨 "+prompt);
  input.value="";
  const loader=createLoader("Generating image...");

  try{
    const res=await fetch("http://127.0.0.1:8000/generate-image",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ prompt })
    });

    const data=await res.json();

    if(data.image_url){
      loader.innerHTML=`<img src="${data.image_url}">`;
      return;
    }
    if(data.image_base64){
      loader.innerHTML=`<img src="data:image/png;base64,${data.image_base64}">`;
      return;
    }

    loader.innerHTML="❌ Image generation failed";
  }
  catch{
    loader.innerHTML="❌ Cannot connect to server";
  }
}

/* VOICE INPUT */
let recognition;
let listening=false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition=new SpeechRecognition();
  recognition.lang="en-AU";

  recognition.onstart=()=>{
    listening=true;
    document.querySelector(".mic").classList.add("listening");
  };

  recognition.onresult=(e)=>{
    document.getElementById("msg").value=e.results[0][0].transcript;
  };

  recognition.onend=()=>{
    listening=false;
    document.querySelector(".mic").classList.remove("listening");
  };
}

function toggleMic(){
  if(!recognition) return alert("Speech recognition not supported");
  listening ? recognition.stop() : recognition.start();
}

document.getElementById("msg").addEventListener("keypress",e=>{
  if(e.key==="Enter") send();
});