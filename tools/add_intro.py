p='/home/user/heart-corner/public/index.html'
s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:60],s.count(a)); s=s.replace(a,b)

# 開場畫面（沿用原本小角落的水晶球歡迎影片）
rep("<body>\n", """<body>
<div class="intro-screen" id="introScreen" hidden aria-label="水晶球歡迎動畫">
  <video class="intro-video" id="introVideo" muted playsinline preload="auto" poster="/assets/intro-poster.webp" aria-hidden="true"><source src="/assets/welcome-intro.mp4" type="video/mp4"></video>
  <p class="intro-sr" id="introTranscript">嗨，妳來啦！今天過得還好嗎？歡迎回到芯彤的小角落。</p>
  <div class="intro-fallback" id="introFallback" hidden>
    <img src="/assets/hero-globe.webp" alt="水晶球裡的小貓正在向妳問好">
    <div class="intro-talk">嗨，妳來啦 ♡<br>今天過得還好嗎？</div>
  </div>
  <button type="button" class="intro-skip" id="introSkip">跳過開場</button>
</div>
""")

rep("/* 店家核銷頁 */", """/* 開場畫面 */
.intro-screen{position:fixed;inset:0;z-index:120;background:linear-gradient(180deg,#726f8a 0%,#726f8a 12%,#f5eae3 88%,#f5eae3 100%);display:grid;place-items:center;transition:opacity .6s ease}
.intro-screen.done{opacity:0;pointer-events:none}
.intro-video{width:min(100%,480px);height:100%;object-fit:contain;display:block}
.intro-video[hidden]{display:none!important}
.intro-sr{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}
.intro-fallback{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:30px 30px 90px}
.intro-fallback img{width:min(65vw,45svh,280px);border-radius:50%;filter:drop-shadow(0 15px 29px rgba(85,61,93,.25));animation:bob 3.5s ease-in-out infinite}
.intro-talk{padding:14px 26px;background:#fff9f3;border:1px solid #ebdcd5;border-radius:24px;box-shadow:0 12px 30px rgba(97,68,90,.13);text-align:center;font-size:18px;line-height:2;color:#795f67;letter-spacing:1.3px}
.intro-skip{position:absolute;right:max(20px,env(safe-area-inset-right,0px));bottom:calc(24px + env(safe-area-inset-bottom,0px));min-height:44px;padding:10px 20px;border-radius:28px;border:1px solid rgba(255,248,245,.6);background:rgba(255,250,246,.88);color:#816875;font-size:14px;letter-spacing:1px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
body.intro-open{overflow:hidden}

/* 店家核銷頁 */""")

# 開場邏輯：同一次瀏覽只播一次；從 LINE 登入回來、或直接打開某一頁時不播
rep("(async function start(){", r"""function playIntro(){
  return new Promise(resolve=>{
    const scr=$('#introScreen'),v=$('#introVideo'),fb=$('#introFallback'),skip=$('#introSkip');
    let seen=false;try{seen=sessionStorage.getItem('hc_intro')==='1'}catch(e){}
    const h=location.hash.slice(1);
    if(seen||(h&&h!=='home')||new URLSearchParams(location.search).has('noIntro')){resolve();return}
    try{sessionStorage.setItem('hc_intro','1')}catch(e){}
    let closed=false,guard;
    const close=()=>{if(closed)return;closed=true;clearTimeout(guard);v.pause();scr.classList.add('done');document.body.classList.remove('intro-open');setTimeout(()=>{scr.hidden=true;resolve()},600)};
    const fallback=()=>{if(closed||!fb.hidden)return;clearTimeout(guard);v.pause();v.hidden=true;fb.hidden=false;skip.textContent='進入小角落';guard=setTimeout(close,4000)};
    skip.onclick=close;
    scr.hidden=false;document.body.classList.add('intro-open');
    if(matchMedia('(prefers-reduced-motion: reduce)').matches){fallback();return}
    guard=setTimeout(fallback,4000);
    v.addEventListener('playing',()=>{clearTimeout(guard);guard=setTimeout(close,11000)},{once:true});
    v.addEventListener('ended',close);v.addEventListener('error',fallback);
    v.muted=true;const pr=v.play();if(pr)pr.catch(fallback);
  });
}

(async function start(){
  const introDone=playIntro();""")
rep("  const me=await api('me');\n  if(me&&me.member){", "  const me=await api('me');\n  await introDone;\n  if(me&&me.member){")
open(p,'w',encoding='utf-8').write(s)
print('ok')
