// 芯彤的小角落｜伺服器程式（Netlify Function）
// 所有跟芯幣、小魚乾、票券、邀請有關的計算都在這裡完成，客人的手機無法自行竄改。
import { createClient } from '@supabase/supabase-js';
import { SignJWT, jwtVerify } from 'jose';

export const config = { path: '/api/*' };

/* ---------------- 規則設定（要調整數字改這裡） ---------------- */
const RULES = {
  coinLifeDays: 365,
  bowlCap: 30,
  tasks: { checkin: 1, draw: 1, breath: 2, pet: 1, game: 2, oil: 1 },
  streakBonusFish: 3,
  redeemOptions: [20, 40, 60],         // 芯幣
  coinValueNTD: 5,
  redeemCodeDays: 30,
  couponPerNTD: 1000,
  maxDiscountNTD: 300,
  welcomeCoins: 1,
  welcomeCouponNTD: 100,
  welcomeCouponDays: 60,
  welcomeNeedsMinSpend: false,         // 新朋友體驗券不受滿千門檻限制
  referInviterCoins: 20,
  badgeFish: 5,
  badgeIds: ['streak', 'draw', 'water', 'game'],
  wheelCost: 10,
  wheelCouponDays: 30,
  wheel: [
    { label: 'NT$100', kind: 'coupon', value: 100, p: 2 },
    { label: '小魚乾×5', kind: 'fish', value: 5, p: 15 },
    { label: 'NT$50', kind: 'coupon', value: 50, p: 15 },
    { label: '小魚乾×1', kind: 'fish', value: 1, p: 28 },
    { label: 'NT$80', kind: 'coupon', value: 80, p: 5 },
    { label: '芯幣+3', kind: 'coin', value: 3, p: 10 },
    { label: 'NT$30', kind: 'coupon', value: 30, p: 25 }
  ]
};

/* ---------------- 共用工具 ---------------- */
const env = k => (typeof Netlify !== 'undefined' ? Netlify.env.get(k) : process.env[k]);
let _db;
const db = () => (_db ||= createClient(env('SUPABASE_URL'), env('SUPABASE_SERVICE_ROLE_KEY'), { auth: { persistSession: false } }));
const secret = () => new TextEncoder().encode(env('SESSION_SECRET'));
const site = () => (env('SITE_URL') || '').replace(/\/$/, '');
const DAY = 86400000;
const dayKey = (t = Date.now()) => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit' }).format(t);
const monthKey = () => dayKey().slice(0, 7);
const json = (data, status = 200, headers = {}) => new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers } });
const fail = (msg, status = 400) => json({ error: msg }, status);
const ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const rand = n => { const b = crypto.getRandomValues(new Uint8Array(n)); return [...b].map(x => ALPHA[x % ALPHA.length]).join(''); };
const couponCode = p => { const s = rand(8); return `${p}-${s.slice(0, 4)}-${s.slice(4)}`; };
function cookie(name, value, maxAge) { return `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`; }
function readCookie(req, name) { const m = (req.headers.get('cookie') || '').match(new RegExp('(?:^|; )' + name + '=([^;]+)')); return m ? m[1] : null; }
async function sign(payload, exp) { return new SignJWT(payload).setProtectedHeader({ alg: 'HS256' }).setIssuedAt().setExpirationTime(exp).sign(secret()); }
async function verify(token) { try { return (await jwtVerify(token, secret())).payload; } catch { return null; } }
async function member(req) { const t = readCookie(req, 'hc_session'); const p = t && await verify(t); return p && p.mid ? p.mid : null; }
async function isStaff(req) { const t = readCookie(req, 'hc_staff'); const p = t && await verify(t); return !!(p && p.staff); }
const yesterday = () => dayKey(Date.now() - DAY);

