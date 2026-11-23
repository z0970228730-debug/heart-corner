# 把示範版頁面轉成正式版（資料改由伺服器管理）
# 用法：python3 tools/build_index.py <示範版 index.html> public/index.html
import sys, re
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()

def rep(a, b, cnt=1):
    global s
    n = s.count(a)
    assert n == cnt, (a[:80], n)
    s = s.replace(a, b)

def cut(start, end_marker):
    """刪掉從 start 開始到 end_marker（不含）之間的內容"""
    global s
    a = s.index(start); b = s.index(end_marker, a)
    s = s[:a] + s[b:]

# ---------- 共用設定 ----------
rep("  inviteBase: 'https://heartstudio.tw/?ref='", "  inviteBase: location.origin+'/?ref='")

# ---------- 狀態：不再產生示範資料 ----------
rep("let S = load() || seed();", "let S = load() || {v:3,member:null,fish:0,lots:[],hist:[],days:{},draw:null,draws:[],streak:{last:'',n:0},coupons:[],invites:[],sound:true,demo:false,badges:{}};\nS.demo=false;S.member=null;S.coupons=[];S.hist=[];S.invites=[];S.fish=0;")

# ---------- 伺服器連線層 ----------
rep("function activeLots(){", r"""let SERVER=null;
async function api(path,body){
  const opt=body===undefined?{credentials:'same-origin'}:{method:'POST',credentials:'same-origin',headers:{'content-type':'application/json'},body:JSON.stringify(body)};
  let r;try{r=await fetch('/api/'+path,opt)}catch(e){return {error:'網路連線不穩，請稍後再試'}}
  const j=await r.json().catch(()=>({error:'系統忙碌中，請稍後再試'}));
  if(r.status===401&&path!=='me'){SERVER=null;S.member=null;render();openLogin();}
  return r.ok?j:{error:j.error||'發生錯誤，請稍後再試',status:r.status};
}
function applyServer(st){
  if(!st||!st.member)return;
  SERVER=st;
  S.member={name:st.member.name,code:st.member.refCode,memberCode:st.member.code,picture:st.member.picture,needsProfile:st.member.needsProfile,firstVisit:st.member.firstVisit};
  S.fish=st.fish;
  S.hist=st.hist.map(h=>({at:Date.parse(h.at),d:h.d,label:h.label}));
  S.coupons=st.coupons.map(c=>({code:c.code,kind:c.kind,title:c.title,value:c.value,at:Date.parse(c.at),exp:Date.parse(c.exp),used:c.used,usedAt:c.usedAt?Date.parse(c.usedAt):null,minSpend:c.minSpend}));
  S.streak=st.streak||{n:0,last:''};
  const d=today();d.tasks={};Object.keys(st.today.tasks||{}).forEach(k=>{if(k!=='free_spin')d.tasks[k]=1});d.freeSpin=st.today.freeSpin?1:0;
  S.invites=st.invites||[];
  S.badges=S.badges||{};Object.entries(st.badges||{}).forEach(([m,v])=>{S.badges[m]=Object.assign(S.badges[m]||{},v)});
  save();
}
function needLogin(){if(SERVER)return false;openLogin();return true}
function refFromUrl(){try{return sessionStorage.getItem('hc_ref')||''}catch(e){return ''}}
function openLogin(ref){
  ref=ref||refFromUrl();
  sheet(`<div style="text-align:center"><svg width="56" height="56" aria-hidden="true"><use href="#coin"/></svg>
    <b class="h2" style="display:block;font-size:21px">加入芯彤的小角落</b>
    <p class="muted" style="margin:4px 0 16px">用 LINE 一鍵登入，加入就送 1 芯幣${ref?`<br>朋友邀請妳來，再送 NT$${CONFIG.referNewcomerNTD} 首次體驗券`:''}</p>
    <a class="btn line-btn btn-block" href="/api/login${ref?'?ref='+encodeURIComponent(ref):''}">用 LINE 登入</a>
    <p class="tiny" style="margin:12px 0 0">登入代表妳同意<a href="/privacy.html" target="_blank" rel="noopener">隱私權政策</a>。我們只會取得妳的 LINE 名稱與頭像。</p></div>`);
}
function openProfile(){
  const m=S.member||{};
  sheet(`<div style="text-align:center"><b class="h2" style="display:block;font-size:21px">歡迎來到小角落</b><p class="muted" style="margin:4px 0 14px">再填一點資料就完成了</p></div>
    <form id="profileForm" class="stack">
      <div class="field"><label for="pName">怎麼稱呼妳？</label><input id="pName" required maxlength="20" value="${esc(m.name||'')}"></div>
      <div class="field"><label for="pPhone">手機號碼（和預約時用的一樣）</label><input id="pPhone" required inputmode="tel" pattern="09[0-9]{8}" placeholder="0912345678"></div>
      <div class="field"><label for="pBday">妳的生日（選填，生日月有小驚喜）</label><input id="pBday" type="date"></div>
      <div class="field"><label for="pBaby">寶寶的生日或預產期（選填）</label><input id="pBaby" type="date"></div>
      <p class="tiny" style="margin:0" id="pErr"></p>
      <button class="btn btn-primary btn-block" type="submit">完成</button>
    </form>`);
  $('#profileForm').onsubmit=async e=>{e.preventDefault();const b=e.submitter||$('#profileForm button');b.disabled=true;
    const r=await api('profile',{name:$('#pName').value,phone:$('#pPhone').value,birthday:$('#pBday').value,babyBirthday:$('#pBaby').value});
    b.disabled=false;if(r.error){$('#pErr').textContent=r.error;return}
    applyServer(r);closeSheet();history.replaceState(null,'','#home');route='home';render(true);toast('歡迎加入！送妳 1 芯幣');setTimeout(maybeSpinPrompt,900);};
}
function qrSvg(text,size){try{const q=qrcode(0,'M');q.addData(text);q.make();return q.createSvgTag({cellSize:Math.max(2,Math.floor(size/(q.getModuleCount()+8))),margin:4,scalable:true})}catch(e){return `<p class="tiny">${esc(text)}</p>`}}
function showQr(title,url,code,note){sheet(`<div style="text-align:center"><b class="h3" style="display:block">${title}</b><div class="qr-box">${qrSvg(url,240)}</div><div class="t-code" style="font-family:var(--latin);font-size:20px;font-weight:600;letter-spacing:2px">${code}</div><p class="muted">${note}</p><button class="btn btn-ghost btn-block" data-close>關閉</button></div>`)}
function activeLots(){""")

