/* Area 33 approved-image gallery. Uses ONLY images from validated public catalog records.
   No requests, thumbnails or placeholders from private distributor/media data.
   Text-only records never reach this component. No auto-download or analytics. */
"use strict";

export function clampGalleryZoom(value){
  return Number.isFinite(value)?Math.min(4,Math.max(1,value)):1;
}
export function galleryPointerPercent(clientX,clientY,rect){
  if(!rect||rect.width<=0||rect.height<=0)return {x:50,y:50};
  const clamp=n=>Math.max(0,Math.min(100,n));
  return {x:clamp((clientX-rect.left)/rect.width*100),
          y:clamp((clientY-rect.top)/rect.height*100)};
}
export function galleryAllowed(item){
  return Boolean(item&&item.presentationMode!=="text_only"&&
    Array.isArray(item.images)&&item.images.length>0&&item.images.length<=8&&
    item.images.every(image=>image&&typeof image.url==="string"&&
      image.url.startsWith("https://")&&typeof image.alt==="string"&&image.alt.trim()));
}
function el(tag,className,text){
  const node=document.createElement(tag);
  if(className)node.className=className;
  if(text!==undefined)node.textContent=text;
  return node;
}
function button(label,cls,click){
  const node=el("button",cls,label);
  node.type="button";
  node.addEventListener("click",click);
  return node;
}
function approvedImg(data){
  const image=el("img");
  image.src=data.url;
  image.alt=data.alt;
  image.referrerPolicy="no-referrer";
  image.decoding="async";
  image.draggable=false;
  return image;
}
function pinPan(stage,zoom,pan){
  const x=Math.max(0,stage.clientWidth*(zoom-1)/2);
  const y=Math.max(0,stage.clientHeight*(zoom-1)/2);
  return {x:Math.max(-x,Math.min(x,pan.x)),
          y:Math.max(-y,Math.min(y,pan.y))};
}
function separation(a,b){return Math.hypot(a.x-b.x,a.y-b.y);}

/* Launches a native modal above the detail dialog; has keyboard zoom/navigation
   and mobile pointer pinch/pan/swipe. It is removed completely on close. */
function openImageViewer(images,selected,productTitle){
  const dlg=el("dialog","approved-gallery-lightbox");
  dlg.setAttribute("aria-label","Full-size approved photo viewer for "+productTitle);
  const shell=el("div","gallery-lightbox-shell");
  const toolbar=el("div","gallery-lightbox-toolbar");
  const heading=el("strong","",productTitle);
  const counter=el("span","gallery-count");
  const close=button("Close ×","gallery-close",()=>dlg.close());
  close.setAttribute("aria-label","Close photo viewer");
  toolbar.append(heading,counter,close);
  const stage=el("div","gallery-lightbox-stage");
  stage.setAttribute("aria-label","Product photograph. Pinch or use controls to zoom.");
  const full=approvedImg(images[selected]);
  const loadMessage=el("p","gallery-image-error");
  loadMessage.setAttribute("role","status");
  loadMessage.hidden=true;
  full.addEventListener("error",()=>{
    full.hidden=true;loadMessage.textContent="This approved image could not load. Choose another view.";
    loadMessage.hidden=false;
  });
  full.addEventListener("load",()=>{full.hidden=false;loadMessage.hidden=true;});
  stage.append(full,loadMessage);
  const controls=el("div","gallery-lightbox-controls");
  const prev=button("← Previous","",()=>choose(selected-1));
  const next=button("Next →","",()=>choose(selected+1));
  const minus=button("−","",()=>setZoom(zoom-.5));
  minus.setAttribute("aria-label","Zoom out");
  const percent=el("output","gallery-zoom-label","100%");
  const plus=button("+","",()=>setZoom(zoom+.5));
  plus.setAttribute("aria-label","Zoom in");
  const reset=button("Reset","",()=>{pan={x:0,y:0};setZoom(1);});
  controls.append(prev,minus,percent,plus,reset,next);
  const hint=el("p","gallery-gesture-hint","Swipe to change views; pinch or use + / − to zoom. Press Esc to close.");
  shell.append(toolbar,stage,controls,hint);
  dlg.append(shell);
  document.body.append(dlg);
  let zoom=1,pan={x:0,y:0};
  let pointers=new Map(),gesture=null;

  function apply(){
    pan=pinPan(stage,zoom,pan);
    full.style.transform="translate("+pan.x+"px,"+pan.y+"px) scale("+zoom+")";
    percent.textContent=Math.round(zoom*100)+"%";
    minus.disabled=zoom<=1;
    plus.disabled=zoom>=4;
    reset.disabled=zoom===1&&pan.x===0&&pan.y===0;
  }
  function setZoom(next){
    zoom=clampGalleryZoom(next);
    if(zoom===1)pan={x:0,y:0};
    apply();
  }
  function choose(nextIndex){
    if(nextIndex<0||nextIndex>=images.length)return;
    selected=nextIndex;
    full.hidden=false;
    loadMessage.hidden=true;
    full.src=images[selected].url;
    full.alt=images[selected].alt;
    counter.textContent=(selected+1)+" of "+images.length;
    prev.disabled=selected===0;
    next.disabled=selected===images.length-1;
    zoom=1;pan={x:0,y:0};pointers.clear();gesture=null;apply();
  }
  stage.addEventListener("pointerdown",event=>{
    if(event.pointerType==="mouse"&&event.button!==0)return;
    const pos={x:event.clientX,y:event.clientY};
    pointers.set(event.pointerId,pos);
    stage.setPointerCapture?.(event.pointerId);
    if(pointers.size===2){
      const [a,b]=[...pointers.values()];
      gesture={kind:"pinch",dist:Math.max(1,separation(a,b)),zoom,pan:{...pan}};
    }else if(pointers.size===1){
      gesture={kind:"move",start:pos,last:pos,initialPan:{...pan},moved:false};
    }
  });
  stage.addEventListener("pointermove",event=>{
    if(!pointers.has(event.pointerId))return;
    const point={x:event.clientX,y:event.clientY};
    pointers.set(event.pointerId,point);
    if(pointers.size===2&&gesture?.kind==="pinch"){
      const [a,b]=[...pointers.values()];
      setZoom(gesture.zoom*separation(a,b)/gesture.dist);
      return;
    }
    if(pointers.size===1&&gesture?.kind==="move"){
      const dx=point.x-gesture.start.x,dy=point.y-gesture.start.y;
      gesture.last=point;
      if(Math.hypot(dx,dy)>8)gesture.moved=true;
      if(zoom>1){pan={x:gesture.initialPan.x+dx,y:gesture.initialPan.y+dy};apply();}
    }
  });
  function pointerFinish(event){
    const g=gesture;
    if(!pointers.has(event.pointerId))return;
    const final={x:event.clientX,y:event.clientY};
    pointers.delete(event.pointerId);
    if(pointers.size===0){
      if(g?.kind==="move"&&zoom===1){
        const dx=final.x-g.start.x,dy=final.y-g.start.y;
        if(Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy)*1.4)choose(selected+(dx<0?1:-1));
      }
      gesture=null;
    }else if(pointers.size===1){
      const only=[...pointers.values()][0];
      gesture={kind:"move",start:only,last:only,initialPan:{...pan},moved:false};
    }
  }
  stage.addEventListener("pointerup",pointerFinish);
  stage.addEventListener("pointercancel",pointerFinish);
  dlg.addEventListener("keydown",event=>{
    if(event.key==="ArrowRight"){event.preventDefault();choose(selected+1);}
    if(event.key==="ArrowLeft"){event.preventDefault();choose(selected-1);}
    if(event.key==="+"||event.key==="="){event.preventDefault();setZoom(zoom+.5);}
    if(event.key==="-"){event.preventDefault();setZoom(zoom-.5);}
    if(event.key==="0"){event.preventDefault();pan={x:0,y:0};setZoom(1);}
  });
  dlg.addEventListener("click",event=>{
    if(event.target===dlg)dlg.close();
  });
  dlg.addEventListener("close",()=>dlg.remove(),{once:true});
  choose(selected);
  dlg.showModal();
  close.focus();
}

