// URL pública del backend en Render. Si Render asigna otra URL, cámbiala solo aquí.
const STEPSTYLE_REMOTE_API='https://stepstyle-api-i381.onrender.com';
// En GitHub Pages se usa la API remota; en local (python3 backend/server.py) se usa el mismo servidor.
const STEPSTYLE_API_BASE=(location.hostname.endsWith('github.io')||location.protocol==='file:'?STEPSTYLE_REMOTE_API:'')+'/api';

window.StepAPI={
 base:STEPSTYLE_API_BASE,
 token:()=>sessionStorage.getItem('stepstyle_token'),
 async call(path,method='GET',data){
  let r;
  try{r=await fetch(this.base+path,{method,headers:{'Content-Type':'application/json',...(this.token()?{'Authorization':'Bearer '+this.token()}:{})},...(data?{body:JSON.stringify(data)}:{})})}
  catch(e){throw Error('No se pudo conectar con el servidor. Si es el primer acceso del día, espera un minuto e inténtalo de nuevo.')}
  let out={};try{out=await r.json()}catch(e){}
  if(r.status===403&&out.error==='Inicia sesión'){sessionStorage.removeItem('stepstyle_token')}
  if(!r.ok)throw Error(out.error||'Error de solicitud ('+r.status+')');
  return out},
 async login(email,password){const d=await this.call('/auth/login','POST',{email,password});sessionStorage.setItem('stepstyle_token',d.token);StepStyle.write(StepStyle.KEYS.session,d.user);return d},
 logout(){this.call('/auth/logout','POST').catch(()=>{});sessionStorage.removeItem('stepstyle_token');localStorage.removeItem(StepStyle.KEYS.session)}
};

fetch(STEPSTYLE_API_BASE+'/products').then(r=>r.ok?r.json():null).then(p=>{if(!Array.isArray(p)||!p.length)return;window.PRODUCTS=p;document.dispatchEvent(new Event('stepstyle:products'));}).catch(()=>{});