rep("function balance(){return activeLots().reduce((s,l)=>s+l.rem,0)}", "function balance(){return SERVER?SERVER.coins:0}")

# ---------- 每日任務：伺服器發小魚乾 ----------
a = s.index("function claim(id,fromEl){"); b = s.index("\n}\n", a) + 3
s = s[:a] + r"""async function claim(id,fromEl){
  if(needLogin())return;
  const t=TASKS.find(x=>x.id===id);const d=today();
  if(d.tasks[id]||taskState(t)!=='ready')return;
  if(fromEl)fromEl.disabled=true;
  const r=await api('claim',{task:id});
  if(r.error){toast(r.error);if(fromEl)fromEl.disabled=false;return}
  applyServer(r.state);
  flyFish(fromEl,Math.min(r.gain,3));
  if(r.bonus)setTimeout(()=>toast(`連續報到 ${r.streak} 天！加送 ${r.bonus} 條小魚乾`),900);
  if(r.added<r.gain)toast('碗滿了！先去小屋餵貓咪吧');else toast(`領到 ${r.gain} 條小魚乾`);
  if(id==='checkin')setTimeout(checkBadges,1200);
  render();
}
""" + s[b:]

# ---------- 餵貓 ----------
a = s.index("function feed(n,btn){"); b = s.index("\nfunction flyTo(", a)
s = s[:a] + r"""async function feed(n,btn){
  if(needLogin())return;
  if(!S.fish){$('#houseTalk').textContent=pick(CAT_LINES.feedEmpty);return}
  n=Math.min(n,S.fish);if(btn)btn.disabled=true;
  const r=await api('feed',{n});
  if(r.error){toast(r.error);if(btn)btn.disabled=false;return}
  today().fed=(today().fed||0)+n;
  flyTo(btn,$('#petCat'),'fish',Math.min(n,4));
  setTimeout(()=>{
    const house=$('#house');if(house){house.classList.remove('purr');void house.offsetWidth;house.classList.add('purr');$('#houseTalk').textContent=pick(CAT_LINES.feed)}
    flyTo($('#petCat'),$('.wallet-chip'),'coin',Math.min(n,3));
    setTimeout(()=>{applyServer(r.state);toast(`貓咪吃了 ${n} 條，存入 ${c1(n*CONFIG.coinTenthsPerFeed)} 芯幣`);render()},900);
  },700);
}
""" + s[b:]

