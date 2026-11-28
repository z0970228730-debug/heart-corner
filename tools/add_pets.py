# 讓客人選擇陪伴的小動物（貓咪／兔兔）
import re
p='/home/user/heart-corner/public/index.html'
s=open(p,encoding='utf-8').read()
def rep(a,b,cnt=1):
    global s
    n=s.count(a); assert n==cnt,(a[:70],n); s=s.replace(a,b)

# ---------- 資料與工具 ----------
rep("""  invite:['把小角落分享給也需要被照顧的朋友吧！'],
};""","""  invite:['把小角落分享給也需要被照顧的朋友吧！'],
};

/* 陪伴的小動物：之後新增動物時，在 PETS 加一筆、放好圖片即可 */
const PETS={
  cat:{id:'cat',name:'貓咪',img:{window:'assets/cat-window.webp',rest:'assets/cat-rest.webp',letter:'assets/cat-letter.webp',oil:'assets/cat-oil.webp',globe:'assets/hero-globe.webp'},video:true,globe:false},
  rabbit:{id:'rabbit',name:'兔兔',img:{window:'assets/pet-rabbit.webp',rest:'assets/pet-rabbit.webp',letter:'assets/pet-rabbit.webp',oil:'assets/pet-rabbit.webp',globe:'assets/pet-rabbit.webp'},video:false,globe:true}
};
const RABBIT_LINES={
  cat:['在毛毯上窩著，等妳來坐一下。','摸摸我的頭，我的耳朵會輕輕動喔。'],
  pet:['嗯～好舒服。','再摸一下下嘛～','妳的手好溫暖。','（耳朵輕輕抖了一下）','今天有妳陪，真好。'],
  feed:['好香的小胡蘿蔔！謝謝妳～','喀滋喀滋……這根特別甜！','吃飽了，幫妳存了一點芯幣喔。'],
  feedEmpty:['盤子空空的……去做個小任務帶點小胡蘿蔔回來好嗎？']
};
const PET_SWAP={rabbit:[['貓咪小屋','兔兔小屋'],['小貓咪','小兔兔'],['小貓','小兔'],['貓咪','兔兔'],['餵貓','餵兔'],['摸貓','摸兔'],['橘白','白色'],['貓','兔'],['小魚乾','小胡蘿蔔'],['魚乾','胡蘿蔔'],['點心碗','點心盤'],['呼嚕聲','音效'],['喵一聲','叫一聲'],['喵～','啾～'],['呼嚕給妳聽','動動耳朵給妳看']]};
function pet(){return PETS[S.pet]||PETS.cat}
function petImg(k){return pet().img[k]}
function petLines(k){return (S.pet==='rabbit'&&RABBIT_LINES[k])||CAT_LINES[k]}
function petStr(t){
  const sw=PET_SWAP[S.pet];if(!sw||!t)return t;
  for(const [a,b] of sw)t=t.split(a).join(b);
  return t.replace(/(\\d+)\\s?條/g,'$1 根');
}
function petText(root){
  if(!PET_SWAP[S.pet]||!root)return;
  const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;
  while((n=w.nextNode())){const v=petStr(n.nodeValue);if(v!==n.nodeValue)n.nodeValue=v}
  root.querySelectorAll('[alt],[aria-label],[placeholder],[title]').forEach(el=>{for(const a of ['alt','aria-label','placeholder','title']){const v=el.getAttribute(a);if(v){const x=petStr(v);if(x!==v)el.setAttribute(a,x)}}});
}
const FISH_SVG=null;
function applyPetSymbol(){
  const sym=document.getElementById('fish');if(!sym)return;
  if(!sym.dataset.orig)sym.dataset.orig=sym.innerHTML;
  sym.innerHTML=S.pet==='rabbit'?'<path d="M7 26 L21 9 Q26 6 25.5 11 L9 27.5 Q5 29.5 7 26Z" fill="#e8873a" stroke="#c0662a" stroke-width="1"/><path d="M12.5 20.5l2.2 1.8M16 16.5l2.2 1.8M19 12.8l1.8 1.6" stroke="#c0662a" stroke-width="1.1" stroke-linecap="round"/><path d="M22.5 8.5l1-5M24 9.5l5-2.2M23.4 9l4.2-4.5" stroke="#7aa35a" stroke-width="2.2" stroke-linecap="round"/>':sym.dataset.orig;
  document.body.classList.toggle('pet-globe',!!pet().globe);
}
function petPicker(){
  return `<div class="pet-pick" role="group" aria-label="選擇陪伴妳的小動物">${Object.values(PETS).map(x=>`<button type="button" data-pet="${x.id}" aria-pressed="${(S.pet||'cat')===x.id}"><img src="${x.img.rest}" alt=""><span>${x.name}</span></button>`).join('')}</div>`;
}""")

