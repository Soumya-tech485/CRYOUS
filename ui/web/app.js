const $ = id => document.getElementById(id);
const feed = $("feed"), act = $("activity"), detail = $("detail");
const STATE_META = {
  dormant:["STANDBY"], listening:["LISTENING"], followup:["FOLLOW-UP"],
  thinking:["PROCESSING"], speaking:["SPEAKING"], sleep:["SLEEP MODE"], off:["OFFLINE"],
};
let ws, reconnectT;

function connect(){
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen  = () => { $("linkStat").textContent = "link stable"; actLog("Neural link established","ok"); };
  ws.onclose = () => { $("linkStat").textContent = "link lost — retrying";
                       clearTimeout(reconnectT); reconnectT = setTimeout(connect, 1500); };
  ws.onmessage = e => route(JSON.parse(e.data));
}

function route(m){
  const d = m.data || {};
  switch(m.type){
    case "state":      setState(d.state); break;
    case "transcript": addMsg("user", d.text, d.source); break;
    case "assistant":
      addMsg("ai", d.summary, d.kind, d.bg);
      detail.textContent = d.detail || d.summary || "—";
      flash(detail.parentElement); break;
    case "agent":
      actLog(`${d.agent.toUpperCase()} ▸ ${d.status}${d.task ? " · " + String(d.task).slice(0,60) : ""}${d.error ? " · " + d.error : ""}`,
             d.status === "error" ? "err" : "ok"); break;
    case "plan":
      actLog(`PLAN ▸ ${d.status === "step" ? `step ${d.i}/${d.total} → ${d.agent}` : d.status}`, "plan"); break;
    case "reminder":   actLog("⏰ REMINDER · " + d.text, "warn"); break;
    case "wake":       actLog("Wake word detected — session open", "ok"); break;
    case "log":        actLog(d.msg, "dim"); break;
  }
}

function setState(s){
  const label = (STATE_META[s] || [String(s).toUpperCase()])[0];
  document.body.dataset.state = s;
  $("pillText").textContent = label;
  $("orbLabel").textContent = label;
}

function addMsg(role, text, tag, bg){
  const el = document.createElement("div");
  el.className = "msg " + role + (bg ? " bg" : "");
  const t = new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
  el.innerHTML = `<span class="who">${role === "user" ? "BOSS" : "CRYOUS"}${tag ? " · " + tag : ""}</span><p></p><span class="ts mono">${t}</span>`;
  el.querySelector("p").textContent = text || "";
  feed.appendChild(el);
  feed.scrollTop = feed.scrollHeight;
  while (feed.children.length > 120) feed.firstChild.remove();
}

function actLog(text, cls){
  const li = document.createElement("li");
  li.className = cls || "";
  const t = new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit", second:"2-digit"});
  const ts = document.createElement("span");
  ts.className = "mono ts"; ts.textContent = t;
  li.appendChild(ts);
  li.appendChild(document.createTextNode(text));
  act.prepend(li);
  while (act.children.length > 40) act.lastChild.remove();
}

function flash(panel){ panel.classList.remove("flash"); void panel.offsetWidth; panel.classList.add("flash"); }

async function send(text){
  if (!text.trim()) return;
  $("typing").hidden = false;
  await fetch("/api/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({text})});
  setTimeout(() => $("typing").hidden = true, 1200);
}

$("composer").addEventListener("submit", e => {
  e.preventDefault();
  const v = $("input").value; $("input").value = "";
  send(v);
});

let powered = false;
$("powerBtn").addEventListener("click", async () => {
  powered = !powered;
  await fetch("/api/power", {method:"POST", headers:{"Content-Type":"application/json"},
                             body: JSON.stringify({action: powered ? "on" : "off"})});
  $("powerBtn").classList.toggle("off", !powered);
});

let micOn = true;
$("micBtn").addEventListener("click", async () => {
  micOn = !micOn;
  await fetch("/api/mic", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({on: micOn})});
  $("micBtn").textContent = micOn ? "MIC ON" : "MIC OFF";
  $("micBtn").classList.toggle("on", micOn);
});

$("sleepBtn").addEventListener("click", () =>
  fetch("/api/power", {method:"POST", headers:{"Content-Type":"application/json"},
                       body: JSON.stringify({action:"sleep", minutes:10})}));

$("copyOut").addEventListener("click", () => navigator.clipboard.writeText(detail.textContent));

const QUICK = ["System status report","Open Notepad","Take a screenshot","Volume up",
  "Research the latest AI news","Remind me in 10 minutes to stretch",
  "What time is it","Create a PDF report on AI trends"];
for (const q of QUICK){
  const b = document.createElement("button");
  b.className = "qbtn"; b.textContent = q;
  b.addEventListener("click", () => send(q));
  $("quick").appendChild(b);
}

function fmt(n){
  if (n >= 1e9) return (n/1e9).toFixed(2) + "B";
  if (n >= 1e6) return (n/1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n/1e3).toFixed(1) + "K";
  return String(n);
}

async function poll(){
  try{
    const r = await (await fetch("/api/stats")).json();
    $("cpuVal").textContent = r.cpu.toFixed(0) + "%";  $("cpuBar").style.width = r.cpu + "%";
    $("ramVal").textContent = r.ram.toFixed(0) + "%";  $("ramBar").style.width = r.ram + "%";
    const u = r.usage;
    $("tokVal").textContent = fmt(u.used) + " / " + fmt(u.budget);
    $("tokBar").style.width = Math.min(100, u.pct) + "%";
    $("provChips").innerHTML =
      r.providers.map(p => `<span class="chip">${p.name}</span>`).join("") +
      `<span class="chip dim">cache×${u.cache_hits}</span>`;
    if (r.state) setState(r.state);
    powered = r.enabled;
    $("powerBtn").classList.toggle("off", !powered);
  }catch(e){}
}

setInterval(() => $("clock").textContent =
  new Date().toLocaleTimeString([], {hour12:false}), 1000);
setInterval(poll, 2500);
connect(); poll();
addMsg("ai", "CRYOUS command deck online. Say “Cryous” to wake the voice engine, or type below.", "boot");