# ---------- 轉盤：伺服器決定獎項 ----------
a = s.index("function spinWheel(){"); b = s.index("\nfunction bestCoupons(", a)
s = s[:a] + r"""async function spinWheel(){
  if(wheelBusy)return;
  if(needLogin())return;
  const free=!today().freeSpin;
  if(!free&&balance()<WHEEL.cost*10){toast(`今天的免費轉盤用過了，再轉一次需要 ${WHEEL.cost} 芯幣`);return}
  wheelBusy=true;ac();
  const bt=$('#spinBtn');if(bt){bt.disabled=true;bt.textContent='轉動中…'}
  const res=await api('spin',{});
  if(res.error){wheelBusy=false;toast(res.error);if(bt){bt.disabled=false;bt.textContent='再試一次'}return}
  $('#chipCoin').textContent=c1(res.state.coins);
  const idx=res.idx;
  const n=WHEEL.prizes.length,segA=360/n;
  const start=wheelRot,base=start-(start%360);
  const target=base+360*6+(360-idx*segA)%360+(Math.random()*segA*.6-segA*.3);
  const svg=$('#wheelSvg'),dur=4600,t0=performance.now();let lastSeg=Math.floor((start+segA/2)/segA);
  const ease=x=>1-Math.pow(1-x,4);
  const frame=now2=>{
    const x=Math.min(1,(now2-t0)/dur),ang=start+(target-start)*ease(x);
    if(svg)svg.setAttribute('transform',`rotate(${ang%360} 150 150)`);
    const sg=Math.floor((ang+segA/2)/segA);if(sg!==lastSeg){lastSeg=sg;sfx('tick');const pt=$('#wheelPtr');if(pt){pt.classList.remove('kick');void pt.offsetWidth;pt.classList.add('kick')}}
    if(x<1)requestAnimationFrame(frame);else{wheelRot=target;finishSpin(res)}
  };
  requestAnimationFrame(frame);
}
function finishSpin(res){
  const pz=res.prize;let title='',detail='';
  if(pz.kind==='coupon'){title=`恭喜抽中 NT$${pz.value} 折價券！`;detail=`已放進「我的票券」，${WHEEL.couponDays} 天內到店出示折扣碼使用。`}
  else if(pz.kind==='fish'){title=`抽中小魚乾 ×${pz.value}！`;detail='已經放進點心碗，記得去小屋餵貓咪。'}
  else{title=`抽中芯幣 +${pz.value}！`;detail='已經存進妳的芯幣錢包。'}
  applyServer(res.state);sfx('flip');
  wheelBusy=false;render();
  sheet(`<div style="text-align:center"><div class="win-burst">${pz.kind==='coupon'?`<b>NT$${pz.value}</b><small>折價券</small>`:pz.kind==='fish'?`<svg width="64" height="64"><use href="#fish"/></svg>`:`<svg width="64" height="64"><use href="#coin"/></svg>`}</div>
    <b class="h2" style="display:block;font-size:21px;margin-top:12px">${title}</b><p class="muted">${detail}</p>
    <button class="btn btn-primary btn-block" data-close>好開心，收下了</button></div>`);
}
""" + s[b:]

# ---------- 兌換折抵券 ----------
rep("""  $('#confirmRedeem').onclick=()=>{
    if(!spendCoins(n*10,`兌換 NT$${n*CONFIG.coinValueNTD} 折抵券`)){toast('芯幣不足');return}
    const code=genCode('HSC');
    S.coupons.push({id:'c'+now(),kind:'redeem',title:`芯幣折抵 NT$${n*CONFIG.coinValueNTD}`,code,value:n*CONFIG.coinValueNTD,at:now(),exp:now()+CONFIG.redeemCodeDays*DAY,used:false});
    redeemPick=null;save();closeSheet();render();toast('兌換成功！到店時出示兌換碼');
  };""", """  $('#confirmRedeem').onclick=async()=>{
    const b=$('#confirmRedeem');b.disabled=true;
    const r=await api('redeem',{coins:n});
    if(r.error){toast(r.error);b.disabled=false;return}
    applyServer(r.state);redeemPick=null;closeSheet();render();toast('兌換成功！到店時出示折扣碼');
  };""")

