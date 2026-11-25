import test from 'node:test';
import assert from 'node:assert/strict';
import '../public/assets/cat-motion.js';

function harness(reduced = false) {
  let time = 0, next = 0;
  const jobs = new Map(), poses = [];
  const motion = globalThis.CatMotion.create({
    onPose: (pose) => poses.push(pose),
    reduced,
    random: () => 0,
    setTimer: (fn, delay) => { jobs.set(++next, { fn, at: time + delay }); return next; },
    clearTimer: (id) => jobs.delete(id)
  });
  function advance(ms) {
    const until = time + ms;
    while (true) {
      const job = [...jobs.entries()].sort((a, b) => a[1].at - b[1].at)[0];
      if (!job || job[1].at > until) break;
      time = job[1].at;
      jobs.delete(job[0]);
      job[1].fn();
    }
    time = until;
  }
  return { motion, poses, jobs, advance };
}

test('idle moves from breathing to curious ears and tail, slow blink, then rest', () => {
  const h = harness();
  assert.deepEqual(h.poses, ['rest']);
  h.advance(20000);
  assert.deepEqual(h.poses.slice(0, 4), ['rest', 'curious', 'blink', 'rest']);
  h.motion.destroy();
  assert.equal(h.jobs.size, 0);
});

test('pet reactions vary and a new pet replaces an older reaction', () => {
  const h = harness();
  assert.equal(h.motion.pet(), 'purr');
  assert.equal(h.motion.pet(), 'stretch');
  assert.equal(h.motion.pet(), 'greet');
  assert.equal(h.poses.at(-1), 'curious');
  h.advance(5000);
  assert.equal(h.poses.at(-1), 'rest');
  assert.equal(h.jobs.size, 1);
});

test('feeding a single fish has a complete three-stage reaction', async () => {
  const h = harness();
  const done = h.motion.feed(1);
  assert.equal(h.poses.at(-1), 'anticipate');
  h.advance(700);
  assert.equal(h.poses.at(-1), 'nibble');
  h.advance(1000);
  assert.equal(h.poses.at(-1), 'satisfied');
  h.advance(2000);
  assert.equal(await done, true);
  assert.equal(h.poses.at(-1), 'rest');
});

test('feeding several fish has a different sequence and cannot overlap', async () => {
  const h = harness();
  const done = h.motion.feed(4);
  assert.equal(h.motion.pet(), null);
  assert.equal(await h.motion.feed(1), false);
  h.advance(5000);
  assert.equal(await done, true);
  assert.deepEqual(h.poses.slice(1, 5), ['anticipate', 'feast', 'celebrate', 'rest']);
});

test('destroy settles an interrupted feed and prevents stale callbacks', async () => {
  const h = harness();
  const done = h.motion.feed(2);
  h.motion.destroy();
  const snapshot = [...h.poses];
  h.advance(60000);
  assert.equal(await done, false);
  assert.deepEqual(h.poses, snapshot);
  assert.equal(h.jobs.size, 0);
});

test('reduced motion stays still unless the user interacts', async () => {
  const h = harness(true);
  h.advance(60000);
  assert.deepEqual(h.poses, ['rest']);
  assert.equal(h.jobs.size, 0);
  h.motion.pet();
  assert.equal(h.poses.at(-1), 'purr');
  h.advance(5000);
  assert.equal(h.poses.at(-1), 'rest');
  const done = h.motion.feed(1);
  h.advance(5000);
  assert.equal(await done, true);
  assert.equal(h.jobs.size, 0);
});

test('changing motion preferences cancels the idle cycle without disturbing feeding', async () => {
  const h = harness();
  h.motion.setReduced(true);
  h.advance(60000);
  assert.equal(h.poses.at(-1), 'rest');
  const done = h.motion.feed(1);
  h.motion.setReduced(false);
  h.advance(5000);
  assert.equal(await done, true);
  assert.equal(h.poses.at(-1), 'rest');
  assert.equal(h.jobs.size, 1);
});
