p='/home/user/heart-corner/public/staff.html'
s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:60],s.count(a)); s=s.replace(a,b)

rep("""    <form class="card" id="findForm" style="margin-top:14px">
      <div class="field"><label for="code">輸入會員碼或折扣碼（或用手機相機掃客人的 QR Code）</label><input id="code" type="text" autocomplete="off" autocapitalize="characters" placeholder="例如 HSM-7K2M3P 或 HSL-7K2M-Q8PD"></div>
      <button class="btn btn-p" type="submit">查詢</button>
    </form>""","""    <section class="card scan-card" style="margin-top:14px">
      <button class="btn btn-scan" id="scanBtn" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M7 12h10"/></svg>掃描 QR Code</button>
      <div class="scan-view" id="scanView" hidden>
        <div class="scan-box"><video id="cam" playsinline muted></video><div class="scan-frame" aria-hidden="true"></div></div>
        <p class="scan-tip">把客人的會員卡或折扣碼 QR Code 對準框框</p>
        <button class="btn btn-g" id="scanStop" type="button">取消</button>
      </div>
      <p class="muted" id="scanErr"></p>
    </section>
    <form class="card" id="findForm" style="margin-top:14px">
      <div class="field"><label for="code">或手動輸入會員碼、折扣碼</label><input id="code" type="text" autocomplete="off" autocapitalize="characters" placeholder="例如 HSM-7K2M3P 或 HSL-7K2M-Q8PD"></div>
      <button class="btn btn-p" type="submit">查詢</button>
    </form>""")

rep(".toast{position:fixed;", """.btn-scan{display:flex;align-items:center;justify-content:center;gap:10px;height:64px;font-size:17px;background:var(--mauve-deep);color:#fff;border-radius:18px}
.btn-scan svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round}
.scan-view{position:relative;display:grid;gap:10px}
.scan-view video{width:100%;aspect-ratio:1;object-fit:cover;display:block;background:#2b2228}
.scan-box{position:relative;border-radius:16px;overflow:hidden}
.scan-frame{position:absolute;inset:19%;border:3px solid #fff;border-radius:18px;box-shadow:0 0 0 999px rgba(0,0,0,.3);pointer-events:none}
.scan-tip{margin:0;text-align:center;font-size:13.5px;color:var(--sub)}
.toast{position:fixed;""")

rep("<script>\n'use strict';", """<script src="/assets/jsqr.js"></script>
<script>
'use strict';""")

rep("function autoFind(){", r"""/* ---------- 掃描 QR Code ---------- */
let stream=null,scanning=false;
const canvas=document.createElement('canvas'),ctx2=canvas.getContext('2d',{willReadFrequently:true});
function codeFromText(t){
  try{const u=new URL(t);const v=u.searchParams.get('m')||u.searchParams.get('c');if(v)return v}catch(e){}
  const m=String(t).toUpperCase().match(/HS[MCLW]-[A-Z0-9-]+/);return m?m[0]:'';
}
async function startScan(){
  $('#scanErr').textContent='';
  if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){$('#scanErr').textContent='這支手機的瀏覽器不支援相機掃描，請改用手機相機 App 掃描，或手動輸入。';return}
  try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false})}
  catch(e){$('#scanErr').textContent='沒有取得相機權限。請到手機設定允許瀏覽器使用相機，或改用手動輸入。';return}
  const v=$('#cam');v.srcObject=stream;await v.play().catch(()=>{});
  $('#scanView').hidden=false;$('#scanBtn').hidden=true;scanning=true;requestAnimationFrame(tick);
}
function stopScan(){scanning=false;if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}$('#scanView').hidden=true;$('#scanBtn').hidden=false}
function tick(){
  if(!scanning)return;
  const v=$('#cam');
  if(v.readyState>=2&&v.videoWidth){
    const w=Math.min(640,v.videoWidth),h=Math.round(v.videoHeight*w/v.videoWidth);
    canvas.width=w;canvas.height=h;ctx2.drawImage(v,0,0,w,h);
    const img=ctx2.getImageData(0,0,w,h);
    const r=window.jsQR&&jsQR(img.data,w,h,{inversionAttempts:'dontInvert'});
    if(r&&r.data){const code=codeFromText(r.data);if(code){if(navigator.vibrate)navigator.vibrate(60);stopScan();toast('已掃描 '+code);find(code);return}}
  }
  requestAnimationFrame(tick);
}
$('#scanBtn').onclick=startScan;$('#scanStop').onclick=stopScan;
window.addEventListener('pagehide',stopScan);

function autoFind(){""")
open(p,'w',encoding='utf-8').write(s)
print('ok')