# ---------- 加入會員改成 LINE 登入 ----------
a = s.index("/* 加入會員 sheet（正式版：LINE Login） */"); b = s.index("function sheet(html){", a)
s = s[:a] + "function openJoin(ref){openLogin(ref)}\n" + s[b:]

# ---------- 月度徽章：伺服器發獎勵 ----------
a = s.index("function checkBadges(){"); b = s.index("\nfunction viewBadges(", a)
s = s[:a] + r"""async function checkBadges(){
  if(!SERVER)return;
  const mk=monthKey();S.badges=S.badges||{};S.badges[mk]=S.badges[mk]||{};
  const b=BADGES.find(x=>!S.badges[mk][x.id]&&x.val()>=x.need);
  if(!b)return;
  const r=await api('badge',{id:b.id});
  if(r.error){if(r.status===409){S.badges[mk][b.id]=1;save()}return}
  applyServer(r.state);S.badges[mk][b.id]=1;save();sfx('flip');
  sheet(`<div style="text-align:center">${medalSvg({...b,done:true},110)}<b class="h2" style="display:block;font-size:21px;margin-top:8px">獲得徽章「${b.name}」！</b><p class="muted">${b.desc}，好厲害！貓咪送妳 ${BADGE_REWARD_FISH} 條小魚乾。</p><button class="btn btn-primary btn-block" data-close>收下徽章</button></div>`);
  if(route==='badges'||route==='home'){const y=scrollY;render();window.scrollTo(0,y)}
}
""" + s[b:]

# ---------- 芯幣頁：到期提醒改用伺服器資料、加上會員卡與 QR ----------
rep("""  const bal=balance(), exp=expiring();
  const expAmt=exp.reduce((s,l)=>s+l.rem,0);
  const nearest=exp.length?exp[0].exp:null;""", """  if(!SERVER)return sky('Heart coins','我的芯幣','每一枚芯幣，都是妳好好照顧自己的證明。','登入之後，貓咪就能幫妳存芯幣囉！')+`<div class="gutter stack" style="margin-top:-12px;position:relative;z-index:3"><section class="card login-card"><b class="h3">先用 LINE 登入</b><p class="muted" style="margin:0">登入後就能存芯幣、轉盤、兌換折價券。</p><button class="btn line-btn btn-block" data-login>用 LINE 登入</button></section></div>`;
  const bal=balance();
  const expAmt=SERVER.expiring?SERVER.expiring.tenths:0;
  const nearest=SERVER.expiring?Date.parse(SERVER.expiring.nearest):null;""")
rep("""    <section class="card redeem">""", """    <section class="card member-card">
      <div class="mc-qr" data-memberqr aria-label="顯示會員 QR Code">${qrSvg(location.origin+'/staff.html?m='+S.member.memberCode,120)}</div>
      <div><span class="eyebrow">Member card</span><b class="h3" style="display:block">${esc(S.member.name||'')}</b><div class="t-code" style="font-family:var(--latin);font-size:18px;font-weight:600;letter-spacing:1.5px">${S.member.memberCode}</div><p class="tiny" style="margin:4px 0 0">到店時給芯彤掃一下，確認到店、查詢芯幣</p></div>
    </section>

    <section class="card redeem">""")
# 票券加上 QR 按鈕
rep("""${c.used?'<span class="stamp">已使用</span>':''}</div>`).join('')""", """${c.used?'<span class="stamp">已使用</span>':''}${!c.used&&c.exp>now()?`<button class="t-qr" data-couponqr="${c.code}">QR</button>`:''}</div>`).join('')""")

# ---------- 首頁：未登入時顯示登入卡 ----------
rep("""    <section class="card today" aria-label="今天的進度">""", """    ${SERVER?'':`<section class="card login-card"><b class="h3">加入芯彤的小角落</b><p class="muted" style="margin:0">用 LINE 一鍵登入，每天做任務、餵貓咪、存芯幣換折價券。</p><button class="btn line-btn btn-block" data-login>用 LINE 登入</button></section>`}
    <section class="card today" aria-label="今天的進度">""")

