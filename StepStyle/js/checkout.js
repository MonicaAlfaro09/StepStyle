document.addEventListener("DOMContentLoaded",async()=>{await StepStyle.syncProducts();
 const api=async(url,options={})=>{const r=await fetch(url,{credentials:"same-origin",headers:{"Content-Type":"application/json",...(options.headers||{})},...options});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||"Ocurrió un error.");return d};
 const me=await api("/api/auth/me").catch(()=>({user:null}));
 if(!me.user){sessionStorage.setItem("stepstyle_redirect","checkout.html");location.href="login.html?required=1";return}
 if(!StepStyle.cart().length){location.href="carrito.html";return}
 const f=document.getElementById("checkoutForm"),s=me.user;f.fullName.value=s.name;f.email.value=s.email;
 let shipping=null;
 function totals(){const sub=StepStyle.subtotal(),tax=Math.round(sub*.16*100)/100,ship=shipping??0,total=sub+tax+ship;
 document.getElementById("sumSubtotal").textContent=StepStyle.money(sub);document.getElementById("sumDiscount").textContent=StepStyle.money(0);
 document.getElementById("sumTax").textContent=StepStyle.money(tax);document.getElementById("sumShipping").textContent=shipping===null?"Por calcular":ship===0?"Gratis":StepStyle.money(ship);
 document.getElementById("sumTotal").textContent=StepStyle.money(total);return{sub,tax,ship,total}}
 function renderItems(){document.getElementById("checkoutItems").innerHTML=StepStyle.cart().map(i=>{const p=StepStyle.product(i.id);return `<div class="mini-order"><img src="${p.image}" alt=""><span><strong>${p.name}</strong><small>Talla ${i.size} · ${i.quantity} pza.</small></span><b>${StepStyle.money(StepStyle.price(p)*i.quantity)}</b></div>`}).join("")}
 function showStep(n){document.querySelectorAll(".checkout-step").forEach(x=>x.classList.toggle("active",Number(x.dataset.step)===n));document.querySelectorAll("[data-step-dot]").forEach(x=>x.classList.toggle("active",Number(x.dataset.stepDot)<=n));if(n===3){const t=totals();document.getElementById("reviewInfo").innerHTML=`<div class="review-card"><strong>Enviar a</strong><p>${f.fullName.value}<br>${f.address.value}, ${f.city.value}, ${f.state.value} ${f.zip.value}</p><strong>Pago</strong><p>${f.payment.value}</p><strong>Total estimado</strong><p>${StepStyle.money(t.total)}</p></div>`}}
 function validateStep(n){const err=document.getElementById("checkoutError");err.textContent="";
 if(n===1){for(const name of ["fullName","email","address","city","state","zip","phone"]){const el=f.elements[name];if(!el.checkValidity()){el.classList.add("invalid");err.textContent="Revisa los campos marcados.";el.reportValidity();return false}else el.classList.remove("invalid")}
 const sub=StepStyle.subtotal(),zip=Number(f.zip.value);shipping=sub>=2500?0:(zip>=88000&&zip<=88999?99:169);totals();}
 if(n===3&&!f.acceptTerms.checked){err.textContent="Debes aceptar los términos y el aviso de privacidad.";return false}return true}
 document.querySelectorAll("[data-next]").forEach(b=>b.onclick=()=>{const current=Number(b.closest("[data-step]").dataset.step);if(validateStep(current))showStep(Number(b.dataset.next))});
 document.querySelectorAll("[data-prev]").forEach(b=>b.onclick=()=>showStep(Number(b.dataset.prev)));
 f.zip.addEventListener("input",()=>{shipping=null;if(/^\d{5}$/.test(f.zip.value)){const n=Number(f.zip.value);shipping=StepStyle.subtotal()>=2500?0:(n>=88000&&n<=88999?99:169)}document.getElementById("shippingStatus").textContent=shipping===null?"Ingresa 5 dígitos.":shipping===0?"Envío gratis por superar $2,500.":`Envío estimado: ${StepStyle.money(shipping)}`;totals()});
 f.onsubmit=async e=>{e.preventDefault();if(!validateStep(1)||!validateStep(3))return;
 const button=document.getElementById("payButton"),overlay=document.getElementById("processing");button.disabled=true;overlay.classList.add("show");
 try{
 const result=await api("/api/orders",{method:"POST",body:JSON.stringify({
 items:StepStyle.cart(),customer:{name:f.fullName.value,email:f.email.value,address:f.address.value,city:f.city.value,state:f.state.value,zip:f.zip.value,phone:f.phone.value},
 paymentMethod:f.payment.value,acceptedTerms:f.acceptTerms.checked
 })});
 const order=result.order;StepStyle.write(StepStyle.KEYS.lastOrder,{number:order.number,date:new Date().toISOString(),customer:{name:f.fullName.value,email:f.email.value},payment:f.payment.value,total:order.total,items:StepStyle.cart()});
 StepStyle.setCart([]);location.href="confirmacion.html";
 }catch(err){document.getElementById("checkoutError").textContent=err.message;button.disabled=false;overlay.classList.remove("show")}
 };
 renderItems();totals();
});
