window.StepAPI={
 token:()=>sessionStorage.getItem('stepstyle_token'),
 async call(path,method='GET',data){const r=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json',...(this.token()?{'Authorization':'Bearer '+this.token()}:{})},...(data?{body:JSON.stringify(data)}:{})});const out=await r.json();if(!r.ok)throw Error(out.error||'Error de solicitud');return out},
 async login(email,password){const d=await this.call('/auth/login','POST',{email,password});sessionStorage.setItem('stepstyle_token',d.token);StepStyle.write(StepStyle.KEYS.session,d.user);return d},
 logout(){this.call('/auth/logout','POST').catch(()=>{});sessionStorage.removeItem('stepstyle_token');localStorage.removeItem(StepStyle.KEYS.session)}
};

fetch('/api/products').then(r=>r.ok?r.json():null).then(p=>{if(!p)return;window.PRODUCTS=p;document.dispatchEvent(new Event('stepstyle:products')); }).catch(()=>{});
