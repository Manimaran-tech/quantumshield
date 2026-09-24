/* ============================================================
   QuantumShield — Scroll engine + cinematic exit transition
   Loads scenes from SCENES (scenes.js) into #deck, drives a
   fixed crossfade per scroll band, lazy-loads optional images
   from /images/, and preserves the "Enter Platform" FX → /app.html
   ============================================================ */
(function () {
  'use strict';

  var SCENES = window.SCENES || [];
  var DECK = document.getElementById('deck');
  var COUNTER_NOW = document.getElementById('counter-now');
  var COUNTER_TOTAL = document.getElementById('counter-total');
  var PROGRESS = document.getElementById('progress-bar');
  var SCROLLER = document.getElementById('scroller');
  var HINT = document.getElementById('scroll-hint');

  var N = SCENES.length;
  if (!N) { return; }
  COUNTER_TOTAL.textContent = String(N).padStart(2, '0');

  // Per-scene entrance "flow" variant — text flows / moves in from a
  // direction (see .fx-* keyframes in index.html). Cycled for variety so the
  // A–Z tell isn't a static left-then-right flip: hero rises, headings wipe
  // left→right / right→left, body flows, theory charts mask down, etc.
  var FX = [
    'fx-rise', 'fx-lr', 'fx-rl', 'fx-rise', 'fx-mask',
    'fx-lr', 'fx-scale', 'fx-rl', 'fx-rise', 'fx-lr',
    'fx-rl', 'fx-rise', 'fx-scale', 'fx-lr', 'fx-rl',
    'fx-rise', 'fx-mask', 'fx-rise', 'fx-rise', 'fx-rise'
  ];

  // viewport height per scene (in px). total scroll = N * VPH
  var VPH = Math.max(window.innerHeight, 640);

  function totalScrollPx() { return N * VPH; }

  // ---------- CSS per-scene needs (loaded images optional) ----------
  // seg = scrollProgress * (N-1)  → ranges 0 .. N-1
  // Scene i is centered at integer i. Around each center there is a 0.44-unit
  // HOLD (opacity 1) [-0.22, +0.22], a 0.20-unit fade-out [+0.22, +0.42],
  // a clean 0.16-unit delay dead-band [+0.42, +0.58] where both adjacent scenes
  // are at 0 (preventing any text or art overlap), and a smooth 0.20-unit
  // fade-in [-0.42, -0.22] for the next scene.
  function smoothstep(a, b, x) {
    if (x <= a) return 0; if (x >= b) return 1;
    var t = (x - a) / (b - a);
    return t * t * (3 - 2 * t);
  }
  function sceneOpacity(i, seg) {
    if (i === 0 && seg <= 0.22) {
      return 1;
    }
    if (i === N - 1 && seg >= (N - 1) - 0.22) {
      return 1;
    }
    var d = seg - i;
    if (Math.abs(d) <= 0.22) {
      return 1;
    }
    if (d < 0) {
      // Approaching scene i from previous scroll
      if (d <= -0.42) return 0;
      return smoothstep(-0.42, -0.22, d);
    } else {
      // Leaving scene i toward next scene
      if (d >= 0.42) return 0;
      return 1 - smoothstep(0.22, 0.42, d);
    }
  }

  // ---------- Render scenes ----------
  function renderScene(s, i) {
    var el = document.createElement('section');
    el.className = 'scene' + (FX[i] ? ' ' + FX[i] : '');
    el.id = 'scene-' + s.id;
    el.dataset.index = i;

    var inner = document.createElement('div');
    inner.className = 'scene-inner' + (s.dual === 'left' ? ' dual-left' : '') + (s.stacked ? ' stacked' : '');

    if (s.id === 'hero') {
      var blurBand = document.createElement('div');
      blurBand.className = 'scene-blur-band';
      inner.appendChild(blurBand);

      // Left-Most Flank: Early Detection (Small text)
      var flankLeft = document.createElement('aside');
      flankLeft.className = 'hero-flank hero-flank-left';
      flankLeft.innerHTML =
        '<div class="hero-flank-card">' +
          '<div class="hero-flank-badge"><span class="hero-flank-dot"></span>STAGE 0 DETECTION</div>' +
          '<h3 class="hero-flank-title">Early Disease Detection</h3>' +
          '<ul class="hero-flank-list">' +
            '<li><span class="hero-flank-dot"></span><span><strong>Chest X-Ray</strong> · 98.8% sensitivity</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>Retinal OCT</strong> · Sub-micron mapping</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>Dermatoscopy</strong> · ABCD melanoma</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>Biopsy</strong> · Adenocarcinoma margin</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>Quantum Vision</strong> · VQC anomaly gate</span></li>' +
          '</ul>' +
        '</div>';
      inner.appendChild(flankLeft);

      // Center Column: Older style & color (h2 QUANTUMSHIELD, lede, scrollHint)
      var textCol = document.createElement('div');
      textCol.className = 'col-text';
      textCol.appendChild(buildEyebrow(s));
      var h2 = document.createElement('h2');
      h2.innerHTML = s.title;
      textCol.appendChild(h2);
      if (s.lede) {
        var lede = document.createElement('p');
        lede.className = 'lede';
        lede.innerHTML = s.lede;
        textCol.appendChild(lede);
      }
      if (s.scrollHint) {
        var hint = document.createElement('div');
        hint.className = 'hero-scroll-hint js-hero-scroll';
        hint.innerHTML = '<span>' + s.scrollHint + '</span>';
        hint.style.cursor = 'pointer';
        hint.addEventListener('click', function () { scrollToScene(1); });
        textCol.appendChild(hint);
      }
      inner.appendChild(textCol);

      // Right-Most Flank: Discovery (Small text)
      var flankRight = document.createElement('aside');
      flankRight.className = 'hero-flank hero-flank-right';
      flankRight.innerHTML =
        '<div class="hero-flank-card">' +
          '<div class="hero-flank-badge"><span class="hero-flank-dot"></span>6-LAYER QM/MM</div>' +
          '<h3 class="hero-flank-title">Quantum Bio-Simulation</h3>' +
          '<ul class="hero-flank-list">' +
            '<li><span class="hero-flank-dot"></span><span><strong>AlphaFold PDB</strong> · 10 pocket residues</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>SMILES LSTM</strong> · QRL policy sampling</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>MMFF94 3D</strong> · Conformer pocket relax</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>Qiskit VQE</strong> · Exact ground state (ΔG, Kd)</span></li>' +
            '<li><span class="hero-flank-dot"></span><span><strong>ADMET & DNA</strong> · Fsp³ saturation safety</span></li>' +
          '</ul>' +
        '</div>';
      inner.appendChild(flankRight);

      el.appendChild(inner);
      return el;
    }

    var textCol = document.createElement('div');
    textCol.className = 'col-text';
    textCol.appendChild(buildEyebrow(s));
    var h2 = document.createElement('h2');
    h2.innerHTML = s.title;
    textCol.appendChild(h2);
    if (s.lede) {
      var lede = document.createElement('p');
      lede.className = 'lede';
      lede.innerHTML = s.lede;
      textCol.appendChild(lede);
    }
    if (s.formula) {
      var fm = document.createElement('div');
      fm.className = 'formula';
      fm.innerHTML = '<span class="cap">' + s.formula.cap + '</span>' + s.formula.body;
      textCol.appendChild(fm);
    }
    if (s.code) {
      var pre = document.createElement('pre');
      pre.className = 'formula';
      pre.style.whiteSpace = 'pre-wrap';
      pre.style.fontFamily = 'var(--mono)';
      pre.textContent = s.code;
      textCol.appendChild(pre);
    }
    if (s.facts && s.facts.length) {
      var ul = document.createElement('ul');
      ul.className = 'fact-list';
      s.facts.forEach(function (f) {
        var li = document.createElement('li');
        li.className = 'fact';
        li.innerHTML = '<span class="k">' + f[0] + '</span><span class="v">' + f[1] + '</span>';
        ul.appendChild(li);
      });
      textCol.appendChild(ul);
    }
    if (s.scrollHint) {
      var hint = document.createElement('div');
      hint.className = 'hero-scroll-hint';
      hint.innerHTML = '<span>' + s.scrollHint + '</span>';
      hint.style.cursor = 'pointer';
      hint.addEventListener('click', function () { scrollToScene(1); });
      textCol.appendChild(hint);
    }
    if (s.layers && s.layers.length) {
      var chart = document.createElement('div');
      chart.className = 'layer-chart';
      s.layers.forEach(function (lr) {
        var row = document.createElement('div');
        row.className = 'layer-row';
        row.innerHTML = '<span class="ln">' + lr[0] + '</span>' +
          '<span><span class="lt">' + lr[1] + '</span><span class="ld">' + (lr[3] || '') + '</span></span>' +
          '<span class="ls">' + (lr[2] || '') + '</span>';
        chart.appendChild(row);
      });
      textCol.appendChild(chart);
    }
    if (s.mods && s.mods.length) {
      var container = document.createElement('div');
      container.className = 'mods-ticker-container';

      var lane1 = document.createElement('div');
      lane1.className = 'mods-ticker-lane is-rtl';

      var lane2 = document.createElement('div');
      lane2.className = 'mods-ticker-lane is-ltr';

      function createCard(m) {
        var card = document.createElement('div');
        card.className = 'mod-card';
        card.dataset.mod = m.tag.toLowerCase();

        var frame = document.createElement('div');
        frame.className = 'mod-frame';

        var art = document.createElement('div');
        art.className = 'mod-art';
        var innerSvg = '';
        if (typeof m.m === 'function') {
          innerSvg = m.m();
        } else if (typeof m.m === 'string') {
          innerSvg = m.m;
        }
        if (innerSvg && !innerSvg.trim().startsWith('<svg')) {
          innerSvg = '<svg viewBox="0 0 100 100" fill="none" stroke-linecap="round" stroke-linejoin="round">' + innerSvg + '</svg>';
        }
        art.innerHTML = innerSvg;

        if (m.img) {
          var img = document.createElement('img');
          img.className = 'mod-img';
          img.loading = 'eager';
          img.decoding = 'async';
          img.alt = m.t;
          img.addEventListener('error', function () { img.remove(); });
          img.addEventListener('load', function () {
            img.classList.add('on');
            frame.classList.add('has-img');
          });
          img.src = '/images/' + m.img;
          art.appendChild(img);
        }

        frame.appendChild(art);

        var info = document.createElement('div');
        info.className = 'mod-info';
        info.innerHTML = '<span class="mod-tag">' + m.tag + '</span>' +
                         '<span class="mod-label">' + m.t + '</span>' +
                         '<span class="mod-sub">' + m.d + '</span>';

        card.appendChild(frame);
        card.appendChild(info);

        var extender = document.createElement('div');
        extender.className = 'mod-extender';
        card.appendChild(extender);

        return card;
      }

      // Group modules dynamically: first half for Lane 1 (RTL), second half for Lane 2 (LTR)
      var half = Math.ceil(s.mods.length / 2);
      var group1 = s.mods.slice(0, half);
      var group2 = s.mods.slice(half);

      // Populate Lane 1 (RTL) - 10 times to prevent loop interval breaks on wide screens
      for (var r1 = 0; r1 < 10; r1++) {
        group1.forEach(function (m) {
          lane1.appendChild(createCard(m));
        });
      }

      // Populate Lane 2 (LTR) - 10 times to prevent loop interval breaks on wide screens
      for (var r2 = 0; r2 < 10; r2++) {
        group2.forEach(function (m) {
          lane2.appendChild(createCard(m));
        });
      }

      container.appendChild(lane1);
      container.appendChild(lane2);
      textCol.appendChild(container);
    }
    if (s.cta) {
      var ct = document.createElement('div');
      ct.className = 'cta-card';
      ct.innerHTML =
        '<div class="stat-row">' +
          '<div class="stat"><div class="num">6</div><div class="lab">Pipeline Layers</div></div>' +
          '<div class="stat"><div class="num">10⁶⁰</div><div class="lab">Chemical Space</div></div>' +
          '<div class="stat"><div class="num">12–24h</div><div class="lab">vs 5–7 yrs</div></div>' +
          '<div class="stat"><div class="num">2-way</div><div class="lab">CPU & IBM QPU</div></div>' +
        '</div>' +
        '<button class="btn-enter js-enter" type="button" style="margin-top:34px;">Enter Platform →</button>';
      textCol.appendChild(ct);
    }

    // art column
    var artCol = document.createElement('div');
    artCol.className = 'col-art';
    var frame = document.createElement('div');
    frame.className = 'art-frame';
    if (typeof s.art === 'function' && !s.img) {
      frame.innerHTML = s.art();
    }
    // blueprint viewfinder corners — drawn in on art-column hover
    frame.insertAdjacentHTML('beforeend',
      '<span class="crosshair ch-tl"></span><span class="crosshair ch-tr"></span>' +
      '<span class="crosshair ch-bl"></span><span class="crosshair ch-br"></span>');
    // optional lazy raster image (premium renders path: /images/<file>)
    if (s.img) {
      var img = document.createElement('img');
      img.className = 'opt-img';
      img.loading = 'eager';
      img.decoding = 'async';
      img.alt = s.id;
      img.addEventListener('error', function () { img.remove(); }); // keep SVG art
      img.addEventListener('load', function () {
        img.classList.add('on');
        frame.classList.add('has-img');
      });
      img.src = '/images/' + s.img;
      if (img.complete) {
        img.classList.add('on');
        frame.classList.add('has-img');
      }
      frame.appendChild(img);
      var cap = document.createElement('span');
      cap.className = 'art-caption';
      cap.textContent = 'FIG · ' + s.id;
      frame.appendChild(cap);
    }
    artCol.appendChild(frame);

    // layout order
    if (s.stacked && s.id !== 'cta') {
      // tall technical charts — text+chart only, centered, no art to avoid overflow
      inner.appendChild(textCol);
    } else if (s.cta) {
      inner.appendChild(textCol);
    } else if (s.dual === 'left') {
      inner.appendChild(artCol);
      inner.appendChild(textCol);
    } else {
      inner.appendChild(textCol);
      inner.appendChild(artCol);
    }

    el.appendChild(inner);
    return el;
  }

  function buildEyebrow(s) {
    var d = document.createElement('div');
    d.className = 'eyebrow';
    var parts = [];
    if (s.num !== undefined) parts.push('<span class="n">' + s.num + '</span>');
    (s.eyebrow || []).forEach(function (t) { if (t) parts.push('<span>' + t + '</span>'); });
    d.innerHTML = parts.join('<span class="bar"></span>');
    return d;
  }

  // Initialize Lenis early if available
  if (!window.lenis && typeof Lenis !== 'undefined') {
    var lenis = new Lenis({
      lerp: 0.1,
      smoothWheel: true,
      syncTouch: false
    });
    window.lenis = lenis;
    function lenisRaf(time) {
      lenis.raf(time);
      requestAnimationFrame(lenisRaf);
    }
    requestAnimationFrame(lenisRaf);
  }

  SCENES.forEach(function (s, i) { DECK.appendChild(renderScene(s, i)); });
  var sceneEls = Array.prototype.slice.call(DECK.querySelectorAll('.scene'));

  // Cache sub-elements per scene for 120fps hardware-accelerated parallax updates
  var sceneCache = sceneEls.map(function (el) {
    return {
      el: el,
      heroFlankLeft: el.querySelector('.hero-flank-left'),
      heroFlankRight: el.querySelector('.hero-flank-right'),
      textCol: el.querySelector('.col-text'),
      artCol: el.querySelector('.col-art'),
      artFrame: el.querySelector('.art-frame'),
      optImg: el.querySelector('.opt-img'),
      svgArt: el.querySelector('.art-frame > svg'),
      formula: el.querySelector('.formula'),
      layerRows: Array.prototype.slice.call(el.querySelectorAll('.layer-row')),
      caption: el.querySelector('.art-caption')
    };
  });

  // ---------- Top Navigator Pill Bar ----------
  var SECTIONS = [
    { name: 'Vision', start: 0, end: 0, tag: 'vision' },
    { name: 'Overview', start: 1, end: 2, tag: 'who' },
    { name: 'Early Detection', start: 3, end: 7, tag: 'detection' },
    { name: 'Unified Loop', start: 8, end: 8, tag: 'bridge' },
    { name: 'Simulation', start: 9, end: 15, tag: 'simulation' },
    { name: 'Engines', start: 16, end: 16, tag: 'engines' },
    { name: 'Quantum Core', start: 17, end: 18, tag: 'quantum' },
    { name: 'Platform', start: 19, end: 19, tag: 'platform' }
  ];
  var PILL_BAR = document.getElementById('nav-pill-bar');
  var pillItems = [];

  if (PILL_BAR) {
    SECTIONS.forEach(function (s) {
      var item = document.createElement('a');
      item.className = 'nav-pill-item';
      item.href = '#';
      item.textContent = s.name;
      item.dataset.sec = s.tag;
      item.addEventListener('click', function (e) {
        e.preventDefault();
        scrollToScene(s.start);
      });
      PILL_BAR.appendChild(item);
      pillItems.push(item);
    });
  }

  // ---------- Interactive 3D Cursor Tilt & Specular Sheen ----------
  var currentTiltX = 0, currentTiltY = 0;
  var targetTiltX = 0, targetTiltY = 0;
  var isMouseOverArt = false;

  window.addEventListener('mousemove', function (e) {
    var c = sceneCache[currentScene];
    if (!c) return;

    if (currentScene === 0) {
      targetTiltX = (e.clientX / window.innerWidth - 0.5) * 2;
      targetTiltY = (e.clientY / window.innerHeight - 0.5) * 2;
      return;
    }

    if (!c.artFrame) return;

    var rect = c.artFrame.getBoundingClientRect();
    var inX = e.clientX - rect.left;
    var inY = e.clientY - rect.top;

    if (inX >= -50 && inX <= rect.width + 50 && inY >= -50 && inY <= rect.height + 50) {
      isMouseOverArt = true;
      targetTiltX = ((inX / rect.width) - 0.5) * 2; // -1 to +1
      targetTiltY = ((inY / rect.height) - 0.5) * 2; // -1 to +1

      // Track dynamic specular highlight coordinates across glossy card surface
      var gx = Math.max(0, Math.min(100, (inX / rect.width) * 100));
      var gy = Math.max(0, Math.min(100, (inY / rect.height) * 100));
      c.artFrame.style.setProperty('--glare-x', gx.toFixed(1) + '%');
      c.artFrame.style.setProperty('--glare-y', gy.toFixed(1) + '%');
    } else {
      isMouseOverArt = false;
      targetTiltX = 0;
      targetTiltY = 0;
    }
  }, { passive: true });

  document.addEventListener('mouseleave', function () {
    isMouseOverArt = false;
    targetTiltX = 0;
    targetTiltY = 0;
  });

  // Tilt spring physics tick
  function tiltRaf() {
    if (isMouseOverArt || Math.abs(currentTiltX - targetTiltX) > 0.002 || Math.abs(currentTiltY - targetTiltY) > 0.002) {
      currentTiltX += (targetTiltX - currentTiltX) * 0.09;
      currentTiltY += (targetTiltY - currentTiltY) * 0.09;
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }
    requestAnimationFrame(tiltRaf);
  }
  requestAnimationFrame(tiltRaf);

  // ---------- Exact Magnetic Scene Snapping Controller ----------
  var lastScrollY = window.scrollY || 0;
  var lastScrollDelta = 0;
  var lastScrollTime = performance.now();
  var snapTimer = null;
  var isSnappingProgrammatically = false;

  function scrollToScene(i, customDuration) {
    i = Math.max(0, Math.min(N - 1, i));
    var p = i / (N - 1);
    var max = totalScrollPx() - window.innerHeight;
    var targetScroll = Math.round(p * max);

    isSnappingProgrammatically = true;
    clearTimeout(snapTimer);

    if (window.lenis) {
      window.lenis.scrollTo(targetScroll, {
        duration: customDuration || 0.65,
        easing: function (t) {
          return 1 - Math.pow(1 - t, 3); // Buttery cubic-out ease
        },
        onComplete: function () {
          setTimeout(function () {
            isSnappingProgrammatically = false;
          }, 60);
        }
      });
    } else {
      window.scrollTo({ top: targetScroll, behavior: 'smooth' });
      setTimeout(function () {
        isSnappingProgrammatically = false;
      }, 650);
    }
  }

  function scheduleMagneticSnap() {
    if (isSnappingProgrammatically) return;

    var y = window.scrollY || document.documentElement.scrollTop;
    var maxScroll = Math.max(1, totalScrollPx() - window.innerHeight);
    var p = Math.min(1, Math.max(0, y / maxScroll));
    var seg = p * (N - 1);

    var base = Math.floor(seg);
    var frac = seg - base;
    var targetScene = Math.round(seg);

    // Momentum-aware snap settling:
    // If user scrolled downward with momentum and passed 0.14 into next scene, snap forward.
    // If user scrolled upward with momentum and passed 0.14 into previous scene, snap backward.
    if (lastScrollDelta > 3 && frac > 0.14) {
      targetScene = Math.min(N - 1, base + 1);
    } else if (lastScrollDelta < -3 && frac < 0.86) {
      targetScene = Math.max(0, base);
    }

    var targetP = targetScene / (N - 1);
    var targetY = Math.round(targetP * maxScroll);

    if (Math.abs(y - targetY) > 2) {
      scrollToScene(targetScene);
    }
  }

  // ---------- Scroll handler & Multi-Plane Parallax (rAF-throttled) ----------
  var ticking = false;
  var currentScene = 0;

  function update() {
    ticking = false;
    var y = window.scrollY || document.documentElement.scrollTop;
    var maxScroll = Math.max(1, totalScrollPx() - window.innerHeight);
    var p = Math.min(1, Math.max(0, y / maxScroll));
    var seg = p * (N - 1); // 0 .. N-1 so last scene reaches center at the end

    PROGRESS.style.width = (p * 100) + '%';

    // Fade and parallax each scene; track whose band we're "in"
    var maxOp = 0;
    var closestScene = Math.min(N - 1, Math.max(0, Math.round(seg)));
    var winner = closestScene;

    for (var i = 0; i < N; i++) {
      var op = sceneOpacity(i, seg);
      var c = sceneCache[i];
      c.el.style.opacity = op.toFixed(3);

      if (op > 0.005) {
        c.el.style.visibility = 'visible';
        var d = seg - i;

        // 0. Hero Left-Most & Right-Most Flanks Differential Parallax
        if (i === 0) {
          if (c.textCol) {
            c.textCol.style.transform = 'translate3d(0, ' + (-d * 24).toFixed(1) + 'px, 0)';
          }
          if (c.heroFlankLeft) {
            c.heroFlankLeft.style.transform = 'translate3d(' + (currentTiltX * -8).toFixed(1) + 'px, calc(-50% + ' + (-d * 18 + currentTiltY * 6).toFixed(1) + 'px), 12px)';
          }
          if (c.heroFlankRight) {
            c.heroFlankRight.style.transform = 'translate3d(' + (currentTiltX * 8).toFixed(1) + 'px, calc(-50% + ' + (-d * 20 + currentTiltY * 6).toFixed(1) + 'px), 12px)';
          }
        }

        // 1. Scene container base drift
        c.el.style.transform = 'translate3d(0, ' + (-d * 18).toFixed(1) + 'px, 0)';

        // 2. Text column differential parallax
        if (c.textCol) {
          c.textCol.style.transform = 'translate3d(0, ' + (-d * 24).toFixed(1) + 'px, 0)';
        }

        // 3. Formula / code block floating depth
        if (c.formula) {
          c.formula.style.transform = 'translate3d(0, ' + (-d * 34).toFixed(1) + 'px, 8px)';
        }

        // 4. Staggered layer chart accordion parallax
        if (c.layerRows && c.layerRows.length) {
          for (var r = 0; r < c.layerRows.length; r++) {
            var rowOffset = -d * (14 + r * 5);
            c.layerRows[r].style.transform = 'translate3d(0, ' + rowOffset.toFixed(1) + 'px, 0)';
          }
        }

        // 5. Art column differential parallax
        if (c.artCol) {
          c.artCol.style.transform = 'translate3d(0, ' + (-d * 52).toFixed(1) + 'px, 0)';
        }

        // 6. Art frame and inner image / SVG parallax
        var frameScrollZ = Math.max(0, (1 - Math.abs(d) * 2.2) * 26);
        var frameRotY = -d * 7;
        var imgScrollY = d * 32;
        var imgScale = Math.max(0.96, 1.05 - Math.abs(d) * 0.08);

        if (i === currentScene && isMouseOverArt) {
          // Combined 3D cursor tilt + scroll depth
          if (c.artFrame) {
            c.artFrame.style.transform = 'perspective(1100px) rotateX(' + (-currentTiltY * 7).toFixed(2) + 'deg) rotateY(' + (frameRotY + currentTiltX * 8).toFixed(2) + 'deg) translateZ(' + frameScrollZ.toFixed(1) + 'px)';
          }
          if (c.optImg) {
            c.optImg.style.transform = 'translate3d(' + (currentTiltX * 14).toFixed(1) + 'px, ' + (imgScrollY + currentTiltY * 14).toFixed(1) + 'px, 24px) scale(' + imgScale.toFixed(3) + ')';
          }
          if (c.svgArt) {
            c.svgArt.style.transform = 'translate3d(' + (currentTiltX * 10).toFixed(1) + 'px, ' + (imgScrollY + currentTiltY * 10).toFixed(1) + 'px, 14px)';
          }
        } else {
          // Pure scroll-driven parallax
          if (c.artFrame) {
            c.artFrame.style.transform = 'perspective(1100px) rotateY(' + frameRotY.toFixed(2) + 'deg) translateZ(' + frameScrollZ.toFixed(1) + 'px)';
          }
          if (c.optImg) {
            c.optImg.style.transform = 'translate3d(0, ' + imgScrollY.toFixed(1) + 'px, 18px) scale(' + imgScale.toFixed(3) + ')';
          }
          if (c.svgArt) {
            c.svgArt.style.transform = 'translate3d(0, ' + imgScrollY.toFixed(1) + 'px, 10px)';
          }
        }
      } else {
        c.el.style.visibility = 'hidden';
        c.el.style.transform = 'translate3d(0, 24px, 0)';
      }

      if (op > maxOp) {
        maxOp = op;
        winner = i;
      }
    }

    // Toggle active classes based on winner to prevent pointer-events dead zones
    for (var j = 0; j < N; j++) {
      var isAct = (j === winner && maxOp > 0.05);
      sceneEls[j].classList.toggle('is-active', isAct);
      sceneEls[j].style.pointerEvents = isAct ? 'auto' : 'none';
    }

    if (winner !== currentScene) {
      currentScene = winner;
      COUNTER_NOW.textContent = (winner < 10 ? '0' : '') + String(winner + 1);

      // Update active nav pill based on winner index
      var activeTag = '';
      for (var k = 0; k < SECTIONS.length; k++) {
        var sec = SECTIONS[k];
        if (winner >= sec.start && winner <= sec.end) {
          activeTag = sec.tag;
          break;
        }
      }
      pillItems.forEach(function (item) {
        if (item.dataset.sec === activeTag) {
          item.classList.add('active');
        } else {
          item.classList.remove('active');
        }
      });
    }

    // Background parallax
    var dnaEl = document.getElementById('dna-viewport') || document.getElementById('css-dna');
    if (dnaEl) {
      dnaEl.style.transform = 'translate3d(0, ' + (p * -50).toFixed(1) + 'px, 0)';
    }
    var watermarksEl = document.getElementById('watermark-field');
    if (watermarksEl) {
      watermarksEl.style.transform = 'translate3d(0, ' + (p * -30).toFixed(1) + 'px, 0)';
    }

    // Hint fades after first scroll
    HINT.style.opacity = (p < 0.02) ? '0.9' : '0';
  }

  function onScroll() {
    var now = performance.now();
    var y = window.scrollY || document.documentElement.scrollTop;
    lastScrollDelta = y - lastScrollY;
    lastScrollY = y;
    lastScrollTime = now;

    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }

    // Debounce magnetic snap: settles exactly at nearest scene when scrolling stops
    if (!isSnappingProgrammatically) {
      clearTimeout(snapTimer);
      snapTimer = setTimeout(scheduleMagneticSnap, 130);
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () {
    VPH = Math.max(window.innerHeight, 640);
    setScrollerHeight();
    update();
  });

  // User gesture interruption — allows instant takeover of scroll
  window.addEventListener('wheel', function () {
    if (isSnappingProgrammatically) {
      isSnappingProgrammatically = false;
    }
    clearTimeout(snapTimer);
    snapTimer = setTimeout(scheduleMagneticSnap, 130);
  }, { passive: true });

  var touchStartY = 0;
  var touchStartTime = 0;
  window.addEventListener('touchstart', function (e) {
    if (isSnappingProgrammatically) {
      isSnappingProgrammatically = false;
    }
    clearTimeout(snapTimer);
    touchStartY = e.touches[0].clientY;
    touchStartTime = performance.now();
  }, { passive: true });

  window.addEventListener('touchend', function (e) {
    var touchEndY = e.changedTouches[0].clientY;
    var dy = touchStartY - touchEndY; // positive = swipe up (scroll down)
    var dt = Math.max(1, performance.now() - touchStartTime);

    if (Math.abs(dy) > 40 && dt < 450) {
      if (dy > 0) {
        scrollToScene(Math.min(N - 1, currentScene + 1));
      } else {
        scrollToScene(Math.max(0, currentScene - 1));
      }
    } else {
      clearTimeout(snapTimer);
      snapTimer = setTimeout(scheduleMagneticSnap, 110);
    }
  }, { passive: true });

  // Keyboard navigation for scene snapping
  window.addEventListener('keydown', function (e) {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable)) {
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'PageDown' || (e.key === ' ' && !e.shiftKey)) {
      e.preventDefault();
      scrollToScene(Math.min(N - 1, currentScene + 1));
    } else if (e.key === 'ArrowUp' || e.key === 'PageUp' || (e.key === ' ' && e.shiftKey)) {
      e.preventDefault();
      scrollToScene(Math.max(0, currentScene - 1));
    } else if (e.key === 'Home') {
      e.preventDefault();
      scrollToScene(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      scrollToScene(N - 1);
    }
  });

  // Interactive controls
  if (HINT) {
    HINT.style.cursor = 'pointer';
    HINT.addEventListener('click', function () {
      scrollToScene(1);
    });
  }

  var counterEl = document.getElementById('counter');
  if (counterEl) {
    counterEl.style.cursor = 'pointer';
    counterEl.title = 'Click to advance scene';
    counterEl.addEventListener('click', function () {
      scrollToScene(Math.min(N - 1, currentScene + 1));
    });
  }

  // set scroller height to create the scrollable region
  function setScrollerHeight() {
    SCROLLER.style.height = totalScrollPx() + 'px';
  }
  setScrollerHeight();
  window.addEventListener('resize', setScrollerHeight);

  update();

  // graceful whole-deck entrance (covers the first paint + Spline load state)
  requestAnimationFrame(function () { DECK.classList.add('loaded'); });

  // ============================================================
  // Spline DNA cross-fade (placeholder -> live 3D)
  // ============================================================
  (function dnaLoad() {
    var sv = document.querySelector('spline-viewer');
    var ph = document.getElementById('dna-placeholder');
    var cssDna = document.getElementById('css-dna');

    // Check if WebGL is supported by the browser
    function hasWebGL() {
      try {
        var canvas = document.createElement('canvas');
        return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
      } catch (e) {
        return false;
      }
    }

    if (cssDna) {
      var pairs = 22;
      for (var i = 0; i < pairs; i++) {
        var p = document.createElement('div');
        p.className = 'base-pair';
        p.style.top = (i / pairs * 100) + '%';
        p.style.animationDelay = ((i / pairs) * -2.8) + 's';
        p.innerHTML = '<div class="node node-left"></div><div class="bridge"></div><div class="node node-right"></div>';
        cssDna.appendChild(p);
      }
    }

    if (!hasWebGL()) {
      if (sv) {
        sv.style.display = 'none';
        if (sv.parentNode) sv.parentNode.removeChild(sv);
      }
      // Leave the CSS DNA placeholder visible and spinning
      return;
    }

    function reveal() {
      sv.style.opacity = '1';
      if (ph) { ph.style.opacity = '0'; setTimeout(function () { if (ph && ph.parentNode) ph.parentNode.removeChild(ph); }, 800); }
    }
    if (sv && sv.shadowRoot && (sv.shadowRoot.querySelector('canvas') || sv.loaded)) { reveal(); }
    else if (sv) { sv.addEventListener('load', reveal); setTimeout(reveal, 3000); }
    else { setTimeout(reveal, 400); }
  })();

  // ============================================================
  // CTA — wire the "Enter Platform" button + hero scene's CTA
  // ============================================================
  function bindTransition(btn) {
    if (!btn) return;
    if (btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      btn.disabled = true;
      runCinematicExit();
    });
  }
  // bind every Enter trigger (top nav + CTA scene button)
  document.querySelectorAll('.js-enter').forEach(bindTransition);

  // ============================================================
  // Cinematic exit transition → /app.html (preserved)
  // ============================================================
  function runCinematicExit() {
    var overlay = document.getElementById('transition-overlay');
    var particleField = document.getElementById('particle-field');
    var pbText = document.getElementById('progress-bar-text');
    var pbFill = document.getElementById('progress-bar-fill');
    var tCoords = document.getElementById('target-coords');
    var particleAnimId = null;
    var imploding = false;

    document.body.classList.add('transitioning-out');
    setTimeout(function () {
      overlay.classList.add('active');
      initParticles(); initWatermarks(); startScan(); rafProgress();
    }, 150);

    // jitter coords
    setTimeout(function () {
      var ci = setInterval(function () {
        var txt = pbText ? pbText.textContent : '';
        if (txt.indexOf('IDENTIFYING') === -1 && txt.indexOf('SCANNING') === -1) { clearInterval(ci); return; }
        var rx = (10 + Math.random() * 10).toFixed(2);
        var ry = (-5 - Math.random() * 5).toFixed(2);
        var rz = (30 + Math.random() * 20).toFixed(2);
        if (tCoords) { tCoords.textContent = 'COORD: [X: +' + rx + ', Y: ' + ry + ', Z: +' + rz + ']'; }
      }, 80);
    }, 200);

    setTimeout(function () {
      if (pbText) pbText.style.color = '#0f766e';
      document.querySelectorAll('.target-bracket').forEach(function (el) {
        el.style.borderColor = '#0f766e';
        el.style.boxShadow = '0 0 10px rgba(15,118,110,.6)';
      });
      var v = document.getElementById('hud-virus-image');
      if (v) { v.style.filter = 'drop-shadow(0 0 25px rgba(15,118,110,.5))'; v.style.transform = 'scale(1.08)'; }
      stopScan(); playChime(); triggerImplode(); fadeOutWatermarks();
    }, 2500);

    setTimeout(function () { overlay.classList.add('flash'); }, 2650);
    setTimeout(function () {
      if (particleAnimId) cancelAnimationFrame(particleAnimId);
      document.body.style.background = '#f4f4f6';
      document.body.innerHTML = '<div style="position:fixed;inset:0;background:#f4f4f6;z-index:999999;"></div>';
      requestAnimationFrame(function () { window.location.href = '/app.html'; });
    }, 3000);

    // ---- audio ----
    var audioCtx = null, scanOsc = null, scanGain = null, lfoOsc = null;
    function initAudio() { if (audioCtx) return; try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} }
    function startScan() {
      try {
        initAudio(); if (!audioCtx) return;
        if (audioCtx.state === 'suspended') audioCtx.resume();
        scanOsc = audioCtx.createOscillator(); scanGain = audioCtx.createGain();
        scanOsc.type = 'triangle'; scanOsc.frequency.setValueAtTime(180, audioCtx.currentTime);
        lfoOsc = audioCtx.createOscillator(); var lg = audioCtx.createGain();
        lfoOsc.type = 'sine'; lfoOsc.frequency.value = 6; lg.gain.value = 40;
        lfoOsc.connect(lg); lg.connect(scanOsc.frequency);
        scanGain.gain.setValueAtTime(0.01, audioCtx.currentTime);
        scanGain.gain.linearRampToValueAtTime(0.08, audioCtx.currentTime + 0.15);
        scanOsc.connect(scanGain); scanGain.connect(audioCtx.destination);
        scanOsc.start(); lfoOsc.start();
        var t = audioCtx.currentTime;
        scanOsc.frequency.linearRampToValueAtTime(320, t + 0.9);
        scanOsc.frequency.linearRampToValueAtTime(180, t + 1.8);
        scanOsc.frequency.linearRampToValueAtTime(320, t + 2.7);
      } catch (e) {}
    }
    function stopScan() {
      try {
        if (scanOsc && audioCtx) {
          scanGain.gain.cancelScheduledValues(audioCtx.currentTime);
          scanGain.gain.setValueAtTime(scanGain.gain.value, audioCtx.currentTime);
          scanGain.gain.linearRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
          setTimeout(function () { try { scanOsc.stop(); if (lfoOsc) lfoOsc.stop(); } catch (e) {} }, 200);
        }
      } catch (e) {}
    }
    function playChime() {
      try {
        initAudio(); if (!audioCtx) return;
        var notes = [523.25, 783.99, 1046.50], t = audioCtx.currentTime;
        notes.forEach(function (f, i) {
          var o = audioCtx.createOscillator(), g = audioCtx.createGain();
          o.type = 'sine'; o.frequency.setValueAtTime(f, t + i * 0.08);
          g.gain.setValueAtTime(0.001, t + i * 0.08);
          g.gain.linearRampToValueAtTime(0.12, t + i * 0.08 + 0.02);
          g.gain.exponentialRampToValueAtTime(0.001, t + i * 0.08 + 0.6);
          o.connect(g); g.connect(audioCtx.destination);
          o.start(t + i * 0.08); o.stop(t + i * 0.08 + 0.75);
        });
      } catch (e) {}
    }
    // ---- particles ----
    var particles = [];
    function initParticles() {
      particleField.innerHTML = ''; particles = [];
      for (var i = 0; i < 45; i++) {
        var el = document.createElement('div');
        el.className = 'particle';
        var x = Math.random() * window.innerWidth, y = Math.random() * window.innerHeight;
        var size = 1.5 + Math.random() * 3.5, ang = Math.random() * Math.PI * 2, sp = 0.3 + Math.random() * 0.7;
        el.style.width = size + 'px'; el.style.height = size + 'px';
        el.style.opacity = (0.2 + Math.random() * 0.6).toString();
        el.style.boxShadow = '0 0 6px rgba(19,138,165,' + (0.4 + Math.random() * 0.4) + ')';
        particleField.appendChild(el);
        particles.push({ el: el, x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp,
          base: parseFloat(el.style.opacity), ps: 0.02 + Math.random() * 0.03, ph: Math.random() * 10 });
      }
      tick();
    }
    function tick() {
      var cx = window.innerWidth / 2, cy = window.innerHeight / 2;
      particles.forEach(function (p) {
        if (imploding) {
          p.x += (cx - p.x) * 0.16; p.y += (cy - p.y) * 0.16;
          p.el.style.opacity = (parseFloat(p.el.style.opacity) * 0.85).toString();
        } else {
          p.x += p.vx; p.y += p.vy;
          if (p.x < 0 || p.x > window.innerWidth) p.vx *= -1;
          if (p.y < 0 || p.y > window.innerHeight) p.vy *= -1;
          p.ph += p.ps; p.el.style.opacity = (p.base + Math.sin(p.ph) * 0.15).toString();
        }
        p.el.style.transform = 'translate(' + p.x + 'px,' + p.y + 'px)';
      });
      updateWatermarks();
      particleAnimId = requestAnimationFrame(tick);
    }
    function triggerImplode() { imploding = true; }

    // ---- watermarks ----
    var watermarks = [];
    var watermarkCount = 22;
    var watermarkSymbols = [
      'C', 'H', 'O', 'N', 'Cl',
      'H₂O', 'CO₂', 'NH₃', 'HCl', 'CH₄',
      'C=O', 'N-H', 'O-H', 'C-Cl'
    ];
    var symbolColors = {
      'C': '#1e293b',    // Carbon (Deep Slate)
      'H': '#0284c7',    // Hydrogen (Vivid Cyan/Blue)
      'O': '#dc2626',    // Oxygen (Bright Red)
      'N': '#4f46e5',    // Nitrogen (Deep Indigo)
      'Cl': '#16a34a',   // Chlorine (Vibrant Green)
      'H₂O': '#0891b2',  // Water (Teal/Cyan)
      'CO₂': '#475569',  // Carbon Dioxide (Slate Grey)
      'NH₃': '#6366f1',  // Ammonia (Purple Indigo)
      'HCl': '#059669',  // Hydrochloric Acid (Emerald)
      'CH₄': '#0d9488',  // Methane (Dark Teal)
      'C=O': '#e11d48',  // Carbonyl group (Vibrant Crimson)
      'N-H': '#6366f1',  // Amide bond (Vivid Violet)
      'O-H': '#ea580c',  // Hydroxyl group (Vibrant Orange)
      'C-Cl': '#15803d'  // Alkyl chloride (Forest Green)
    };

    function initWatermarks() {
      var field = document.getElementById('watermark-field');
      if (!field) return;
      field.innerHTML = '';
      watermarks = [];
      for (var i = 0; i < watermarkCount; i++) {
        var el = document.createElement('div');
        el.className = 'watermark-node';
        var symbol = watermarkSymbols[Math.floor(Math.random() * watermarkSymbols.length)];
        el.textContent = symbol;
        var x = Math.random() * window.innerWidth;
        var y = Math.random() * window.innerHeight;
        var size = 20 + Math.random() * 55;
        var speed = 0.15 + Math.random() * 0.35;
        var angle = Math.random() * Math.PI * 2;
        var color = symbolColors[symbol] || '#138aa5';
        var baseOpacity = 0.35 + Math.random() * 0.30;
        el.style.fontSize = size + 'px';
        el.style.color = color;
        var curAngle = Math.random() * 360;
        el.style.transform = 'translate(' + x + 'px,' + y + 'px) rotate(' + curAngle + 'deg)';
        field.appendChild(el);
        (function(element, opacityVal) {
          setTimeout(function() {
            element.style.opacity = opacityVal.toString();
          }, 50 + i * 20);
        })(el, baseOpacity);
        watermarks.push({
          el: el,
          x: x,
          y: y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          angle: curAngle,
          rotSpeed: -0.15 + Math.random() * 0.3
        });
      }
    }

    function updateWatermarks() {
      watermarks.forEach(function(w) {
        w.x += w.vx;
        w.y += w.vy;
        w.angle += w.rotSpeed;
        if (w.x < -120) w.x = window.innerWidth + 50;
        if (w.x > window.innerWidth + 120) w.x = -50;
        if (w.y < -120) w.y = window.innerHeight + 50;
        if (w.y > window.innerHeight + 120) w.y = -50;
        w.el.style.transform = 'translate(' + w.x + 'px,' + w.y + 'px) rotate(' + w.angle + 'deg)';
      });
    }

    function fadeOutWatermarks() {
      watermarks.forEach(function(w) {
        w.el.style.opacity = '0';
      });
    }
    var stT = null, tot = 2700;
    function rafProgress() {
      if (!stT) { stT = 1; }
      var start = performance.now();
      function frame(now) {
        var elapsed = now - start, prog = Math.min(1, elapsed / tot), pct = Math.floor(prog * 100);
        if (pbFill) pbFill.style.width = pct + '%';
        var phase = 'INITIALIZING SYSTEM';
        if (elapsed < 550) phase = 'IDENTIFYING PATHOGEN TARGET';
        else if (elapsed < 1100) phase = 'SCANNING ACTIVE POCKET';
        else if (elapsed < 1700) phase = 'SYNTHESIZING LIGAND SCAFFOLDS';
        else if (elapsed < 2350) phase = 'RUNNING VQE DOCKING SOLVER';
        else phase = 'DOCKING SIMULATION COMPLETED';
        if (pbText) pbText.textContent = phase + '... ' + pct + '%';
        if (prog < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }
  }
})();
