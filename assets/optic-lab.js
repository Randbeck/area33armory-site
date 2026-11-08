"use strict";
import {paintReticle} from "./counter-3d-scene.mjs";
const $=id=>document.getElementById(id);
const canvas=$("reticle-canvas"),ctx=canvas.getContext("2d");
let plane="ffp",mag=4;
function render(){
 if(!ctx)return;
 const rect=canvas.getBoundingClientRect(),ratio=Math.min(2,window.devicePixelRatio||1);
 const width=Math.max(1,Math.round(rect.width*ratio)),height=Math.max(1,Math.round(rect.height*ratio));
 if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
 paintReticle(ctx,width,height,mag,plane);
}
for(const id of ["ffp","sfp"])$(id).addEventListener("click",()=>{
 plane=id;
 $("ffp").setAttribute("aria-pressed",String(plane==="ffp"));
 $("sfp").setAttribute("aria-pressed",String(plane==="sfp"));
 $("focal-heading").textContent=plane==="ffp"?"First focal plane":"Second focal plane";
 $("focal-copy").textContent=plane==="ffp"?
  "The reticle appears to change size together with the magnified scene. Watch both the scene's geometric background and the red/black reticle scale.":
  "The scene magnifies, but the reticle stays about the same apparent size. Compare the crosshair to the geometric background as you move the slider.";
 render();
});
$("magnification").addEventListener("input",e=>{
 mag=Number(e.target.value);
 $("mag-label").textContent=mag+"×";
 render();
});
window.addEventListener("resize",render);
render();
