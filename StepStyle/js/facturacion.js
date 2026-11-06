document.addEventListener("DOMContentLoaded",()=>{
  const form=document.getElementById("invoiceForm");
  form?.addEventListener("submit",e=>{
    e.preventDefault();
    if(!form.reportValidity())return;
    const data=new FormData(form);
    const lines=[
      "STEPSTYLE - SOLICITUD DE FACTURACIÓN",
      "Solicitud de información; no constituye un CFDI.",
      "",
      ...["folio","razon","rfc","correo","detalle"].map(k=>k.toUpperCase()+": "+String(data.get(k)||"")),
      "",
      ""
    ];
    const url=URL.createObjectURL(new Blob([lines.join("\\n")],{type:"text/plain;charset=utf-8"}));
    const a=document.createElement("a");a.href=url;a.download="StepStyle_solicitud_facturacion.txt";
    document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
    document.getElementById("invoiceResult").textContent="Solicitud descargada. No se ha enviado.";
  });
});