export function createApprovedGallery(item){
  if(!galleryAllowed(item))return null;
  const images=item.images;
  const title=[item.manufacturer,item.model,item.variant].filter(Boolean).join(" ");
  const gallery=el("section","approved-product-gallery");
  gallery.setAttribute("aria-label","Approved product photos for "+title);
  const stage=button("","gallery-stage",()=>openImageViewer(images,current,title));
  stage.setAttribute("aria-label","Expand photo 1 of "+images.length+" for "+title);
  const main=approvedImg(images[0]);
  main.className="gallery-hero";
  const fallback=el("span","gallery-image-error","This approved photo could not load.");
  fallback.hidden=true;
  main.addEventListener("error",()=>{main.hidden=true;fallback.hidden=false;stage.classList.remove("hover-zooming");});
  main.addEventListener("load",()=>{main.hidden=false;fallback.hidden=true;});
  const zoomLabel=el("span","gallery-hover-label","Hover to zoom · Click to expand");
  stage.append(main,fallback,zoomLabel);
  const count=el("p","gallery-caption","Approved product photograph · 1 of "+images.length);
  const thumbs=el("div","gallery-thumbnails");
  const controls=[];
  let current=0;
  function pick(i){
    if(i<0||i>=images.length)return;
    current=i;
    main.hidden=false;fallback.hidden=true;
    main.src=images[i].url;
    main.alt=images[i].alt;
    stage.setAttribute("aria-label","Expand photo "+(i+1)+" of "+images.length+" for "+title);
    count.textContent="Approved product photograph · "+(i+1)+" of "+images.length;
    controls.forEach((b,index)=>{b.setAttribute("aria-pressed",String(index===i));});
    stage.classList.remove("hover-zooming");
    main.style.removeProperty("transform-origin");
  }
  if(images.length>1){
    images.forEach((image,index)=>{
      const thumb=button("","gallery-thumb",()=>pick(index));
      thumb.setAttribute("aria-label","View approved photo "+(index+1)+" of "+images.length);
      const preview=approvedImg(image);
      preview.alt="";
      preview.loading="lazy";
      const label=el("span","gallery-thumb-count",String(index+1));
      thumb.append(preview,label);
      controls.push(thumb);
      thumbs.append(thumb);
    });
  }
  stage.addEventListener("pointerenter",event=>{
    if(event.pointerType==="mouse"&&window.matchMedia("(hover: hover) and (pointer: fine)").matches&&!main.hidden)
      stage.classList.add("hover-zooming");
  });
  stage.addEventListener("pointermove",event=>{
    if(!stage.classList.contains("hover-zooming"))return;
    const p=galleryPointerPercent(event.clientX,event.clientY,stage.getBoundingClientRect());
    main.style.transformOrigin=p.x+"% "+p.y+"%";
  });
  stage.addEventListener("pointerleave",()=>{
    stage.classList.remove("hover-zooming");
    main.style.removeProperty("transform-origin");
  });
  gallery.append(stage,count);
  if(images.length>1)gallery.append(thumbs);
  if(images.length>1)pick(0);
  return gallery;
}
