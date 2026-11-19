document.addEventListener("DOMContentLoaded",()=>{
 if(!StepStyle.session()){sessionStorage.setItem("stepstyle_redirect","checkout.html");location.href="login.html?required=1";return}
 if(!StepStyle.cart().length){location.href="carrito.html";return}
 const f=document.getElementById("checkoutForm"),s=StepStyle.session();
 f.fullName.value=s.name;f.email.value=s.email;
 let shipping=null,coupon=null;
 const money=StepStyle.money;
 function destination(){
  const country=f.country?.value||"México",state=(f.state.value||"").trim().toLowerCase(),city=(f.city.value||"").trim().toLowerCase();
  const borderCities=["nuevo laredo","reynosa","matamoros","rio bravo","miguel aleman","camargo","guerrero"];
  const border=country==="México" && (borderCities.some(c=>city.includes(c)) || ["baja california","sonora"].includes(state) && /san luis rio colorado|nogales|agua prieta|naco|cananea|general plutarco/.test(city));
  const rate=country!=="México"?0:(border?.08:.16);
  let fee=country!=="México"?499:(state==="tamaulipas"?99:149);
  if(country==="México" && StepStyle.subtotal()>=2500)fee=0;
  const kind=country!=="México"?"Envío internacional":state==="tamaulipas"?"Envío local":"Envío nacional";
  return {country,rate,fee,kind,border};
 }
 function totals(){
  const sub=StepStyle.subtotal(),disc=coupon?coupon.amount:0,base=Math.max(0,sub-disc),dest=destination();
  shipping=dest.fee;
  const tax=Math.round(base*dest.rate*100)/100,total=base+tax+dest.fee;
  document.getElementById("sumSubtotal").textContent=money(sub);
  document.getElementById("sumDiscount").textContent=disc?`-${money(disc)}`:money(0);
  document.getElementById("sumTax").textContent=money(tax);
  document.getElementById("taxLabel").textContent=dest.rate===0?"Impuestos de importación":"IVA estimado ("+Math.round(dest.rate*100)+"%)";
  document.getElementById("taxNote").textContent=dest.rate===0?"No se cobra IVA mexicano en este cálculo. El país de destino puede cobrar aranceles o impuestos de importación al recibir el paquete.":dest.border?"Se estima IVA fronterizo del 8%; la tasa definitiva depende de la localidad y requisitos fiscales.":"Se estima IVA del 16% para entregas dentro de México.";
  document.getElementById("sumShipping").textContent=dest.fee===0?"Gratis":money(dest.fee);
  document.getElementById("sumTotal").textContent=money(total);
  return{sub,disc,tax,ship:dest.fee,total,destination:dest};
 }
 function renderItems(){document.getElementById("checkoutItems").innerHTML=StepStyle.cart().map(i=>{const p=StepStyle.product(i.id);return `<div class="mini-order"><img src="${p.image}" alt=""><span><strong>${p.name}</strong><small>Talla ${i.size} · ${i.quantity} pza.</small></span><b>${money(StepStyle.price(p)*i.quantity)}</b></div>`}).join("")}
 function showStep(n){
  document.querySelectorAll(".checkout-step").forEach(x=>x.classList.toggle("active",Number(x.dataset.step)===n));
  document.querySelectorAll("[data-step-dot]").forEach(x=>x.classList.toggle("active",Number(x.dataset.stepDot)<=n));
  if(n===3){const t=totals();document.getElementById("reviewInfo").innerHTML=`<div class="review-card"><strong>Enviar a</strong><p>${f.fullName.value}<br>${f.address.value}, ${f.city.value}, ${f.state.value} ${f.zip.value}, ${f.country.value}</p><strong>Método de pago</strong><p>Tarjeta (validación de prueba; sin cargo real)</p><strong>Total</strong><p>${money(t.total)}</p></div>`}
 }
 function validateStep(n){
  const err=document.getElementById("checkoutError");err.textContent="";
  if(n===1){
   for(const name of ["fullName","email","address","city","state","zip","country","phone"]){const el=f[name];if(!el.checkValidity()){el.classList.add("invalid");err.textContent="Revisa los campos marcados en rojo.";el.reportValidity();return false}else el.classList.remove("invalid")}
   if(!/^\d{5}$/.test(f.zip.value)){err.textContent="El código postal debe tener 5 dígitos.";return false}
   totals();
  }
  if(n===2){
   const digits=f.card.value.replace(/\D/g,""),exp=f.expiry.value.trim(),cvv=f.cvv.value.trim();
   const [mm,yy]=exp.split("/").map(Number);
   if(f.cardName.value.trim().length<3||digits.length!==16||!/^(0[1-9]|1[0-2])\/\d{2}$/.test(exp)||!cvv.match(/^\d{3,4}$/)||!mm||yy<0){
    err.textContent="Completa el titular, los 16 dígitos, vencimiento MM/AA y CVV de la tarjeta.";[f.cardName,f.card,f.expiry,f.cvv].forEach(x=>x.classList.add("invalid"));return false;
   }
   [f.cardName,f.card,f.expiry,f.cvv].forEach(x=>x.classList.remove("invalid"));
  }
  return true;
 }
 document.querySelectorAll("[data-next]").forEach(b=>b.onclick=()=>{const current=Number(b.closest("[data-step]").dataset.step);if(validateStep(current))showStep(Number(b.dataset.next))});
 document.querySelectorAll("[data-prev]").forEach(b=>b.onclick=()=>showStep(Number(b.dataset.prev)));
 f.zip.addEventListener("input",()=>{if(f.zip.value.length===5)totals();document.getElementById("shippingStatus").textContent=f.zip.value.length===5?("Costo actualizado: "+destination().kind+"."):"Ingresa un código postal de 5 dígitos."});
 ["country","state","city"].forEach(k=>f[k].addEventListener("change",()=>{totals();document.getElementById("shippingStatus").textContent="Destino actualizado: "+destination().kind+"."}));
 f.card.addEventListener("input",e=>{let v=e.target.value.replace(/\D/g,"").slice(0,16);e.target.value=v.replace(/(.{4})/g,"$1 ").trim()});
 f.expiry.addEventListener("input",e=>{let v=e.target.value.replace(/\D/g,"").slice(0,4);e.target.value=v.length>2?v.slice(0,2)+"/"+v.slice(2):v});
 f.cvv.addEventListener("input",e=>e.target.value=e.target.value.replace(/\D/g,"").slice(0,4));
 document.getElementById("applyCoupon").onclick=()=>{const c=StepStyle.coupon(document.getElementById("couponCode").value,StepStyle.subtotal());if(!c){coupon=null;StepStyle.toast("Cupón no válido")}else{coupon=c;StepStyle.toast(`${c.code}: ${c.label}`)}totals()};
 f.onsubmit=e=>{e.preventDefault();if(!validateStep(1)){showStep(1);return}if(!validateStep(2)){showStep(2);return}if(!f.acceptLegal.checked){document.getElementById("checkoutError").textContent="Debes aceptar los Términos y Condiciones y el Aviso de Privacidad para continuar.";f.acceptLegal.focus();return}};
 renderItems();totals();
});