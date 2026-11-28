# 媽媽小幫手 → 芯情調色盤：任何過去的日子都能補記心情、喝水、日記
p='/home/user/heart-corner/public/index.html'
s=open(p,encoding='utf-8').read()
def rep(a,b,cnt=1):
    global s
    n=s.count(a); assert n==cnt,(a[:70],n); s=s.replace(a,b)

rep('/* 媽媽小幫手 */','/* 芯情調色盤 */')
rep('   媽媽小幫手：喝水打卡＋心情日曆','   芯情調色盤：心情・喝水・日記，過去的日子也能補記')
rep('<b>媽媽小幫手</b><small>喝水打卡・心情日曆</small>','<b>芯情調色盤</b><small>心情・日記・喝水</small>')

# ---------- 畫面 ----------
a=s.index('function viewMom(){'); b=s.index('function waterHistory(){')
s=s[:a]+r'''function viewMom(){
  const tk=dayKey(),k=momDay||tk,isT=k===tk,goal=S.waterGoal||8;
  const v=(S.days||{})[k]||{},w=v.water||0,mo=MOODS.find(x=>x.id===v.mood);
  const mk=momMonth||monthKey(),md=monthDays(mk),thisMk=monthKey();
  const wk=['日','一','二','三','四','五','六'];
  const [,m,dd]=k.split('-').map(Number);
  const dayName=isT?'今天':`${m} 月 ${dd} 日`;
  // 這個月的顏色比例
  const mine=md.keys.map(x=>((S.days||{})[x]||{}).mood).filter(Boolean);
  const strip=mine.length?MOODS.map(x=>({x,n:mine.filter(y=>y===x.id).length})).filter(o=>o.n).map(o=>`<span style="flex:${o.n};background:${o.x.color}" title="${o.x.name} ${o.n} 天"></span>`).join(''):'';
  return sky('Mood palette','芯情調色盤','每一種心情都是一個顏色，把每一天塗上屬於妳的色彩。',isT?(mo?mo.reply:'今天心情怎麼樣？點一下，幫今天塗上顏色。'):`正在幫 ${m} 月 ${dd} 日補記，想起什麼就寫什麼。`)+`
  <div class="gutter stack" style="margin-top:-12px;position:relative;z-index:3">
    <section class="card cal palette">
      <div class="cal-top">
        <button class="mnav" data-month="-1" aria-label="上個月">‹</button>
        <div class="cal-title"><b>${md.y===new Date().getFullYear()?'':md.y+' 年 '}${md.m} 月的調色盤</b><small>塗了 ${mine.length} 天・喝水達標 ${monthCount('water',mk)} 天</small></div>
        <button class="mnav" data-month="1" aria-label="下個月" ${mk>=thisMk?'disabled':''}>›</button>
      </div>
      <div class="pal-strip" aria-hidden="true">${strip||'<span class="empty"></span>'}</div>
      <div class="cal-grid">${wk.map(x=>`<span class="cal-h">${x}</span>`).join('')}${'<span></span>'.repeat(md.first)}${md.keys.map((x,i)=>{const dv=(S.days||{})[x]||{};const dm=MOODS.find(y=>y.id===dv.mood);
        const fut=x>tk;
        return `<button class="cal-d ${dm?'paint':''} ${x===tk?'today':''} ${x===k?'sel':''}" data-day="${x}" ${fut?'disabled':''} style="${dm?`--mc:${dm.color}`:''}" aria-label="${md.m} 月 ${i+1} 日${dm?'，'+dm.name:''}${dv.diary?'，有日記':''}" aria-pressed="${x===k}"><b class="num">${i+1}</b>${(dv.water||0)>=goal?'<em>💧</em>':''}${dv.diary?'<u></u>':''}</button>`}).join('')}</div>
      <div class="legend">${MOODS.map(x=>`<span><i style="background:${x.color}"></i>${x.name}</span>`).join('')}<span>💧 喝水達標</span><span><u class="dot-diary"></u> 有寫日記</span></div>
      <p class="tiny" style="margin:0;text-align:center">點日曆上任何一天，都可以回去補記心情、喝水和日記</p>
    </section>

    <section class="card day-card" id="dayCard" style="${mo?`--mc:${mo.color}`:''}">
      <div class="day-head">
        <div><b>${dayName}${isT?'':`<span class="past-tag">補記中</span>`}</b><small>${isT?`${m} 月 ${dd} 日・星期${wk[new Date(k+'T12:00:00+08:00').getDay()]}`:`星期${wk[new Date(k+'T12:00:00+08:00').getDay()]}`}</small></div>
        ${isT?'':'<button class="btn btn-ghost back-today" data-day="'+tk+'">回到今天</button>'}
      </div>

      <div class="rv-q"><b>${isT?'今天':'這天'}的心情是什麼顏色？</b><small>${mo?'再點一次可以取消':'點一下塗上顏色'}</small></div>
      <div class="mood-row">${MOODS.map(x=>`<button data-mood="${x.id}" aria-pressed="${v.mood===x.id}" style="--mc:${x.color}"><i></i>${x.name}</button>`).join('')}</div>

      <div class="rv-q" style="margin-top:6px"><b>${isT?'今天':'這天'}喝了幾杯水？</b><small>1 杯約 250ml</small></div>
      <div class="cups">${Array.from({length:goal},(_,i)=>`<button class="cup ${i<w?'full':''}" data-cup="${i}" aria-label="第 ${i+1} 杯"><svg viewBox="0 0 30 36"><path d="M4 4h22l-3 28H7Z" fill="#fff" stroke="#b9cbd6" stroke-width="1.5"/><path class="wtr" d="M5.6 14h18.8l-2 17.2H7.6Z" fill="#9cc3d8"/></svg></button>`).join('')}</div>
      <div class="water-row"><span><b class="num" style="font-size:22px;font-family:var(--latin)">${w}</b> / ${goal} 杯${w>=goal?'・達標了！':''}</span>
        <span class="goal-ctl"><button data-goal="-1" aria-label="目標減少">−</button><span>目標 ${goal} 杯</span><button data-goal="1" aria-label="目標增加">＋</button></span></div>

      <div class="rv-q" style="margin-top:6px"><b>${isT?'今天':'這天'}的日記</b><small>${isT?'寫給今天的自己':'想起什麼就補寫什麼'}</small></div>
      <label for="diaryText" style="position:absolute;left:-9999px">心情日記</label>
      <textarea id="diaryText" maxlength="500" placeholder="${isT?'今天發生了什麼事？開心的、累的、想對寶寶或自己說的話，都可以寫下來。':'這天發生了什麼事？現在補寫也可以。'}">${esc(v.diary||'')}</textarea>
      <div class="rv-meta"><span id="diaryCount">${(v.diary||'').length} / 500 字</span><span id="diarySaved">${v.diary?'已儲存':'會自動儲存'}</span></div>
      <p class="tiny" style="margin:0">哺乳期的媽媽通常需要比平常多喝一點水，口渴就喝，不用勉強一次喝很多。<br>🔒 心情、喝水和日記只存在妳自己的手機裡，芯彤和其他人都看不到。</p>
    </section>
    ${waterHistory()}
  </div>`;
}
let momDay=null,momMonth=null,waterRange=7;
function momRec(){const k=momDay||dayKey();if(k===dayKey())return today();S.days[k]=S.days[k]||{tasks:{},pets:0,fed:0};return S.days[k]}
'''+s[b:]

