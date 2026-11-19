document.addEventListener('DOMContentLoaded',()=>{
 const err=document.getElementById('adminError'),content=document.getElementById('adminContent'),denied=document.getElementById('adminDenied');
 const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const parseShipping=v=>{try{return typeof v==='string'?JSON.parse(v):v||{}}catch{return {}}};
 async function render(){
  try{
   const u=await StepAPI.call('/me');
   if(u.role!=='admin'){content.style.display='none';denied.style.display='block';denied.querySelector('h1').textContent='Sin permisos';return}
   denied.style.display='none';content.style.display='block';
   const [p,o,r,report]=await Promise.all(['/admin/products','/admin/orders','/admin/returns','/admin/reports'].map(x=>StepAPI.call(x)));
   document.getElementById('reports').textContent=`Pedidos: ${report.orders} · Ventas: ${StepStyle.money(report.sales_cents/100)} · Stock bajo: ${report.low_stock} · Devoluciones: ${report.returns}`;
   document.getElementById('adminProducts').innerHTML=p.map(x=>`<div class="order-row">${safe(x.id)} · ${safe(x.name)} · ${StepStyle.money(x.price_cents/100)} · Stock: ${x.stock} <button class="button button-outline compact" data-product="${safe(x.id)}">Editar</button></div>`).join('')||'<p>No hay productos.</p>';
   document.getElementById('adminOrders').innerHTML=o.map(x=>{
    const sh=parseShipping(x.shipping),next=['pendiente','preparando','enviado','entregado','cancelado'];
    return `<article class="admin-record"><div><strong>${safe(x.folio)}</strong> · ${safe(x.status)} · ${StepStyle.money(x.total_cents/100)}</div><p><b>Cliente:</b> ${safe(x.customer_name)} (${safe(x.customer_email)})</p><p><b>Destino:</b> ${safe(sh.address)}, ${safe(sh.city)}, ${safe(sh.state)}, ${safe(sh.zip)}, ${safe(sh.country||'México')}</p><p><b>Impuestos:</b> ${StepStyle.money(x.tax_cents/100)} · <b>Envío:</b> ${StepStyle.money(x.shipping_cents/100)}</p><button class="button button-outline compact" data-order-detail="${x.id}">Ver artículos</button> <select data-order="${x.id}" aria-label="Cambiar estado del pedido"><option value="">Cambiar estado</option>${['preparando','enviado','entregado','cancelado'].map(y=>`<option value="${y}">${y}</option>`).join('')}</select><div id="order-items-${x.id}" class="admin-order-items"></div></article>`
   }).join('')||'<p>No hay pedidos todavía.</p>';
   document.getElementById('adminReturns').innerHTML=r.map(x=>`<article class="admin-record"><strong>Solicitud #${x.id}</strong> · ${safe(x.status)}<p><b>Cliente:</b> ${safe(x.customer_name)} (${safe(x.customer_email)})</p><p><b>Pedido / paquete:</b> ${safe(x.folio)} (ID ${x.order_id})</p><p><b>Motivo de devolución:</b> ${safe(x.reason)}</p><p><b>Fecha:</b> ${safe(x.created_at)}</p>${x.status==='solicitada'?`<button class="button button-dark compact" data-return="${x.id}" data-status="aprobada">Aprobar</button> <button class="button button-outline compact" data-return="${x.id}" data-status="rechazada">Rechazar</button>`:''}</article>`).join('')||'<p>No hay solicitudes de devolución.</p>';
   err.textContent='';
  }catch(e){content.style.display='none';denied.style.display='block';denied.querySelector('h1').textContent='Sin permisos';denied.querySelector('p').textContent='Esta sección está disponible únicamente para cuentas administradoras. Inicia sesión con una cuenta autorizada.'}
 }
 document.getElementById('newProduct').onsubmit=async e=>{e.preventDefault();const f=e.target;try{await StepAPI.call('/admin/products','POST',{id:f.id.value,name:f.name.value,category:f.category.value,price_cents:Math.round(Number(f.price.value)*100),stock:Number(f.stock.value)});f.reset();render()}catch(x){err.textContent=x.message}};
 document.body.addEventListener('click',async e=>{
  const b=e.target.closest('[data-product],[data-return],[data-order-detail]');if(!b)return;
  try{
   if(b.dataset.product){const stock=prompt('Nueva existencia');if(stock===null)return;const n=Number(stock);if(!Number.isInteger(n)||n<0)throw Error('La existencia debe ser un número entero igual o mayor a cero.');await StepAPI.call('/admin/products/'+b.dataset.product,'PATCH',{stock:n});render()}
   else if(b.dataset.return){await StepAPI.call('/admin/returns/'+b.dataset.return,'PATCH',{status:b.dataset.status});render()}
   else {const d=await StepAPI.call('/admin/orders/'+b.dataset.orderDetail);document.getElementById('order-items-'+b.dataset.orderDetail).innerHTML='<p><b>Artículos:</b> '+(d.items||[]).map(i=>`${safe(i.name)} · ${i.quantity} pza. · ${StepStyle.money(i.unit_price_cents/100)}`).join(' | ')+'</p>'}
  }catch(x){err.textContent=x.message}
 });
 document.body.addEventListener('change',async e=>{const b=e.target.closest('[data-order]');if(!b||!b.value)return;try{await StepAPI.call('/admin/orders/'+b.dataset.order,'PATCH',{status:b.value});render()}catch(x){err.textContent=x.message}});
 render();
});