// Local-only fake member state. Never serves real users or calls production.
export function previewFixture({ fish = 4, failFeed = false } = {}) {
  const state = {
    member: { name: '預覽會員', code: 'DEMO', refCode: 'DEMO', needsProfile: false, firstVisit: true },
    fish, coins: 0, hist: [], coupons: [], streak: { n: 0, last: '' },
    today: { tasks: { free_spin: true }, freeSpin: true }, invites: [], badges: {}, expiring: null
  };
  const calls = [];
  function handle(path, body = {}) {
    if (path === 'me') return { status: 200, data: structuredClone(state) };
    calls.push({ path, body });
    if (path === 'feed') {
      if (failFeed) { failFeed = false; return { status: 400, data: { error: '預覽：餵食暫時失敗，請再試一次' } }; }
      if (!Number.isInteger(body.n) || body.n < 1 || body.n > state.fish)
        return { status: 400, data: { error: '小魚乾不足' } };
      state.fish -= body.n;
      state.coins += body.n;
      state.hist.unshift({ at: new Date().toISOString(), d: body.n, label: '餵貓咪累積' });
      return { status: 200, data: { state: structuredClone(state) } };
    }
    if (path === 'claim' && body.task === 'pet' && !state.today.tasks.pet) {
      state.today.tasks.pet = true;
      state.fish = Math.min(30, state.fish + 1);
      return { status: 200, data: { gain: 1, added: 1, state: structuredClone(state) } };
    }
    return { status: 400, data: { error: '此預覽僅開放摸摸、餵食與摸摸任務' } };
  }
  return { state, calls, handle };
}
