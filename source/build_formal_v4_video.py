#!/usr/bin/env python3
"""Build the 22-round replay with large central danmaku and reveal-only sound."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import wave
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[3]
RUN=ROOT/'data/formal-run-20260918-12x22'
ROSTER=json.loads((ROOT/'data/formal-roster-12.json').read_text())['players']
BASENAME='rps-carousel-v8-varied-danmaku'
VERSION='V8-变化弹幕'
FPS=30;DURATION=34.;GAME_END=18.4;ROUND_COUNT=22

def brand_data(key):
 spec=importlib.util.spec_from_file_location('brand_assets',REPO/'tools/brand_assets.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.icon_data(key),m.icon_path(key)

def build_timeline():
 peak=1.5
 factor=peak/1.7
 knots=[(0,.77),(2,.86),(4,.99),(6,1.16),(8,1.33),(10,1.5),(12,1.67),(13.8,1.7)]
 knots=[(t,v*factor) for t,v in knots];segments=[];progress=0.
 for (a,v0),(b,v1) in zip(knots,knots[1:]):
  segments.append({'start':a,'end':b,'v0':v0,'v1':v1,'progress_start':progress});progress+=(b-a)*(v0+v1)/2
 plateau_duration=(ROUND_COUNT-progress)/peak
 closing=[{'progress':progress,'start':13.8,'end':13.8+plateau_duration,'speed':peak}]
 def motion(t):
  for s in segments:
   if t<=s['end']:
    dt=s['end']-s['start'];u=max(0,min(1,(t-s['start'])/dt));dv=s['v1']-s['v0'];return s['progress_start']+dt*(s['v0']*u+dv*(u**3-.5*u**4))
  for s in closing:
   if t<=s['end']:return s['progress']+(t-s['start'])*s['speed']
  return 20
 times=[]
 for q in range(ROUND_COUNT+1):
  if q>=progress: times.append(13.8+(q-progress)/peak);continue
  lo,hi=0.,13.8
  for _ in range(64):
   mid=(lo+hi)/2
   if motion(mid)<q:lo=mid
   else:hi=mid
  times.append((lo+hi)/2)
 return segments,closing,times

def build_plan():
 seg,closing,times=build_timeline();players=[]
 for p in ROSTER:
  icon,src=brand_data(p['brand']);players.append({**p,'icon':icon,'icon_source':str(src.relative_to(REPO)),'icon_sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
 # Keep DeepSeek in the fixed observation seat while the other eleven rotate visually.
 visual=[10]+[i for i in range(1,13) if i!=10];visual_layouts=[]
 for _ in range(ROUND_COUNT):visual_layouts.append(visual[:]);visual=[visual[0],visual[-1],*visual[1:-1]]
 gesture={'石头':0,'布':1,'剪刀':2};rounds=[]
 for n in range(1,ROUND_COUNT+1):
  raw=json.loads((RUN/f'round-{n:02d}.json').read_text());moves=[None];before=[0];after=[0];deltas=[0]
  for p in players:
   key,ident=p['key'],p['id'];moves.append(gesture[raw['moves'][key]]);before.append(raw['scores_before'][key]);after.append(raw['scores_after'][key]);deltas.append(after[-1]-before[-1])
  duration=times[n]-times[n-1];frames=duration*FPS;fast=frames<=6;is_closing=False
  reveal=max(1,round(frames*.24));rotate=round(frames*.55)
  rounds.append({'index':n,'cycle':raw.get('cycle',(n-1)//11+1),'layout':visual_layouts[n-1],'pairs':raw['pairs'],'start':times[n-1],'duration':duration,'start_frame':times[n-1]*FPS,'end_frame':times[n]*FPS,'frames':frames,'fast':fast,'closing':is_closing,'reveal_frame':reveal,'rotate_frame':rotate,'reveal_at':(times[n-1]*FPS+reveal)/FPS,'rotate_at':(times[n-1]*FPS+rotate)/FPS,'moves':moves,'before':before,'after':after,'deltas':deltas})
 result=json.loads((RUN/'results-summary.json').read_text());by_key={p['key']:p['id'] for p in players};final_scores={str(by_key[k]):v for k,v in result['final_scores'].items()};order=[by_key[r['player_key']] for r in result['ranking']]
 danmaku=[
  {'text':'别急，我先把你们的套路读完。','color':'#b3ffc1','y':700,'speed':340,'font_size':46,'direction':-1,'start':.35},
  {'text':'我不连手，但我连胜。','color':'#8ed8ee','y':820,'speed':270,'font_size':58,'direction':1,'start':.60},
  {'text':'前半冲太快，后半先喘口气。','color':'#ffd790','y':980,'speed':410,'font_size':44,'direction':-1,'start':.95},
  {'text':'剪刀不是偏科，是稳定输出。','color':'#b9a8ff','y':1140,'speed':300,'font_size':52,'direction':1,'start':1.25},
  {'text':'管你出什么，反正我要纯随机。','color':'#9fe4c1','y':1290,'speed':380,'font_size':48,'direction':-1,'start':1.55},
  {'text':'哎呀，我怎么出了这么多石头啊。','color':'#a7d7ff','y':760,'speed':450,'font_size':42,'direction':1,'start':2.05},
  {'text':'前半送的分，后半我收回来了。','color':'#ffb38c','y':900,'speed':290,'font_size':60,'direction':-1,'start':2.45},
  {'text':'我很均衡，分数不太均衡。','color':'#8ed8ee','y':1060,'speed':360,'font_size':45,'direction':1,'start':2.85},
  {'text':'布阵很厚，胜负看运。','color':'#e1c5ff','y':1220,'speed':420,'font_size':50,'direction':-1,'start':3.25},
  {'text':'前半挨揍，后半止血。','color':'#ffc08d','y':680,'speed':315,'font_size':54,'direction':1,'start':3.70},
  {'text':'我很优雅地随机，然后优雅地输。','color':'#d6dce8','y':880,'speed':395,'font_size':46,'direction':-1,'start':4.10},
  {'text':'记得太多，赢得太少。','color':'#ff9b9b','y':1180,'speed':275,'font_size':56,'direction':1,'start':4.50},
 ]
 for item,key in zip(danmaku,['glm','meta','kimi','gemini','hunyuan','gpt','grok','deepseek','minimax','doubao','claude','qwen']):
  item['player_id']=by_key[key]
 return {'version':VERSION,'basename':BASENAME,'synthetic':False,'model_calls':264,'notice':'二十二轮真实模型选择。','data_source':'data/formal-run-20260918-12x22','duration':DURATION,'game_end':GAME_END,'game_frames':round(GAME_END*FPS),'fps':FPS,'round_count':ROUND_COUNT,'match_count':132,'progress_segments':10,'players':players,'rounds':rounds,'final_scores':final_scores,'final_order':order,'final_ranks':{str(by_key[r['player_key']]):r['rank'] for r in result['ranking']},'score':{'win':1,'loss':-1,'draw':0},'danmaku':danmaku,'danmaku_presentation':{'font_size_range':[42,60],'name_size':30,'speed_range':[270,450],'y_range':[680,1290],'directions':[-1,1],'gap':96,'edge_margin':40,'authorship':'Scripted character banter based on this game; not verbatim model replies.'},'timeline':{'segments':seg,'closing':closing,'peak_time':13.8,'peak_rounds_per_second':1.5}}

def write_audio(plan):
 rate=48000;audio=np.zeros((round(rate*DURATION),2),np.float64)
 def add(at,sig,gain=.1,pan=0):
  b=max(0,round(at*rate));e=min(len(audio),b+len(sig))
  if e>b:audio[b:e,0]+=sig[:e-b]*gain*(1-.2*pan);audio[b:e,1]+=sig[:e-b]*gain*(1+.2*pan)
 def tone(at,freq,length,gain):
  t=np.arange(round(rate*length))/rate;env=np.minimum(t/.005,1)*np.exp(-t/(length*.26));add(at,(np.sin(2*np.pi*freq*t)+.2*np.sin(4*np.pi*freq*t))*env,gain)
  # Retain the original two-layer reveal hit; leave every other sample silent.
 events=[]
 for r in plan['rounds']:
  tone(r['reveal_at'],118 if not r['fast'] else 165,min(.16,r['duration']*.55),(.10 if not r['fast'] else .046)*min(1,8*r['duration']))
  tone(r['reveal_at']+.01,600+(r['index']%9)*48,min(.10,r['duration']*.5),(.034 if not r['fast'] else .017)*min(1,8*r['duration']),)
  events.append({'round':r['index'],'start':r['reveal_at'],'end':r['reveal_at']+.16})
 peak=float(np.abs(audio).max());gain=.56/peak if peak else 1;audio*=gain;integer=np.rint(np.clip(audio,-.999,.999)*8388607).astype('<i4');packed=integer.view(np.uint8).reshape(-1,4)[:,:3].tobytes();target=ROOT/'output'/f'{BASENAME}.wav'
 with wave.open(str(target),'wb') as out:out.setnchannels(2);out.setsampwidth(3);out.setframerate(rate);out.writeframes(packed)
 return {'file':str(target.relative_to(ROOT)),'sample_rate':rate,'bits':24,'channels':2,'duration':DURATION,'peak':.56,'linear_gain':gain,'source':'Original reveal hits only','events':events,'wind_noise':False,'rotation_swishes':False,'ending_chime':False}

def main():
 (ROOT/'output').mkdir(exist_ok=True);plan=build_plan();plan['audio']=write_audio(plan);clean=json.loads(json.dumps(plan))
 for p in clean['players']:p.pop('icon',None)
 (ROOT/'data/formal-v8-video-plan.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2)+'\n')
 html=(ROOT/'src/formal_v4_scene.html').read_text().replace('__PLAN__',json.dumps(plan,ensure_ascii=False)).replace('__ANIMATION__',(ROOT/'src/formal_v4_animation_12.js').read_text()).replace('__BASENAME__',BASENAME).replace('__VERSION__',VERSION).replace('__DURATION__',str(DURATION));target=ROOT/'output'/f'{BASENAME}.html';target.write_text(html);print(json.dumps({'html':str(target),'rounds':ROUND_COUNT,'matches':ROUND_COUNT*6,'duration':DURATION},ensure_ascii=False))
if __name__=='__main__':main()
