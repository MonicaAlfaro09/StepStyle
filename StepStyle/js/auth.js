document.addEventListener("DOMContentLoaded",async()=>{
 const mode=document.body.dataset.auth,card=document.getElementById("authCard");
 const api=async(url,options={})=>{const r=await fetch(url,{credentials:"same-origin",headers:{"Content-Type":"application/json",...(options.headers||{})},...options});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||"Ocurrió un error.");return d};
 function passwordScore(v){let s=0;if(v.length>=10)s++;if(/[A-Z]/.test(v))s++;if(/[0-9]/.test(v))s++;if(/[^A-Za-z0-9]/.test(v))s++;return s}
 if(mode==="signup"){
 card.innerHTML=`<p class="kicker">STEPSTYLE MEMBER</p><h1>Crea tu cuenta</h1><p class="auth-lead">Tus datos se guardan en el servidor de demostración.</p><form id="signupForm" class="form-stack" novalidate><label>Nombre<input name="name" required maxlength="100" autocomplete="name"></label><label>Correo<input name="email" type="email" required autocomplete="email"></label><label>Contraseña<input name="password" type="password" required minlength="10" autocomplete="new-password"><small>Al menos 10 caracteres, mayúscula, número y símbolo recomendado.</small></label><label>Confirmar contraseña<input name="confirm" type="password" required></label><div id="authError" class="form-error" role="alert"></div><button class="button button-dark full-width tall">Crear cuenta</button></form><p class="auth-switch">¿Ya tienes cuenta? <a href="login.html">Inicia sesión</a></p>`;
 const f=document.getElementById("signupForm");f.onsubmit=async e=>{e.preventDefault();const err=document.getElementById("authError");err.textContent="";
 if(!f.checkValidity()){f.reportValidity();return}if(f.password.value!==f.confirm.value){err.textContent="Las contraseñas no coinciden.";return}
 try{const d=await api("/api/auth/register",{method:"POST",body:JSON.stringify({name:f.name.value,email:f.email.value,password:f.password.value})});StepStyle.write(StepStyle.KEYS.session,d.user);location.href=sessionStorage.getItem("stepstyle_redirect")||"perfil.html"}catch(x){err.textContent=x.message}};
 }else if(mode==="login"){
 const required=new URLSearchParams(location.search).has("required");
 card.innerHTML=`<p class="kicker">BIENVENIDA DE NUEVO</p><h1>Iniciar sesión</h1>${required?'<div class="notice">Debes iniciar sesión para continuar al checkout.</div>':''}<form id="loginForm" class="form-stack"><label>Correo<input name="email" type="email" required autocomplete="email"></label><label>Contraseña<input name="password" type="password" required autocomplete="current-password"></label><div id="authError" class="form-error" role="alert"></div><button class="button button-dark full-width tall">Entrar</button></form><p class="auth-switch">¿No tienes cuenta? <a href="registro.html">Crear cuenta</a></p>`;
 const f=document.getElementById("loginForm");f.onsubmit=async e=>{e.preventDefault();const err=document.getElementById("authError");err.textContent="";try{const d=await api("/api/auth/login",{method:"POST",body:JSON.stringify({email:f.email.value,password:f.password.value})});StepStyle.write(StepStyle.KEYS.session,d.user);const next=sessionStorage.getItem("stepstyle_redirect")||(d.user.role==="admin"?"admin.html":"perfil.html");sessionStorage.removeItem("stepstyle_redirect");location.href=next}catch(x){err.textContent=x.message}};
 }else{
 let me;try{me=(await api("/api/auth/me")).user}catch(e){}
 if(!me){location.href="login.html";return}
 StepStyle.write(StepStyle.KEYS.session,me);
 const orders=await api("/api/orders/mine").catch(()=>[]);
 card.classList.add("profile-card");
 card.innerHTML=`<p class="kicker">MI CUENTA</p><h1>${escapeHtml(me.name)}</h1><p>${escapeHtml(me.email)}</p><div class="profile-actions"><a class="button button-dark" href="favoritos.html">Ver favoritos</a><a class="button button-outline" href="carrito.html">Ver carrito</a>${me.role==="admin"?'<a class="button button-outline" href="admin.html">Administrar tienda</a>':''}</div><h2>Mis pedidos</h2>${orders.length?orders.map(o=>`<div class="order-row"><strong>${escapeHtml(o.number)}</strong><span>${new Date(o.created_at).toLocaleDateString("es-MX")}</span><b>${StepStyle.money(o.total)}</b><span>${escapeHtml(o.status)}</span></div>`).join(""):'<p class="muted">Aún no hay pedidos registrados.</p>'}<button id="profileLogout" class="text-button">Cerrar sesión</button>`;
 document.getElementById("profileLogout").onclick=async()=>{await api("/api/auth/logout",{method:"POST"}).catch(()=>{});localStorage.removeItem(StepStyle.KEYS.session);location.href="index.html"};
 }
 function escapeHtml(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
});
