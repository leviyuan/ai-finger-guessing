const W=1080,H=1920,DPR=window.devicePixelRatio||1;
const canvas=document.getElementById('video');canvas.width=Math.round(W*DPR);canvas.height=Math.round(H*DPR);
const ctx=canvas.getContext('2d',{alpha:false});window.videoCanvas=canvas;
const EXPORT=new URLSearchParams(location.search).has('export');document.body.classList.toggle('export',EXPORT);
const FONT='"PingFang SC","Arial",sans-serif',NUM='"Avenir Next","Arial",sans-serif';
const C={bg:'#07101e',white:'#edf4ff',muted:'#899aae',line:'#263d52',win:'#b3ffc1',loss:'#ff887e',gold:'#ffd790',cyan:'#9bd9e2'};
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>{t=clamp(t);return t*t*(3-2*t)},out=t=>1-(1-clamp(t))**3,signed=n=>n>0?'+'+n:String(n);
const names=Object.fromEntries(PLAN.players.map(p=>[p.id,p])),icons={};
const slots=Array.from({length:12},(_,i)=>i<6?{x:268,y:480+i*170}:{x:812,y:480+(11-i)*170});
const glyphs=['✊','✋','✌️'];let loaded=false,latest=0;
function text(s,x,y,size=32,color=C.white,weight=600,align='center',font=FONT){ctx.font=weight+' '+size+'px '+font;ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillStyle=color;ctx.fillText(s,x,y)}
function line(x1,y1,x2,y2,color,width=1){ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke()}
function rounded(x,y,w,h,r,fill,stroke=null,lw=1){ctx.beginPath();ctx.roundRect(x,y,w,h,r);if(fill){ctx.fillStyle=fill;ctx.fill()}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=lw;ctx.stroke()}}
function circle(x,y,r,fill,stroke=null,lw=1){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);if(fill){ctx.fillStyle=fill;ctx.fill()}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=lw;ctx.stroke()}}
function background(t){
 ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);
 const g=ctx.createRadialGradient(540,910,30,540,960,1180);g.addColorStop(0,'#122b3d');g.addColorStop(.53,'#0b1929');g.addColorStop(1,'#040a14');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
 ctx.save();ctx.globalAlpha=.16;for(let i=0;i<30;i++){const x=(i*197.3)%990+45,y=(i*111.7-t*10+H*2)%H;circle(x,y,1.2+(i%3)*.45,'#83b5ba')}ctx.restore();
 line(0,286,1080,286,'#1b2c3d',1);
 text('十二模型猜拳',540,158,72,C.white,850);
 text('赢',351,260,28,C.muted);text('+1',401,260,34,C.win,700,'center',NUM);text('输',524,260,28,C.muted);text('−1',574,260,34,C.loss,700,'center',NUM);text('平',699,260,28,C.muted);text('0',750,260,34,'#bac6d3',700,'center',NUM);
}
function orbitPath(){ctx.beginPath();ctx.moveTo(268,480);ctx.lineTo(268,1330);ctx.bezierCurveTo(268,1510,812,1510,812,1330);ctx.lineTo(812,480);ctx.bezierCurveTo(812,285,268,285,268,480)}
function track(t,rotation){
 ctx.save();orbitPath();ctx.strokeStyle='#19374a';ctx.lineWidth=34;ctx.stroke();orbitPath();ctx.strokeStyle='#345167';ctx.lineWidth=1.4;ctx.setLineDash([4,12]);ctx.lineDashOffset=-t*9;ctx.stroke();ctx.setLineDash([]);
 for(const side of [-1,1]){const x=side<0?175:905,y=side<0?830:1010,dir=side<0?1:-1;ctx.globalAlpha=.36+.24*rotation;for(let j=0;j<3;j++){const yy=y+j*14*dir;ctx.beginPath();ctx.moveTo(x-9,yy-5*dir);ctx.lineTo(x,yy+3*dir);ctx.lineTo(x+9,yy-5*dir);ctx.strokeStyle='#8aa7b7';ctx.lineWidth=2.4;ctx.stroke()}}
 ctx.restore();
}
function movingPosition(slot,t){
 if(slot===0)return slots[0];
 const next=slot===11?slots[1]:slots[slot+1],a=slots[slot];
 return {x:lerp(a.x,next.x,t),y:lerp(a.y,next.y,t)};
}
function windTrails(progress,speed){
 const strength=clamp((speed-.7)/(PLAN.timeline.peak_rounds_per_second-.7))**.65;if(strength<.01)return;
 ctx.save();ctx.globalCompositeOperation='screen';ctx.lineCap='round';
 for(let lane=0;lane<3;lane++){const rx=330+lane*27,ry=560+lane*22,point=a=>({x:540-rx*Math.cos(a),y:930+ry*Math.sin(a)});
  for(let streak=0;streak<5;streak++){const head=(progress/4+streak/5+lane*.037)*Math.PI*2,length=.13+.67*strength;
   for(let part=0;part<10;part++){const a=head-length+length*part/10,b=a+length/10,p=point(a),q=point(b),m=point((a+b)/2);ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.quadraticCurveTo(m.x,m.y,q.x,q.y);ctx.strokeStyle=lane===1?'#b3ffdb':'#8bccf2';ctx.globalAlpha=(.035+.21*strength)*((part+1)/10)**1.7;ctx.lineWidth=1.1+strength*1.9+lane*.15;ctx.stroke()}}
 }
 ctx.globalAlpha=.06*strength;ctx.lineWidth=7*strength;for(let i=0;i<3;i++){const head=(progress/4+i/3)*Math.PI*2;ctx.beginPath();for(let j=0;j<=20;j++){const a=head-.85+j*.85/20,x=540-405*Math.cos(a),y=930+590*Math.sin(a);if(j===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}ctx.strokeStyle='#79aec9';ctx.stroke()}ctx.restore();
}
function drawIcon(id,x,y,size){const p=names[id],light=['openai','anthropic','zai'].includes(p.brand);ctx.save();ctx.beginPath();ctx.arc(x,y,size/2,0,Math.PI*2);ctx.clip();ctx.fillStyle=light||p.brand==='doubao'?'#fff':'#122335';ctx.fillRect(x-size/2,y-size/2,size,size);const img=icons[id];if(img){const pad=light||p.brand==='doubao'?size*.08:size*.15;ctx.drawImage(img,x-size/2+pad,y-size/2+pad,size-2*pad,size-2*pad)}ctx.restore()}
function hand(move,x,y,side,scale=1,angle=0,alpha=1){ctx.save();ctx.globalAlpha*=alpha;ctx.translate(x,y);ctx.rotate(angle);ctx.scale(scale*(side===1?-1:1),scale);ctx.font='106px "Apple Color Emoji","Segoe UI Emoji",sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(glyphs[move],0,0);ctx.restore()}
function burst(x,y,age,color){if(age<0||age>.36)return;const p=age/.36;ctx.save();ctx.globalAlpha=(1-p)*.54;circle(x,y,24+p*59,null,color,3*(1-p)+.5);for(let i=0;i<8;i++){const a=i*Math.PI/4;line(x+Math.cos(a)*(27+p*20),y+Math.sin(a)*(27+p*20),x+Math.cos(a)*(39+p*40),y+Math.sin(a)*(39+p*40),color,2)}ctx.restore()}
function node(id,x,y,score,delta,age,t,fast){
 const p=names[id],isFixed=id===10,flash=fast?.26:age>=0?Math.exp(-age*5):0,scale=fast?.91:1;
 ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);const glow=isFixed?C.win:(delta>0?C.win:delta<0?C.loss:'#96acbf');
 if(isFixed||flash>.025){ctx.save();ctx.shadowColor=glow;ctx.shadowBlur=isFixed?15+4*Math.sin(t*3):flash*23;circle(0,0,58,'#12253a',glow,isFixed?3:flash*3);ctx.restore()}else circle(0,0,57,'#112133','#435565',1.4);
 drawIcon(id,0,0,94);const badge=score>0?C.win:score<0?C.loss:'#c1cfdd';rounded(8,20,70,44,14,'#0a1928',badge,1.5);text(signed(score),43,42,29,badge,800,'center',NUM);text(p.short_name,0,92,27,isFixed?C.win:'#e3ecf7',isFixed?800:650);ctx.restore();
}
function motionAt(t){
 for(const s of PLAN.timeline.segments){if(t<=s.end){const dt=s.end-s.start,u=clamp((t-s.start)/dt),dv=s.v1-s.v0;return {progress:s.progress_start+dt*(s.v0*u+dv*(u**3-.5*u**4)),speed:s.v0+dv*u*u*(3-2*u)}}}
 for(const s of PLAN.timeline.closing){if(t<=s.end)return {progress:s.progress+(t-s.start)*s.speed,speed:s.speed}}return {progress:PLAN.round_count,speed:0};
}
function drawRound(t){
 const motion=motionAt(t),frame=t*PLAN.fps,idx=Math.min(PLAN.round_count-1,Math.floor(motion.progress+1e-9)),r=PLAN.rounds[idx],localFrame=Math.max(0,frame-r.start_frame),u=clamp(motion.progress-idx),revealed=localFrame+1e-7>=r.reveal_frame;
 const age=t-r.reveal_at,score=revealed?r.after:r.before,rotate=idx===PLAN.round_count-1?0:r.fast?u:ease((localFrame-r.rotate_frame)/Math.max(1,r.frames-1-r.rotate_frame)),handAlpha=idx===PLAN.round_count-1?1:r.fast?lerp(.84,.43,clamp((motion.speed-2)/8)):1-ease((localFrame-r.rotate_frame+2)/2),moving=rotate>0;
 track(t,rotate);windTrails(motion.progress,motion.speed);
 for(let row=0;row<6;row++){const pair=r.pairs[row],a=pair[0],b=pair[1],y=slots[row].y;ctx.save();ctx.globalAlpha=r.fast?.67:1-rotate*.88;let shade=ctx.createLinearGradient(375,y,705,y);shade.addColorStop(0,'#19304100');shade.addColorStop(.5,'#18334491');shade.addColorStop(1,'#19304100');rounded(362,y-62,356,138,38,shade);line(500,y,580,y,'#355061',1.4);if(!revealed)text('VS',540,y-4,23,'#688397',700,'center',NUM);else if(r.deltas[a]===0)text('平',540,y-4,27,'#aebdcd',600);else{const left=r.deltas[a]>0;ctx.save();ctx.translate(540,y-4);if(!left)ctx.rotate(Math.PI);ctx.beginPath();ctx.moveTo(15,0);ctx.lineTo(-12,0);ctx.moveTo(-2,-10);ctx.lineTo(-13,0);ctx.lineTo(-2,10);ctx.strokeStyle=C.win;ctx.lineWidth=3.5;ctx.stroke();ctx.restore()}ctx.restore();
  if(handAlpha>.005){const shake=!revealed?Math.sin(localFrame/Math.max(1,r.reveal_frame)*Math.PI*4)*8:0,impact=!r.fast&&age>=0?Math.sin(clamp(age/.16)*Math.PI)*.16:0;hand(revealed?r.moves[a]:0,425+(revealed?impact*14:0),y+shake,0,1+impact,-shake*.008,handAlpha);hand(revealed?r.moves[b]:0,655-(revealed?impact*14:0),y-shake,1,1+impact,shake*.008,handAlpha);if(revealed&&!r.fast){ctx.save();ctx.globalAlpha=handAlpha*out(age/.07);text(r.deltas[a]===0?'0':signed(r.deltas[a]),425,y+60,30,r.deltas[a]>0?C.win:r.deltas[a]<0?C.loss:'#a4b4c5',800,'center',NUM);text(r.deltas[b]===0?'0':signed(r.deltas[b]),655,y+60,30,r.deltas[b]>0?C.win:r.deltas[b]<0?C.loss:'#a4b4c5',800,'center',NUM);ctx.restore()}}
  if(!r.fast&&revealed&&!moving&&r.deltas[a]!==0)burst(r.deltas[a]>0?425:655,y,age,C.win);
 }
 r.layout.forEach((id,slot)=>{const pos=movingPosition(slot,rotate);node(id,pos.x,pos.y,score[id],revealed?r.deltas[id]:0,age,t,r.fast)});
 const stage=motion.speed>=1.35?'最高速':motion.speed>=1.05?'加速段':moving?'换位':'';
 if(stage)text(stage,540,1600,30,r.closing?C.gold:'#bdd7df',650);text(String(idx+1).padStart(2,'0'),441,1727,61,C.white,800,'center',NUM);text('/ '+PLAN.round_count+' 轮',604,1732,30,'#8b9db0',600);
 const seg=10,width=666,gap=8,cell=(width-gap*(seg-1))/seg,progress=(idx+u)/PLAN.round_count*seg;for(let i=0;i<seg;i++){rounded(207+i*(cell+gap),1782,cell,5,2,'#243b4c');if(progress>i)rounded(207+i*(cell+gap),1782,cell*clamp(progress-i),5,2,Math.floor(progress)===i?C.win:'#587f7e')}
 return {round:idx+1,settled_rounds:idx+(revealed?1:0),progress:motion.progress,speed:motion.speed,phase:moving?'rotate':revealed?'reveal':'prepare',revealed,scores:score};
}
let danmakuLayout=null;
function prepareDanmaku(){
 const cfg=PLAN.danmaku_presentation;
 danmakuLayout=PLAN.danmaku.map((item,i)=>{
  const p=names[item.player_id],label=p.short_name+'：';
  ctx.font='700 '+cfg.name_size+'px '+FONT;const labelWidth=Math.ceil(ctx.measureText(label).width);
  ctx.font='750 '+item.font_size+'px '+FONT;const textWidth=Math.ceil(ctx.measureText(item.text).width);
  const bodyOffset=22+44+14+labelWidth+10,width=bodyOffset+textWidth+24;
  const duration=(W+width+2*cfg.edge_margin)/item.speed;
  return {...item,lane:i,y:item.y,start:item.start,duration,width,label,labelWidth,bodyOffset};
 });
 window.danmakuLayout=danmakuLayout;
 window.danmakuEnd=PLAN.game_end+Math.max(...danmakuLayout.map(item=>item.start+item.duration));
 if(window.danmakuEnd>PLAN.duration)throw Error('Video ends before every danmaku has crossed the screen');
}
function drawDanmaku(age){
 if(!danmakuLayout)prepareDanmaku();
 const cfg=PLAN.danmaku_presentation,visible=[];
 danmakuLayout.forEach(item=>{
  const elapsed=age-item.start;
  if(elapsed<0||elapsed>item.duration)return;
  const x=item.direction>0 ? -item.width-cfg.edge_margin+elapsed*item.speed : W+cfg.edge_margin-elapsed*item.speed,y=item.y;
  visible.push({player_id:item.player_id,lane:item.lane,x,y,width:item.width,text:item.text});
  ctx.save();ctx.globalAlpha=.98;
  ctx.shadowColor='#000a';ctx.shadowBlur=12;ctx.shadowOffsetY=3;
  const boxHeight=item.font_size+34;
  rounded(x,y-boxHeight/2,item.width,boxHeight,boxHeight/2,'#071525f2',item.color,2);
  ctx.shadowBlur=0;ctx.shadowOffsetY=0;
  drawIcon(item.player_id,x+44,y,44);
  text(item.label,x+80,y,cfg.name_size,'#eef5ff',700,'left');
  text(item.text,x+item.bodyOffset,y,item.font_size,item.color,750,'left');
  ctx.restore();
 });
 return visible;
}
function finalScene(t){
 const age=t-PLAN.game_end,order=PLAN.final_order;text('最终排名',540,350,40,C.gold,750);
 order.forEach((id,i)=>{const show=out((age-.025*i)/.55),y=490+i*78,p=names[id],val=PLAN.final_scores[id],winner=i===0;ctx.save();ctx.globalAlpha=show;ctx.translate(0,(1-show)*28);rounded(164,y-32,752,64,16,winner?'#203e39':(i%2===0?'#122434':'#0e1e2e'),winner?'#a7eab176':'#29415480',winner?2:1);text(String(i+1).padStart(2,'0'),210,y,25,winner?C.gold:'#6f879c',750,'center',NUM);drawIcon(id,272,y,46);text(p.short_name,310,y,25,id===10?C.win:C.white,700,'left');text(p.model,560,y,15,C.muted,500,'left');text(signed(val),862,y,31,val>0?C.win:val<0?C.loss:'#abbacb',800,'center',NUM);ctx.restore()});
 const danmaku=drawDanmaku(age);
 return {phase:'final',scores:PLAN.final_scores,order,danmaku};
}
function render(t){t=clamp(Number(t)||0,0,PLAN.duration);latest=t;ctx.setTransform(DPR,0,0,DPR,0,0);ctx.globalAlpha=1;background(t);const state=t<PLAN.game_end?drawRound(t):finalScene(t);window.frameState={time:t,...state};if(!EXPORT){document.getElementById('seek').value=t;document.getElementById('time').textContent=t.toFixed(1)+' / '+PLAN.duration.toFixed(1)}}
window.videoDuration=PLAN.duration;window.seekVideo=t=>render(t);window.captureFrames=[['opening',.2],['reveal',.7],['plateau',15],['round-22',18.2],['ranking',18.9],['danmaku-first',26],['danmaku-middle',32],['danmaku-last',39],['ending',PLAN.duration-.3]];
window.assetsReady=Promise.all(PLAN.players.map(p=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{icons[p.id]=img;resolve()};img.onerror=()=>reject(Error('brand asset unavailable: '+p.name));img.src=p.icon}))).then(()=>document.fonts.ready).then(()=>{loaded=true;render(0)});
let playing=!EXPORT,origin=performance.now(),offset=0;const audio=EXPORT?null:new Audio(PLAN.basename+'.wav');
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'暂停':'播放';if(playing){offset=latest;origin=performance.now();if(audio){audio.currentTime=latest;audio.play().catch(()=>{})}}else if(audio)audio.pause()};document.getElementById('seek').oninput=e=>{offset=Number(e.target.value);origin=performance.now();render(offset);if(audio)audio.currentTime=offset};function tick(now){if(loaded&&playing){let t=offset+(now-origin)/1000;if(t>PLAN.duration){offset=0;origin=now;t=0;if(audio&&!audio.paused)audio.currentTime=0}render(t)}if(!EXPORT)requestAnimationFrame(tick)}if(!EXPORT)window.assetsReady.then(()=>{origin=performance.now();requestAnimationFrame(tick)});
