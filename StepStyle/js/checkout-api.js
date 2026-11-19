document.addEventListener('DOMContentLoaded',()=>{
 const f=document.getElementById('checkoutForm');if(!f)return;
 let busy=false;
 f.addEventListener('submit',async e=>{
 e.preventDefault();e.stopImmediatePropagation();
 if(busy)return;
 if(!StepAPI.token()){location.href='login.html';return}
 const names=['fullName','email','address','city','state','zip','country','phone'];
 const digits=f.card.value.replace(/\D/g,'');
 if(f.cardName.value.trim().length<3||digits.length!==16||!/^(0[1-9]|1[0-2])\/\d{2}$/.test(f.expiry.value)||!/^\d{3,4}$/.test(f.cvv.value)){
  document.getElementById('checkoutError').textContent='Completa correctamente los datos de la tarjeta.';return;
 }
 if(names.some(k=>!f[k].checkValidity())){f.reportValidity();return}
 if(!f.acceptLegal.checked){document.getElementById('checkoutError').textContent='Debes aceptar los términos y el aviso de privacidad.';return}
 const items=StepStyle.cart().map(x=>({id:x.id,quantity:x.quantity}));
 const shipping={name:f.fullName.value,email:f.email.value,address:f.address.value,city:f.city.value,state:f.state.value,zip:f.zip.value,country:f.country.value,phone:f.phone.value};
 const key=crypto.randomUUID();busy=true;
 try{const d=await StepAPI.call('/orders','POST',{items,shipping,payment:'Tarjeta',accept_terms:true,coupon:document.getElementById('couponCode')?.value.trim()||'',idempotency_key:key});
 StepStyle.write(StepStyle.KEYS.lastOrder,{number:d.folio,date:d.date,customer:shipping,items:StepStyle.cart(),total:d.total,subtotal:d.subtotal,tax:d.tax,shipping:d.shipping,discount:d.discount,payment:'Tarjeta'});StepStyle.setCart([]);location.href='confirmacion.html';
 }catch(x){document.getElementById('checkoutError').textContent=x.message;busy=false}
 },true);
});