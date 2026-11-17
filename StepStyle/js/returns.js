document.addEventListener("DOMContentLoaded",async()=>{
 const msg=document.getElementById("returnMessage"),sel=document.getElementById("orderId"),list=document.getElementById("myReturns");
 async function api(url,opts={}){const r=await fetch(url,{credentials:"same-origin",headers:{"Content-Type":"application/json"},...opts});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||"Error");return d}
 try{const me=await api("/api/auth/me");if(!me.user){location.href="login.html";return}
 const orders=await api("/api/orders/mine");orders.forEach(o=>{const op=document.createElement("option");op.value=o.id;op.textContent=`${o.number} · ${o.status}`;sel.appendChild(op)});
 document.getElementById("returnForm").onsubmit=async e=>{e.preventDefault();msg.textContent="";try{const d=await api("/api/returns",{method:"POST",body:JSON.stringify({orderId:Number(sel.value),reason:e.target.reason.value,details:e.target.details.value})});msg.textContent=`Solicitud registrada. Folio de atención: DEV-${d.id}`;e.target.reset()}catch(x){msg.textContent=x.message}};
 const returns=await api("/api/returns/mine");
 list.innerHTML=returns.length?returns.map(r=>`<p>${r.number} — ${r.reason} — <strong>${r.status}</strong>${r.resolution?" — "+r.resolution:""}</p>`).join(""):"<p>Aún no has registrado solicitudes.</p>";
 }catch(e){msg.textContent=e.message}
});
