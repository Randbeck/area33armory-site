/* An actual, orbitable 3D polygon scene rendered on a 2D canvas, with no
   downloaded gun meshes, third-party graphics, GPU requirement or hidden
   manufacturer-accurate geometry claims. Pure geometry/projection helpers
   can be tested in Node. This is a conceptual product UX demonstrator. */
export const COUNTER_SCENE_SCHEMA="area33.counter.scene.v1";
export const FINISHES=Object.freeze({
 graphite:Object.freeze({frame:"#383e46",slide:"#676e78",grip:"#272c32",trim:"#151a1f"}),
 sand:Object.freeze({frame:"#7c6d5b",slide:"#aa9878",grip:"#51493f",trim:"#292723"}),
 slate:Object.freeze({frame:"#424d5b",slide:"#808d9e",grip:"#303744",trim:"#1c242c"})
});
export const SAMPLE_PRICES=Object.freeze({
 base:650,
 "holosun-scs-m-gr":325,
 "streamlight-tlr7-x":145,
 "aliengear-photon":75
});
export function samplePackage(selected=[]){
 const unique=new Set(Array.isArray(selected)?selected:[]);
 const lines=[{id:"base",name:"Example handgun (fictional base amount)",amount:SAMPLE_PRICES.base}];
 for(const [id,name] of [
  ["holosun-scs-m-gr","Example optic amount"],
  ["streamlight-tlr7-x","Example light amount"],
  ["aliengear-photon","Example holster amount"]
 ])if(unique.has(id))lines.push({id,name,amount:SAMPLE_PRICES[id]});
 return {lines,total:lines.reduce((sum,line)=>sum+line.amount,0),isQuote:false,verified:false};
}
const face=(points,color)=>({points:points.map(p=>p.slice()),color});
function box(faces,x0,x1,y0,y1,z0,z1,color){
 const a=[x0,y0,z0],b=[x1,y0,z0],c=[x1,y1,z0],d=[x0,y1,z0];
 const e=[x0,y0,z1],f=[x1,y0,z1],g=[x1,y1,z1],h=[x0,y1,z1];
 faces.push(face([a,b,c,d],color),face([e,h,g,f],color),face([a,e,f,b],color),face([d,c,g,h],color),face([a,d,h,e],color),face([b,f,g,c],color));
}
function extrude(faces,outline,width,color){
 const near=outline.map(([x,y])=>[x,y,width/2]),far=outline.map(([x,y])=>[x,y,-width/2]);
 faces.push(face(near,color),face(far.slice().reverse(),color));
 for(let i=0;i<outline.length;i++){
  const j=(i+1)%outline.length;
  faces.push(face([far[i],far[j],near[j],near[i]],color));
 }
}
function line(lines,points,color="#a1a8ae",size=1){
 lines.push({points:points.map(p=>p.slice()),color,size});
}
function disc(faces,x,y,z,r,color){
 const points=[];
 for(let k=0;k<14;k++){const t=k*Math.PI*2/14;points.push([x,y+Math.cos(t)*r,z+Math.sin(t)*r]);}
 faces.push(face(points,color));
}
export function buildConceptMesh({finish="graphite",optic=false}={}){
 const palette=FINISHES[finish]||FINISHES.graphite;
 const faces=[],lines=[];
 // Layered volumes, an illustrative non-functional product concept,
 // NOT a dimensional replica, engineering drawing or assembly guide.
 extrude(faces,[[0.48,0.10],[1.67,0.07],[1.82,-1.91],[0.96,-1.96],[0.62,-1.10],[0.47,-0.44]],0.55,palette.grip);
 extrude(faces,[[-2.12,0.18],[-1.66,-0.17],[-0.50,-0.21],[0.45,-0.14],[1.62,-0.13],[2.03,0.22],[1.86,0.40],[-2.10,0.42]],0.59,palette.frame);
 extrude(faces,[[-2.27,0.36],[-2.23,0.91],[1.71,0.91],[2.08,0.71],[2.08,0.35]],0.66,palette.slide);
 // Inert visual details that help the object read as multi-sided.
 box(faces,-2.20,1.93,0.90,0.98,-0.28,0.28,palette.trim);
 box(faces,-1.15,-0.47,0.77,0.835,0.328,0.341,palette.trim);
 box(faces,-2.15,-1.95,0.98,1.10,-0.20,0.20,palette.trim);
 box(faces,1.40,1.71,0.98,1.15,-0.26,0.26,palette.trim);
 // Trigger-guard outline with a real empty interior, not a flat texture.
 box(faces,-0.98,0.51,-0.77,-0.66,-0.23,0.23,palette.trim);
 box(faces,-1.01,-0.90,-0.76,-0.11,-0.23,0.23,palette.trim);
 box(faces,0.40,0.50,-0.75,-0.15,-0.23,0.23,palette.trim);
 line(lines,[[-0.28,-0.16,0.29],[-0.11,-0.34,0.29],[-0.17,-0.53,0.29]],"#161b20",4);
 box(faces,0.94,1.88,-2.02,-1.92,-0.29,0.29,palette.trim);
 // End-view ring shows model depth when physically rotated.
 disc(faces,-2.275,0.60,0,0.16,"#1c2024");
 disc(faces,-2.278,0.60,0,0.095,"#0a0c0f");
 // Serrations and grip grooves are surface-only line art.
 for(let i=0;i<7;i++){
  const x=1.25+i*.085;
  line(lines,[[x,0.46,0.339],[x+0.11,0.81,0.339]],"#151b20",1.7);
  line(lines,[[x,0.46,-0.34],[x+0.11,0.81,-0.34]],"#151b20",1.7);
 }
 for(let i=0;i<11;i++){
  const y=-0.55-i*0.113;
  const x0=0.68+(-y)*0.22;
  const x1=1.66+(-y)*0.055;
  line(lines,[[x0,y,0.286],[x1,y,0.286]],"#13191c",1.1);
  line(lines,[[x0,y,-0.286],[x1,y,-0.286]],"#13191c",1.1);
 }
 line(lines,[[-1.85,0.27,0.307],[-1.2,0.27,0.307]],"#171b1e",1.3);
 line(lines,[[-1.85,0.27,-0.307],[-1.2,0.27,-0.307]],"#171b1e",1.3);
 if(optic){
  // Conceptual optic envelope only. Manufacturer-listed G19 MOS fit
  // allows contextual demonstration, but not a dimensional fit assertion.
  box(faces,0.56,1.35,0.99,1.09,-0.22,0.22,"#1a2026");
  box(faces,0.61,0.73,1.06,1.43,-0.19,0.19,"#343e48");
  box(faces,1.19,1.33,1.06,1.43,-0.19,0.19,"#343e48");
  box(faces,0.61,1.33,1.34,1.45,-0.19,0.19,"#343e48");
  box(faces,0.73,1.19,1.11,1.34,0.175,0.185,"#52717c");
 }
 return {faces,lines,conceptOnly:true,exactProduct:false,meshKind:"procedural-illustration"};
}
export function transformPoint(p,camera){
 const yaw=Number.isFinite(camera?.yaw)?camera.yaw:0;
 const pitch=Number.isFinite(camera?.pitch)?camera.pitch:0;
 const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const x=p[0]*cy+p[2]*sy;
 const z=-p[0]*sy+p[2]*cy;
 return [x,p[1]*cp-z*sp,p[1]*sp+z*cp];
}
export function projectPoint(p,camera,width,height){
 const t=transformPoint(p,camera);
 const distance=9.5;
 const perspective=distance/Math.max(3,distance-t[2]);
 const zoom=Math.max(.7,Math.min(2.1,Number.isFinite(camera?.zoom)?camera.zoom:1));
 const scale=Math.min(width/6.6,height/4.25)*zoom*perspective;
 return [width/2+t[0]*scale,height*.55-t[1]*scale,t[2]];
}
export function clampCamera(camera){
 return {
  yaw:Number.isFinite(camera?.yaw)?camera.yaw:0,
  pitch:Math.max(-1.42,Math.min(1.42,Number.isFinite(camera?.pitch)?camera.pitch:0)),
  zoom:Math.max(.7,Math.min(2.1,Number.isFinite(camera?.zoom)?camera.zoom:1))
 };
}
export function reticleScale(magnification,plane){
 const mag=Math.max(1,Math.min(8,Number.isFinite(magnification)?magnification:4));
 return plane==="ffp"?mag/4:1;
}
const hexToRgb=h=>{
 const digits=h.replace("#","");
 return [parseInt(digits.slice(0,2),16),parseInt(digits.slice(2,4),16),parseInt(digits.slice(4,6),16)];
};
function shade(hex,amount){
 const [r,g,b]=hexToRgb(hex);
 const level=Math.max(.22,Math.min(1.3,amount));
 return "rgb("+[r,g,b].map(v=>Math.round(Math.min(255,v*level))).join(",")+")";
}
function normal(a,b,c){
 const u=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],v=[c[0]-a[0],c[1]-a[1],c[2]-a[2]];
 const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
 const len=Math.hypot(...n)||1;
 return n.map(q=>q/len);
}
function poly(ctx,points){
 ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);
 for(let i=1;i<points.length;i++)ctx.lineTo(points[i][0],points[i][1]);
 ctx.closePath();
}
export function paintConcept(ctx,width,height,camera,mix,mesh){
 const solid=Math.max(0,Math.min(1,mix));
 const bg=ctx.createRadialGradient(width*.5,height*.5,0,width*.5,height*.5,width*.7);
 bg.addColorStop(0,"#242d39");bg.addColorStop(1,"#0b0d10");
 ctx.fillStyle=bg;ctx.fillRect(0,0,width,height);
 // Actual model geometry orbits; the blueprint reference grid stays fixed.
 ctx.strokeStyle=solid<.7?"#5cb7c11a":"#ffffff0b";ctx.lineWidth=1;
 const step=width>550?46:34;
 for(let x=(width/2)%step;x<width;x+=step){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,height);ctx.stroke();}
 for(let y=(height/2)%step;y<height;y+=step){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(width,y);ctx.stroke();}
 ctx.strokeStyle=solid<.7?"#78dce52c":"#ddd3";
 for(const scale of [.29,.46]){ctx.beginPath();ctx.ellipse(width/2,height*.55,width*scale,height*scale*.76,0,0,Math.PI*2);ctx.stroke();}
 ctx.strokeStyle="#e8ecf014";ctx.beginPath();ctx.moveTo(width/2,0);ctx.lineTo(width/2,height);ctx.moveTo(0,height*.55);ctx.lineTo(width,height*.55);ctx.stroke();
 const shadow=ctx.createRadialGradient(width*.50,height*.78,5,width*.50,height*.78,width*.33);
 shadow.addColorStop(0,"#0000008c");shadow.addColorStop(1,"#00000000");
 ctx.fillStyle=shadow;ctx.beginPath();ctx.ellipse(width*.50,height*.79,width*.32,height*.10,0,0,Math.PI*2);ctx.fill();
 const vertices=mesh.faces.map(f=>({original:f,
  turned:f.points.map(p=>transformPoint(p,camera)),
  projected:f.points.map(p=>projectPoint(p,camera,width,height)),
  depth:f.points.reduce((sum,p)=>sum+transformPoint(p,camera)[2],0)/f.points.length
 })).sort((a,b)=>a.depth-b.depth);
 for(const f of vertices){
  if(f.projected.length<3)continue;
  poly(ctx,f.projected);
  if(solid>.001){
   const n=normal(...f.turned.slice(0,3));
   const light=Math.max(0,n[0]*(-.25)+n[1]*.58+n[2]*.75);
   ctx.globalAlpha=solid;
   ctx.fillStyle=shade(f.original.color,.5+.55*light);ctx.fill();
   ctx.globalAlpha=1;
  }
  if(solid<.97){ctx.globalAlpha=1-solid*.78;ctx.strokeStyle="#8de7f3";ctx.lineWidth=1;ctx.stroke();ctx.globalAlpha=1;}
  else{ctx.strokeStyle="#090c105c";ctx.lineWidth=.6;ctx.stroke();}
 }
 for(const seg of mesh.lines){
  const points=seg.points.map(p=>projectPoint(p,camera,width,height));
  ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);for(let i=1;i<points.length;i++)ctx.lineTo(points[i][0],points[i][1]);
  ctx.lineWidth=seg.size;
  ctx.strokeStyle=solid<.45?"#8de9e3":"#141a20";ctx.globalAlpha=solid<.45?.86:.78;ctx.stroke();ctx.globalAlpha=1;
 }
 ctx.fillStyle=solid<.5?"#93d7de":"#9aabb9";
 ctx.font="10px monospace";ctx.textAlign="left";
 ctx.fillText(solid<.5?"3D MODEL / WIREFRAME":"3D MODEL / SHADED",18,22);
}
export function paintReticle(ctx,width,height,magnification,plane){
 const mag=Math.max(1,Math.min(8,Number(magnification)||4));
 ctx.fillStyle="#e8ebe5";ctx.fillRect(0,0,width,height);
 ctx.save();ctx.translate(width/2,height/2);
 // Scene motifs magnify in either focal plane; a reticle's apparent scale
 // differs in FFP vs SFP. No trajectory or holdover instructions.
 const bgScale=.5+mag/8;
 ctx.lineWidth=1;ctx.strokeStyle="#919d99b0";
 for(let r=22;r<=170;r+=32){ctx.beginPath();ctx.arc(0,0,r*bgScale,0,2*Math.PI);ctx.stroke();}
 for(let k=-4;k<=4;k++){const x=k*32*bgScale;
  ctx.beginPath();ctx.moveTo(x,-height);ctx.lineTo(x,height);ctx.stroke();
  ctx.beginPath();ctx.moveTo(-width,x);ctx.lineTo(width,x);ctx.stroke();
 }
 ctx.scale(reticleScale(mag,plane),reticleScale(mag,plane));
 const extent=Math.min(width,height)*.39;
 ctx.strokeStyle="#161a1e";ctx.lineWidth=3.3;ctx.beginPath();
 for(const [a,b,c,d] of [[-extent,0,-13,0],[13,0,extent,0],[0,-extent,0,-13],[0,13,0,extent]]){ctx.moveTo(a,b);ctx.lineTo(c,d);}
 ctx.stroke();
 ctx.strokeStyle="#b72f35";ctx.lineWidth=2.4;ctx.beginPath();ctx.arc(0,0,8,0,Math.PI*2);ctx.stroke();
 ctx.fillStyle="#c1363a";ctx.beginPath();ctx.arc(0,0,2.8,0,Math.PI*2);ctx.fill();
 ctx.restore();
}