/* ---------------- 客人狀態 ---------------- */
async function state(mid) {
  const d = db(), now = new Date().toISOString(), today = dayKey(), mk = monthKey();
  const [{ data: m }, { data: lots }, { data: hist }, { data: coupons }, { data: claims }, { data: badges }, { data: invites }] = await Promise.all([
    d.from('members').select('*').eq('id', mid).single(),
    d.from('coin_lots').select('remaining,expires_at').eq('member_id', mid).gt('remaining', 0).gt('expires_at', now).order('expires_at'),
    d.from('coin_history').select('delta,label,created_at').eq('member_id', mid).order('created_at', { ascending: false }).limit(30),
    d.from('coupons').select('*').eq('member_id', mid).order('issued_at', { ascending: false }).limit(50),
    d.from('task_claims').select('task').eq('member_id', mid).eq('day', today),
    d.from('badge_claims').select('badge,month').eq('member_id', mid),
    d.from('members').select('display_name,first_visit_at,created_at').eq('referred_by', mid).order('created_at', { ascending: false })
  ]);
  if (!m) return null;
  const bal = (lots || []).reduce((a, l) => a + l.remaining, 0);
  const warnUntil = Date.now() + 30 * DAY;
  const exp = (lots || []).filter(l => new Date(l.expires_at).getTime() <= warnUntil);
  const taskMap = {}; (claims || []).forEach(c => { taskMap[c.task] = true; });
  const badgeMap = {}; (badges || []).forEach(b => { (badgeMap[b.month] ||= {})[b.badge] = true; });
  return {
    member: { name: m.display_name, picture: m.picture_url, code: m.member_code, refCode: m.referral_code, needsProfile: !m.phone, firstVisit: !!m.first_visit_at, birthday: m.birthday, babyBirthday: m.baby_birthday },
    fish: m.fish, coins: bal,
    expiring: exp.length ? { tenths: exp.reduce((a, l) => a + l.remaining, 0), nearest: exp[0].expires_at } : null,
    hist: (hist || []).map(h => ({ at: h.created_at, d: h.delta, label: h.label })),
    coupons: (coupons || []).map(c => ({ code: c.code, kind: c.kind, title: c.title, value: c.value, at: c.issued_at, exp: c.expires_at, used: !!c.used_at, usedAt: c.used_at, minSpend: c.needs_min_spend })),
    streak: { n: m.streak_last === today || m.streak_last === yesterday() ? m.streak_n : 0, last: m.streak_last },
    today: { day: today, tasks: taskMap, freeSpin: !!taskMap.free_spin },
    badges: badgeMap, month: mk,
    invites: (invites || []).map(i => ({ name: i.display_name || '新朋友', status: i.first_visit_at ? 'done' : 'wait' })),
    rules: { redeemOptions: RULES.redeemOptions, coinValueNTD: RULES.coinValueNTD, wheelCost: RULES.wheelCost, couponPerNTD: RULES.couponPerNTD, maxDiscountNTD: RULES.maxDiscountNTD, referInviterCoins: RULES.referInviterCoins, welcomeCouponNTD: RULES.welcomeCouponNTD }
  };
}