rep("if(r!=='mom')momDay=null;","if(r!=='mom'){momDay=null;momMonth=null}")

# ---------- 互動 ----------
rep("""  document.querySelectorAll('[data-cup]').forEach(b=>b.onclick=()=>{const d=today(),i=+b.dataset.cup,goal=S.waterGoal||8;const was=d.water||0;d.water=(i<was)?i:i+1;save();ac();sfx('tick');
    if(was<goal&&d.water>=goal){toast('今天喝水達標了！');setTimeout(checkBadges,600)}const y=scrollY;render();window.scrollTo(0,y)});""",
"""  document.querySelectorAll('[data-cup]').forEach(b=>b.onclick=()=>{const d=momRec(),isT=!momDay||momDay===dayKey(),i=+b.dataset.cup,goal=S.waterGoal||8;const was=d.water||0;d.water=(i<was)?i:i+1;save();ac();sfx('tick');
    if(was<goal&&d.water>=goal){toast(isT?'今天喝水達標了！':'這天的喝水補記好了，達標 💧');setTimeout(checkBadges,600)}const y=scrollY;render();window.scrollTo(0,y)});""")
rep("""  document.querySelectorAll('[data-day]').forEach(b=>b.onclick=()=>{momDay=b.dataset.day;const y=scrollY;render();window.scrollTo(0,y);const dd=$('.diary');if(dd)dd.scrollIntoView({behavior:'smooth',block:'nearest'})});""",
"""  document.querySelectorAll('[data-day]').forEach(b=>b.onclick=()=>{const k=b.dataset.day;momDay=k===dayKey()?null:k;momMonth=monthKey(k)===monthKey()?null:monthKey(k);const y=scrollY;render();window.scrollTo(0,y);const dd=$('#dayCard');if(dd)dd.scrollIntoView({behavior:'smooth',block:'start'})});
  document.querySelectorAll('[data-month]').forEach(b=>b.onclick=()=>{const [y0,m0]=(momMonth||monthKey()).split('-').map(Number);const t=new Date(Date.UTC(y0,m0-1+ +b.dataset.month,1));const mk=t.toISOString().slice(0,7);if(mk>monthKey())return;momMonth=mk===monthKey()?null:mk;const y=scrollY;render();window.scrollTo(0,y)});""")