# ---------- 圖片改成跟著小動物 ----------
s=s.replace('<div class="talk-cat"><img src="assets/cat-rest.webp" alt=""></div>','<div class="talk-cat"><img src="${petImg(\'rest\')}" alt=""></div>')
rep('<img class="hero-img" src="assets/cat-window.webp"','<img class="hero-img" src="${petImg(\'window\')}"')
rep('<button class="tile" data-go="cards"><img src="assets/cat-letter.webp"','<button class="tile" data-go="cards"><img src="${petImg(\'letter\')}"')
rep('<button class="tile" data-go="cat"><img src="assets/cat-rest.webp"','<button class="tile" data-go="cat"><img src="${petImg(\'rest\')}"')
rep('<button class="tile" data-go="play"><img src="assets/cat-oil.webp"','<button class="tile" data-go="play"><img src="${petImg(\'oil\')}"')
rep('<button class="tile" data-go="mom"><img src="assets/hero-globe.webp"','<button class="tile" data-go="mom"><img src="${petImg(\'globe\')}"')
rep('<img src="assets/hero-globe.webp" alt="水晶球裡的溫室，小貓在裡面睡覺" loading="lazy">','<img src="${petImg(\'globe\')}" alt="水晶球裡的溫室，小貓在裡面睡覺" loading="lazy">')
rep('<div class="warm-art"><img src="assets/cat-letter.webp"','<div class="warm-art"><img src="${petImg(\'letter\')}"')
rep('sheet(`<div style="text-align:center"><img src="assets/cat-oil.webp"','sheet(`<div style="text-align:center"><img src="${petImg(\'oil\')}"')

# 小屋：兔兔還沒有動畫，先用圖片
a=s.index('      <video id="petCat" class="cat-vid"'); b=s.index('</video>', s.index('id="catPetVid"'))+len('</video>')
old=s[a:b]
s=s[:a]+"${pet().video?`"+old.strip()+"`:`<img id=\"petCat\" class=\"cat-vid\" src=\"${petImg('rest')}\" alt=\"小動物在毛毯上休息，點一下可以摸摸牠\">`}"+s[b:]

# 小屋頂端加上選擇
rep("""  return sky('Cat house','貓咪小屋','摸摸牠、餵牠吃小魚乾，貓咪會幫妳存芯幣。',pick(CAT_LINES.cat))+`
  <div class="gutter stack" style="margin-top:-12px;position:relative;z-index:3">""","""  return sky('Cat house','貓咪小屋','摸摸牠、餵牠吃小魚乾，貓咪會幫妳存芯幣。',pick(petLines('cat')))+`
  <div class="gutter stack" style="margin-top:-12px;position:relative;z-index:3">
    <section class="card pet-card"><div class="rv-q"><b>陪伴我的小動物</b><small>隨時可以換，芯幣不受影響</small></div>${petPicker()}</section>""")

# 台詞改成跟著小動物
s=re.sub(r"pick\(CAT_LINES\.(\w+)\)", r"pick(petLines('\1'))", s)