/* ---------------- LINE 登入 ---------------- */
async function login(req) {
  const url = new URL(req.url);
  const ref = (url.searchParams.get('ref') || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
  const nonce = rand(16);
  const st = await sign({ ref, nonce }, '10m');
  const auth = new URL('https://access.line.me/oauth2/v2.1/authorize');
  auth.search = new URLSearchParams({ response_type: 'code', client_id: env('LINE_CHANNEL_ID'), redirect_uri: `${site()}/api/callback`, state: st, scope: 'openid profile', nonce }).toString();
  return new Response(null, { status: 302, headers: { location: auth.toString(), 'set-cookie': cookie('hc_nonce', nonce, 600) } });
}

async function callback(req) {
  const url = new URL(req.url);
  const code = url.searchParams.get('code'), st = await verify(url.searchParams.get('state') || '');
  if (!code || !st || st.nonce !== readCookie(req, 'hc_nonce')) return new Response(null, { status: 302, headers: { location: `${site()}/#login-failed` } });
  const tok = await fetch('https://api.line.me/oauth2/v2.1/token', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: `${site()}/api/callback`, client_id: env('LINE_CHANNEL_ID'), client_secret: env('LINE_CHANNEL_SECRET') }) }).then(r => r.json());
  if (!tok.id_token) return new Response(null, { status: 302, headers: { location: `${site()}/#login-failed` } });
  const prof = await fetch('https://api.line.me/oauth2/v2.1/verify', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ id_token: tok.id_token, client_id: env('LINE_CHANNEL_ID'), nonce: st.nonce }) }).then(r => r.json());
  if (!prof.sub) return new Response(null, { status: 302, headers: { location: `${site()}/#login-failed` } });

  const d = db();
  let { data: m } = await d.from('members').select('id,phone').eq('line_user_id', prof.sub).maybeSingle();
  if (!m) {
    let referrer = null;
    if (st.ref) { const { data: r } = await d.from('members').select('id').eq('referral_code', st.ref).maybeSingle(); referrer = r ? r.id : null; }
    for (let i = 0; i < 5 && !m; i++) {
      const { data, error } = await d.from('members').insert({
        line_user_id: prof.sub, display_name: prof.name || '', picture_url: prof.picture || null,
        member_code: 'HSM-' + rand(6), referral_code: 'HS' + rand(5), referred_by: referrer
      }).select('id,phone').single();
      if (!error) m = data;
    }
    if (!m) return new Response(null, { status: 302, headers: { location: `${site()}/#login-failed` } });
    await d.rpc('add_coins', { p_member: m.id, p_tenths: RULES.welcomeCoins * 10, p_label: '加入會員禮', p_merge: null, p_days: RULES.coinLifeDays });
    if (referrer) await d.from('coupons').insert({ member_id: m.id, code: couponCode('HSW'), kind: 'welcome', title: '新朋友首次體驗券', value: RULES.welcomeCouponNTD, needs_min_spend: RULES.welcomeNeedsMinSpend, expires_at: new Date(Date.now() + RULES.welcomeCouponDays * DAY).toISOString() });
  } else {
    await d.from('members').update({ picture_url: prof.picture || null }).eq('id', m.id);
  }
  const session = await sign({ mid: m.id }, '30d');
  return new Response(null, { status: 302, headers: [['location', `${site()}/#${m.phone ? 'home' : 'profile'}`], ['set-cookie', cookie('hc_session', session, 30 * 86400)], ['set-cookie', cookie('hc_nonce', '', 0)]] });
}

/* ---------------- 客人操作 ---------------- */
async function profile(mid, body) {
  const name = String(body.name || '').trim().slice(0, 20);
  const phone = String(body.phone || '').replace(/\D/g, '');
  if (!name) return fail('請填寫稱呼');
  if (!/^09\d{8}$/.test(phone)) return fail('手機號碼格式不正確，請輸入 09 開頭的 10 碼');
  const okDate = v => (v && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : null);
  const { error } = await db().from('members').update({ display_name: name, phone, birthday: okDate(body.birthday), baby_birthday: okDate(body.babyBirthday) }).eq('id', mid);
  if (error) return fail('儲存失敗，請稍後再試', 500);
  return json(await state(mid));
}

async function claim(mid, body) {
  const task = String(body.task || '');
  const fish = RULES.tasks[task];
  if (fish === undefined) return fail('沒有這個任務');
  const d = db(), today = dayKey();
  const { error } = await d.from('task_claims').insert({ member_id: mid, day: today, task, fish });
  if (error) return fail('今天已經領過了', 409);
  const { data: m } = await d.from('members').select('fish,streak_n,streak_last').eq('id', mid).single();
  let gain = fish, bonus = 0, streak = m.streak_n;
  const patch = {};
  if (task === 'checkin') {
    streak = m.streak_last === yesterday() ? m.streak_n + 1 : (m.streak_last === today ? m.streak_n : 1);
    patch.streak_n = streak; patch.streak_last = today;
    if (streak % 7 === 0) { bonus = RULES.streakBonusFish; gain += bonus; }
  }
  const added = Math.max(0, Math.min(gain, RULES.bowlCap - m.fish));
  patch.fish = m.fish + added;
  await d.from('members').update(patch).eq('id', mid);
  return json({ gain, added, bonus, streak, state: await state(mid) });
}