# ---------- 綁定事件 ----------
rep("  const spb=$('#spinBtn');if(spb)spb.onclick=spinWheel;", """  const spb=$('#spinBtn');if(spb)spb.onclick=spinWheel;
  document.querySelectorAll('[data-login]').forEach(b=>b.onclick=()=>openLogin());
  const mq=$('[data-memberqr]');if(mq)mq.onclick=()=>showQr('我的會員卡',location.origin+'/staff.html?m='+S.member.memberCode,S.member.memberCode,'到店時請芯彤掃這個 QR Code');
  document.querySelectorAll('[data-couponqr]').forEach(b=>b.onclick=()=>showQr('折扣碼',location.origin+'/staff.html?c='+b.dataset.couponqr,b.dataset.couponqr,'結帳時請芯彤掃這個 QR Code'));""")

# ---------- 店家頁改到 staff.html，移除示範功能 ----------
rep("'articles','staff'];", "'articles'];")
rep("articles:viewArticles,staff:viewStaff};", "articles:viewArticles};")
rep("  bindStaff();\n", "")
rep('<div class="demo"><span>示範版：資料只存在這支手機</span><button id="resetDemo" type="button">重設示範資料</button><button type="button" data-go="staff">店家核銷頁</button></div>',
    '<div class="demo"><a href="/privacy.html">隱私權政策</a><a href="/staff.html">店家核銷</a><button id="logoutBtn" type="button" hidden>登出</button></div>')
a = s.index("$('#resetDemo').onclick=()=>{"); b = s.index("window.addEventListener('scroll'", a)
s = s[:a] + """$('#logoutBtn').onclick=async()=>{await api('logout',{});SERVER=null;S.member=null;S.coupons=[];S.hist=[];S.fish=0;save();render();toast('已登出')};
""" + s[b:]
rep("window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(h.startsWith('ref-')){openJoin(h.slice(4));return}",
    "window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);")

# ---------- 啟動：先問伺服器「我是誰」 ----------
a = s.index("// 啟動\n(function start(){"); b = s.index("})();", a) + 5
s = s[:a] + r"""// 啟動
(async function start(){
  const q=new URLSearchParams(location.search);
  const ref=(q.get('ref')||'').toUpperCase().replace(/[^A-Z0-9]/g,'');
  if(ref){try{sessionStorage.setItem('hc_ref',ref)}catch(e){};history.replaceState(null,'',location.pathname+location.hash)}
  const h=location.hash.slice(1);
  route=ROUTES.includes(h)?h:'home';
  render();
  const me=await api('me');
  if(me&&me.member){applyServer(me);$('#logoutBtn').hidden=false;render();
    if(me.member.needsProfile||h==='profile'){openProfile();return}
    setTimeout(maybeSpinPrompt,700);
  }else{
    if(h==='login-failed')toast('LINE 登入沒有成功，請再試一次');
    if(ref||h==='login-failed')setTimeout(()=>openLogin(ref),500);
  }
})();""" + s[b:]

# 文字：拿掉示範字樣
s = s.replace("${S.demo?'示範資料':''}", "")

# ---------- 樣式 ----------
rep("/* 店家核銷頁 */", """/* 正式版：登入卡、會員卡、QR */
.login-card{padding:18px;display:grid;gap:10px;margin-top:18px}
.member-card{display:grid;grid-template-columns:96px 1fr;gap:14px;align-items:center;padding:16px}
.mc-qr{width:96px;height:96px;padding:6px;background:#fff;border-radius:12px;border:1px solid var(--line);cursor:pointer}
.mc-qr svg,.qr-box svg{width:100%;height:100%;display:block}
.qr-box{width:min(240px,70vw);aspect-ratio:1;margin:14px auto;padding:10px;background:#fff;border-radius:16px;border:1px solid var(--line)}
.t-qr{position:absolute;right:10px;top:10px;font-size:11px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);background:#fff;color:var(--mauve-deep)}
.demo a{font-size:11.5px;color:var(--sub);text-decoration:underline;text-underline-offset:3px}

/* 店家核銷頁 */""")

# ---------- 組成完整 HTML 文件 ----------
split = s.index('<svg width="0" height="0"')
head, body = s[:split], s[split:]
doc = f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="芯彤美學 Heart studio 的會員小角落：每日任務、塔羅指引、漢芳療保養建議、芯幣與折價券。">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<script src="/assets/qrcode.js"></script>
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""
open(out, 'w', encoding='utf-8').write(doc)
print('ok', len(doc))
