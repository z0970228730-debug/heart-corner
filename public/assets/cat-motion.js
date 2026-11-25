/* Visual-only cat choreography. The app owns all tasks, fish and coins. */
(() => {
  'use strict';
  const labels = {
    rest: '暖暖午睡', curious: '好奇地看看', blink: '慢慢眨眼',
    purr: '呼嚕呼嚕', stretch: '舒服伸伸爪', anticipate: '聞到香味了',
    nibble: '小口嚼嚼', feast: '開心大餐', satisfied: '心滿意足', celebrate: '吃得好滿足'
  };
  const visuals = {
    rest: 'rest', curious: 'curious', blink: 'happy', purr: 'happy', stretch: 'happy',
    anticipate: 'curious', nibble: 'eat', feast: 'eat', satisfied: 'happy', celebrate: 'happy'
  };
  const petReactions = [
    { name: 'purr', steps: [['purr', 3000]] },
    { name: 'stretch', steps: [['stretch', 1900]] },
    { name: 'greet', steps: [['curious', 1000], ['stretch', 1600]] }
  ];

  function create({ onPose, reduced = false, random = Math.random,
    setTimer = setTimeout, clearTimer = clearTimeout } = {}) {
    let timer, alive = true, busy = false, settle, pose, petIndex = 0;
    const stop = () => { if (timer !== undefined) clearTimer(timer); timer = undefined; };
    const show = (next) => { pose = next; onPose?.(next); };
    function sequence(steps, complete) {
      stop();
      let index = 0;
      function next() {
        timer = undefined;
        if (!alive) return;
        if (index === steps.length) { complete(); return; }
        const [nextPose, delay] = steps[index++];
        show(nextPose);
        timer = setTimer(next, delay);
      }
      next();
    }
    function idle() {
      stop();
      show('rest');
      if (reduced) return;
      timer = setTimer(() => sequence([['curious', 3300], ['blink', 3000]], idle),
        11000 + Math.floor(random() * 8000));
    }
    function pet() {
      if (!alive || busy) return null;
      const reaction = petReactions[petIndex++ % petReactions.length];
      sequence(reaction.steps, idle);
      return reaction.name;
    }
    function feed(count) {
      if (!alive || busy || !(count > 0)) return Promise.resolve(false);
      busy = true;
      const steps = count === 1
        ? [['anticipate', 650], ['nibble', 950], ['satisfied', 1500]]
        : [['anticipate', 650], ['feast', 1450], ['celebrate', 1800]];
      return new Promise(resolve => {
        settle = resolve;
        sequence(steps, () => {
          busy = false;
          settle = undefined;
          idle();
          resolve(true);
        });
      });
    }
    function setReduced(value) {
      if (!alive || reduced === value) return;
      reduced = value;
      if (busy) show(pose);
      else idle();
    }
    function destroy() {
      if (!alive) return;
      alive = false;
      stop();
      settle?.(false);
      settle = undefined;
    }
    idle();
    return { pet, feed, setReduced, destroy };
  }

  function markup() {
    const layer = (pose, image, details = []) => `<span class="cat-pose cat-pose--${pose}" aria-hidden="true">
      <img src="assets/${image}" alt="" draggable="false" decoding="async">
      ${details.map(detail => `<span class="cat-detail cat-detail--${detail}" aria-hidden="true"></span>`).join('')}
    </span>`;
    return `<button type="button" class="cat-stage" id="petCat" data-pose="rest" data-visual="rest"
      aria-label="摸摸橘白小貓" aria-describedby="petProgress">
      <span class="cat-backdrop" aria-hidden="true"><img src="assets/cat-rest.webp" alt="" draggable="false"></span>
      ${layer('rest', 'cat-rest.webp', ['breath'])}
      <video class="cat-video cat-video--idle" src="assets/cat-idle.mp4" muted loop playsinline preload="metadata" aria-hidden="true"></video>
      ${layer('curious', 'cat-curious-v2.webp', ['breath', 'ear', 'ear-other', 'tail'])}
      ${layer('eat', 'cat-eating-v2.webp', ['breath', 'ear', 'tail', 'nibble'])}
      ${layer('happy', 'cat-happy-v2.webp', ['breath', 'ear', 'tail'])}
      <video class="cat-video cat-video--pet" src="assets/cat-pet.mp4" muted playsinline preload="metadata" aria-hidden="true"></video>
      <span class="cat-effects" aria-hidden="true"><i>✧</i><i>♡</i><i>✦</i></span>
    </button>`;
  }

  function mount(stage, { onPose } = {}) {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const idle = stage.querySelector('.cat-video--idle');
    const pet = stage.querySelector('.cat-video--pet');
    let current = 'rest', destroyed = false, playVersion = 0;
    function syncPlayback() {
      const version = ++playVersion;
      stage.removeAttribute('data-video');
      const target = current === 'rest' ? idle : ['blink', 'purr'].includes(current) ? pet : null;
      for (const v of [idle, pet]) if (v !== target || media.matches || document.hidden) v.pause();
      if (!target || media.matches || document.hidden || destroyed) return;
      const reveal = () => {
        if (!destroyed && version === playVersion && !media.matches && !document.hidden && !target.paused)
          stage.dataset.video = target === idle ? 'idle' : 'pet';
      };
      try {
        if (target === pet) target.currentTime = 0;
        const playing = target.play();
        if (playing) playing.then(reveal, () => {});
        else reveal();
      } catch (_) { /* Keep the watercolor fallback visible. */ }
    }
    const motion = create({
      reduced: media.matches,
      onPose(pose) {
        current = pose;
        stage.dataset.pose = pose;
        stage.dataset.visual = visuals[pose];
        onPose?.(pose, labels[pose]);
        syncPlayback();
      }
    });
    const onMedia = () => motion.setReduced(media.matches);
    const onVisibility = () => syncPlayback();
    media.addEventListener?.('change', onMedia);
    if (!media.addEventListener) media.addListener?.(onMedia);
    document.addEventListener('visibilitychange', onVisibility);
    function destroy() {
      if (destroyed) return;
      destroyed = true;
      motion.destroy();
      ++playVersion;
      idle.pause();
      pet.pause();
      media.removeEventListener?.('change', onMedia);
      if (!media.removeEventListener) media.removeListener?.(onMedia);
      document.removeEventListener('visibilitychange', onVisibility);
    }
    return { pet: motion.pet, feed: motion.feed, destroy };
  }
  globalThis.CatMotion = Object.freeze({ create, markup, mount });
})();