async function feed(mid, body) {
  const n = Math.max(1, Math.min(RULES.bowlCap, parseInt(body.n) || 1));
  const { data: ok } = await db().rpc('feed_cat', { p_member: mid, p_n: n, p_day: dayKey() });
  if (!ok) return fail('小魚乾不夠');
  return json({ fed: n, state: await state(mid) });
}

async function spin(mid) {
  const d = db();
  const { error } = await d.from('task_claims').insert({ member_id: mid, day: dayKey(), task: 'free_spin', fish: 0 });
  const free = !error;
  if (!free) {
    const { data: ok } = await d.rpc('spend_coins', { p_member: mid, p_tenths: RULES.wheelCost * 10, p_label: '幸運轉盤' });
    if (!ok) return fail(`今天的免費次數用完了，再轉一次需要 ${RULES.wheelCost} 芯幣`);
  }
  const tot = RULES.wheel.reduce((a, b) => a + b.p, 0);
  const r = crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32 * tot;
  let acc = 0, idx = 0;
  for (; idx < RULES.wheel.length; idx++) { acc += RULES.wheel[idx].p; if (r < acc) break; }
  const pz = RULES.wheel[idx];
  let coupon = null;
  if (pz.kind === 'coupon') {
    coupon = couponCode('HSL');
    await d.from('coupons').insert({ member_id: mid, code: coupon, kind: 'wheel', title: `轉盤折價券 NT$${pz.value}`, value: pz.value, expires_at: new Date(Date.now() + RULES.wheelCouponDays * DAY).toISOString() });
  } else if (pz.kind === 'fish') {
    const { data: m } = await d.from('members').select('fish').eq('id', mid).single();
    await d.from('members').update({ fish: Math.min(RULES.bowlCap, m.fish + pz.value) }).eq('id', mid);
  } else {
    await d.rpc('add_coins', { p_member: mid, p_tenths: pz.value * 10, p_label: '幸運轉盤獎勵', p_merge: null, p_days: RULES.coinLifeDays });
  }
  return json({ idx, free, prize: { kind: pz.kind, value: pz.value }, coupon, state: await state(mid) });
}

async function redeem(mid, body) {
  const coins = parseInt(body.coins);
  if (!RULES.redeemOptions.includes(coins)) return fail('兌換數量不正確');
  const ntd = coins * RULES.coinValueNTD;
  const { data: ok } = await db().rpc('spend_coins', { p_member: mid, p_tenths: coins * 10, p_label: `兌換 NT$${ntd} 折抵券` });
  if (!ok) return fail('芯幣不夠');
  const code = couponCode('HSC');
  await db().from('coupons').insert({ member_id: mid, code, kind: 'redeem', title: `芯幣折抵 NT$${ntd}`, value: ntd, expires_at: new Date(Date.now() + RULES.redeemCodeDays * DAY).toISOString() });
  return json({ code, state: await state(mid) });
}

async function badge(mid, body) {
  const id = String(body.id || '');
  if (!RULES.badgeIds.includes(id)) return fail('沒有這個徽章');
  const d = db();
  const { error } = await d.from('badge_claims').insert({ member_id: mid, month: monthKey(), badge: id });
  if (error) return fail('這個月已經領過了', 409);
  const { data: m } = await d.from('members').select('fish').eq('id', mid).single();
  await d.from('members').update({ fish: Math.min(RULES.bowlCap, m.fish + RULES.badgeFish) }).eq('id', mid);
  return json({ fish: RULES.badgeFish, state: await state(mid) });
}

/* ---------------- 店家 ---------------- */
async function staffLogin(body) {
  const pin = env('STAFF_PIN');
  if (!pin || String(body.pin || '') !== pin) return fail('密碼不正確', 401);
  return json({ ok: true }, 200, { 'set-cookie': cookie('hc_staff', await sign({ staff: true }, '12h'), 12 * 3600) });
}