# 摸摸的聲音：兔兔用輕柔的音效
rep("    if(S.sound){ac();const a=$('#purr');","    if(S.sound&&S.pet==='rabbit'){ac();sfx('soft')}\n    else if(S.sound){ac();const a=$('#purr');")
rep("  else if(kind==='meow'){","  else if(kind==='soft'){[660,990].forEach((f,i)=>tone(t+i*.12,f,.5,.05))}\n  else if(kind==='meow'){")

# 第一次填資料時也可以選
rep("""      <div class="field"><label for="pBday">妳的生日（選填，生日月有小驚喜）</label>""","""      <div class="field"><label>選一位陪伴妳的小動物</label>${petPicker()}</div>
      <div class="field"><label for="pBday">妳的生日（選填，生日月有小驚喜）</label>""")

# 套用：畫面、視窗、提示文字
rep("  bind();\n}\n\nfunction bind(){","  applyPetSymbol();petText($('#main'));petText($('.topbar'));petText($('#nav'));\n  bind();\n}\n\nfunction bind(){")
rep("""  $('#sheetBg').onclick=e=>{if(e.target.id==='sheetBg'||e.target.closest('[data-close]'))closeSheet()};""","""  $('#sheetBg').onclick=e=>{if(e.target.id==='sheetBg'||e.target.closest('[data-close]'))closeSheet()};
  petText($('#sheetRoot'));bindPetPick($('#sheetRoot'));""")
rep("function toast(msg){const t=$('#toast');t.textContent=msg;","function toast(msg){const t=$('#toast');t.textContent=petStr(msg);")
rep("function catSay(text){const b=$('#catTalk');if(!b)return;b.classList.remove('pop');void b.offsetWidth;b.innerHTML=text;","function catSay(text){const b=$('#catTalk');if(!b)return;b.classList.remove('pop');void b.offsetWidth;b.innerHTML=petStr(text);")
rep("  // cat\n  const pc=$('#petCat');","""  bindPetPick(document);
  // cat
  const pc=$('#petCat');""")
rep("    $('#houseTalk').textContent=pick(petLines('pet'));","    $('#houseTalk').textContent=petStr(pick(petLines('pet')));")
rep("function closeSheet(){","""function bindPetPick(root){
  root.querySelectorAll('[data-pet]').forEach(b=>b.onclick=()=>{
    S.pet=b.dataset.pet;save();
    const inSheet=!!b.closest('#sheetRoot');
    if(inSheet){root.querySelectorAll('[data-pet]').forEach(x=>x.setAttribute('aria-pressed',x===b))}
    const y=scrollY;render();window.scrollTo(0,y);
    if(!inSheet)toast(`現在陪伴妳的是${pet().name} ♡`);
  });
}
function closeSheet(){""")

# 開場：選了兔兔就不播貓咪影片
rep("    scr.hidden=false;document.body.classList.add('intro-open');","""    scr.hidden=false;document.body.classList.add('intro-open');
    if(pet().id!=='cat'){fb.querySelector('img').src='/'+petImg('globe');fb.querySelector('img').alt='水晶球裡的'+pet().name+'正在向妳問好';fallback();return}""")

# ---------- 樣式 ----------
rep("/* 開場畫面 */","""/* 小動物選擇 */
.pet-card{padding:16px 18px;display:grid;gap:10px}
.pet-pick{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:10px}
.pet-pick button{display:grid;justify-items:center;gap:4px;padding:10px 6px;border-radius:var(--r-md);border:1.5px solid var(--line);background:#fff;font-size:14px}
.pet-pick img{width:56px;height:56px;border-radius:50%;object-fit:cover}
.pet-pick button[aria-pressed="true"]{border-color:var(--rose);background:#fbf1ee;font-weight:500}
.pet-globe .hero-img,.pet-globe .tile img,.pet-globe .warm-art img,.pet-globe .house .cat-vid,.pet-globe .studio img{object-fit:contain;background:linear-gradient(180deg,#8d879e,#e9dcd6)}
.pet-globe .talk-cat img{transform:scale(1.25);object-position:50% 50%}

/* 開場畫面 */""")
open(p,'w',encoding='utf-8').write(s)
print('ok', s.count("petImg("), s.count("CAT_LINES."))