rep("""  document.querySelectorAll('[data-mood]').forEach(b=>b.onclick=()=>{const d=today();d.mood=b.dataset.mood;save();const y=scrollY;render();window.scrollTo(0,y)});""",
"""  document.querySelectorAll('[data-mood]').forEach(b=>b.onclick=()=>{const d=momRec();d.mood=d.mood===b.dataset.mood?undefined:b.dataset.mood;if(!d.mood)delete d.mood;save();ac();sfx('tick');const y=scrollY;render();window.scrollTo(0,y);setTimeout(checkBadges,600)});""")

# ---------- 樣式 ----------
rep(".cal-d.sel{box-shadow:0 0 0 2px var(--mauve) inset}",""".cal-d.sel{box-shadow:0 0 0 2px var(--mauve-deep) inset,0 0 0 3px #fff inset;transform:scale(1.06);z-index:2}
.cal-d{transition:transform .2s,background .3s}
.cal-d.paint{background:linear-gradient(145deg,color-mix(in srgb,var(--mc) 78%,#fff),var(--mc));color:#fff;box-shadow:0 3px 8px color-mix(in srgb,var(--mc) 35%,transparent)}
.cal-d.paint b{text-shadow:0 1px 2px rgba(0,0,0,.15)}
.cal-d.paint u{background:#fff}
.cal-top{display:grid;grid-template-columns:36px 1fr 36px;align-items:center;gap:6px}
.cal-title{text-align:center;display:grid;gap:2px}
.cal-title b{font-size:17px;font-weight:500}
.cal-title small{font-size:12.5px;color:var(--sub)}
.mnav{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:#fff;font-size:20px;line-height:1;color:var(--sub)}
.mnav:disabled{opacity:.3}
.pal-strip{display:flex;height:10px;border-radius:99px;overflow:hidden;background:var(--cream);gap:2px}
.pal-strip span{display:block;min-width:6px}
.pal-strip .empty{flex:1;background:repeating-linear-gradient(90deg,#e7b75f33 0 20%,#8fae8b33 20% 40%,#a99bb533 40% 60%,#7f97b533 60% 80%,#d08b7f33 80% 100%)}
.day-card{padding:18px;display:grid;gap:12px;border-top:6px solid var(--mc,var(--line));scroll-margin-top:80px}
.day-card textarea{min-height:120px;width:100%;padding:12px;border-radius:var(--r-md);border:1px solid var(--line);background:#fff;line-height:1.7;resize:vertical}
.day-head{display:flex;justify-content:space-between;align-items:center;gap:10px}
.day-head b{font-size:18px;display:flex;align-items:center;gap:8px}
.day-head small{display:block;color:var(--sub);font-size:12.5px;margin-top:2px}
.back-today{height:36px;padding:0 14px;font-size:13px;flex:none}
.past-tag{font-size:11.5px;font-weight:500;padding:2px 10px;border-radius:99px;background:#f3e9f0;color:var(--mauve-deep)}""")
open(p,'w',encoding='utf-8').write(s)
print('ok')