function couponStatus(c) { if (c.used_at) return 'used'; if (new Date(c.expires_at).getTime() < Date.now()) return 'expired'; return 'valid'; }

async function staffCoupon(url) {
  const code = (url.searchParams.get('code') || '').toUpperCase().replace(/\s/g, '');
  const { data: c } = await db().from('coupons').select('*, members(display_name, member_code)').eq('code', code).maybeSingle();
  if (!c) return json({ found: false });
  return json({ found: true, status: couponStatus(c), coupon: { code: c.code, kind: c.kind, title: c.title, value: c.value, minSpend: c.needs_min_spend, issued: c.issued_at, expires: c.expires_at, usedAt: c.used_at, usedSpend: c.used_spend }, member: { name: c.members?.display_name, code: c.members?.member_code } });
}

async function staffRedeem(body) {
  const d = db();
  const code = String(body.code || '').toUpperCase().replace(/\s/g, '');
  const spend = parseInt(body.spend) || 0;
  const { data: c } = await d.from('coupons').select('*').eq('code', code).maybeSingle();
  if (!c) return fail('查無此折扣碼', 404);
  const st = couponStatus(c);
  if (st !== 'valid') return fail(st === 'used' ? '這張已經使用過了' : '這張已經過期了', 409);
  if (body.birthday) return fail('這筆消費已使用生日優惠，折價券不能同時使用');
  // 同一位客人、同一筆消費（3 小時內、相同金額）已經用了幾張
  const since = new Date(Date.now() - 3 * 3600 * 1000).toISOString();
  const { data: same } = await d.from('coupons').select('value').eq('member_id', c.member_id).eq('used_spend', spend).gt('used_at', since);
  const usedN = (same || []).length, usedSum = (same || []).reduce((a, x) => a + x.value, 0);
  if (c.needs_min_spend) {
    if (!spend) return fail('請輸入這次的消費金額');
    const allow = Math.floor(spend / RULES.couponPerNTD);
    if (allow < 1) return fail(`消費未滿 NT$${RULES.couponPerNTD.toLocaleString()}，不能使用這張折價券`);
    if (usedN >= allow) return fail(`這筆消費最多可用 ${allow} 張，已經用了 ${usedN} 張`);
  }
  if (usedSum + c.value > RULES.maxDiscountNTD) return fail(`超過單筆折抵上限 NT$${RULES.maxDiscountNTD}（這筆已折 NT$${usedSum}）`);
  const { data: upd } = await d.from('coupons').update({ used_at: new Date().toISOString(), used_spend: spend }).eq('id', c.id).is('used_at', null).select('id');
  if (!upd || !upd.length) return fail('這張剛剛已被使用', 409);
  await d.from('staff_log').insert({ action: 'redeem', member_id: c.member_id, coupon_code: c.code, amount: c.value, note: spend ? `消費 ${spend}` : null });
  return json({ ok: true, value: c.value, note: `小角落折價券 ${c.code} 折 NT$${c.value}` });
}

async function staffMember(url) {
  const code = (url.searchParams.get('code') || '').toUpperCase().replace(/\s/g, '');
  const d = db();
  const { data: m } = await d.from('members').select('id,display_name,member_code,phone,first_visit_at,referred_by,created_at').eq('member_code', code).maybeSingle();
  if (!m) return json({ found: false });
  const [{ data: ref }, { data: cps }, { data: lots }] = await Promise.all([
    m.referred_by ? d.from('members').select('display_name').eq('id', m.referred_by).single() : Promise.resolve({ data: null }),
    d.from('coupons').select('code,title,value,expires_at,used_at,needs_min_spend').eq('member_id', m.id).is('used_at', null).gt('expires_at', new Date().toISOString()),
    d.from('coin_lots').select('remaining').eq('member_id', m.id).gt('remaining', 0).gt('expires_at', new Date().toISOString())
  ]);
  return json({ found: true, member: { name: m.display_name, code: m.member_code, phoneTail: m.phone ? m.phone.slice(-3) : '', firstVisit: m.first_visit_at, joined: m.created_at, referrer: ref?.display_name || null, coins: (lots || []).reduce((a, l) => a + l.remaining, 0) }, coupons: cps || [] });
}

async function staffFirstVisit(body) {
  const d = db();
  const code = String(body.code || '').toUpperCase().replace(/\s/g, '');
  const { data: m } = await d.from('members').select('id,display_name,first_visit_at,referred_by,referral_rewarded').eq('member_code', code).maybeSingle();
  if (!m) return fail('查無此會員', 404);
  if (m.first_visit_at) return fail('這位會員之前已經確認過首次到店', 409);
  await d.from('members').update({ first_visit_at: new Date().toISOString() }).eq('id', m.id).is('first_visit_at', null);
  let rewarded = null;
  if (m.referred_by && !m.referral_rewarded) {
    const { data: upd } = await d.from('members').update({ referral_rewarded: true }).eq('id', m.id).eq('referral_rewarded', false).select('id');
    if (upd && upd.length) {
      await d.rpc('add_coins', { p_member: m.referred_by, p_tenths: RULES.referInviterCoins * 10, p_label: `好友 ${m.display_name || ''} 完成首次到店`, p_merge: null, p_days: RULES.coinLifeDays });
      const { data: r } = await d.from('members').select('display_name').eq('id', m.referred_by).single();
      rewarded = r?.display_name || '邀請人';
    }
  }
  await d.from('staff_log').insert({ action: 'first_visit', member_id: m.id, note: rewarded ? `邀請人 ${rewarded} +${RULES.referInviterCoins} 芯幣` : null });
  return json({ ok: true, name: m.display_name, rewarded, coins: RULES.referInviterCoins });
}

async function staffToday() {
  const start = new Date(`${dayKey()}T00:00:00+08:00`).toISOString();
  const { data } = await db().from('staff_log').select('action,coupon_code,amount,note,created_at,members(display_name)').gt('created_at', start).order('created_at', { ascending: false });
  return json({ log: (data || []).map(x => ({ action: x.action, code: x.coupon_code, amount: x.amount, note: x.note, at: x.created_at, name: x.members?.display_name })) });
}

/* ---------------- 路由 ---------------- */
export default async (req) => {
  const url = new URL(req.url);
  const path = url.pathname.replace(/^\/api\//, '');
  const method = req.method;
  const body = method === 'POST' ? await req.json().catch(() => ({})) : {};
  try {
    if (path === 'login') return login(req);
    if (path === 'callback') return callback(req);
    if (path === 'logout' && method === 'POST') return json({ ok: true }, 200, { 'set-cookie': cookie('hc_session', '', 0) });

    if (path.startsWith('staff/')) {
      const sp = path.slice(6);
      if (sp === 'login' && method === 'POST') return staffLogin(body);
      if (sp === 'logout' && method === 'POST') return json({ ok: true }, 200, { 'set-cookie': cookie('hc_staff', '', 0) });
      if (!(await isStaff(req))) return fail('請先登入店家帳號', 401);
      if (sp === 'check') return json({ ok: true });
      if (sp === 'coupon') return staffCoupon(url);
      if (sp === 'redeem' && method === 'POST') return staffRedeem(body);
      if (sp === 'member') return staffMember(url);
      if (sp === 'first-visit' && method === 'POST') return staffFirstVisit(body);
      if (sp === 'today') return staffToday();
      return fail('not found', 404);
    }

    const mid = await member(req);
    if (!mid) return fail('請先登入', 401);
    if (path === 'me') { const s = await state(mid); return s ? json(s) : fail('請先登入', 401); }
    if (method !== 'POST') return fail('not found', 404);
    if (path === 'profile') return profile(mid, body);
    if (path === 'claim') return claim(mid, body);
    if (path === 'feed') return feed(mid, body);
    if (path === 'spin') return spin(mid);
    if (path === 'redeem') return redeem(mid, body);
    if (path === 'badge') return badge(mid, body);
    return fail('not found', 404);
  } catch (e) {
    console.error(e);
    return fail('系統忙碌中，請稍後再試', 500);
  }
};
