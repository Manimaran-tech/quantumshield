/* ============================================================
   QuantumShield — Lando Norris Motion & Interaction Enhancer
   ============================================================ */
(function () {
  'use strict';

  // 1. Check for reduced motion preference
  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 2. Initialize Lenis Smooth Scroll
  if (!prefersReduced && typeof Lenis !== 'undefined') {
    var lenis = new Lenis({
      lerp: 0.1,
      smoothWheel: true,
      syncTouch: false
    });
    window.lenis = lenis;

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }

  // 3. Helper to split text content into stagger-ready characters
  function splitTextToChars(element) {
    var text = element.textContent.trim();
    element.innerHTML = '';
    var charIndex = 0;
    
    for (var i = 0; i < text.length; i++) {
      var char = text[i];
      var span = document.createElement('span');
      if (char === ' ') {
        span.innerHTML = '&nbsp;';
      } else {
        span.textContent = char;
        span.className = 'q-ch';
        span.setAttribute('data-letter', char);
        span.style.setProperty('--i', charIndex);
        charIndex++;
      }
      // Ensure spaces also keep correct display properties but don't increment character index
      if (char === ' ') {
        span.className = 'q-space';
        span.style.display = 'inline-block';
      }
      element.appendChild(span);
    }
  }

  // 4. Restructure Buttons (.btn-enter) & split characters
  function enhanceButtons() {
    document.querySelectorAll('.btn-enter').forEach(function (btn) {
      if (btn.dataset.enhanced) return;
      btn.dataset.enhanced = '1';
      btn.setAttribute('data-roll', 'true');

      // Strip arrow characters if they exist in the raw markup
      var rawText = btn.textContent;
      var cleanText = rawText.replace('→', '').replace('↗', '').trim();

      btn.innerHTML = '';

      var textSpan = document.createElement('span');
      textSpan.className = 'qbtn-text';
      textSpan.textContent = cleanText;
      btn.appendChild(textSpan);

      // Split button text characters
      splitTextToChars(textSpan);

      // Append Lando-style up-right arrow
      var arrSpan = document.createElement('span');
      arrSpan.className = 'qbtn-arr';
      arrSpan.textContent = ' ↗';
      btn.appendChild(arrSpan);
    });
  }

  // 5. Split Eyebrows text spans into characters
  function enhanceEyebrows() {
    document.querySelectorAll('.eyebrow span:not(.n):not(.bar)').forEach(function (span) {
      if (span.dataset.enhanced) return;
      span.dataset.enhanced = '1';
      span.setAttribute('data-roll', 'true');
      splitTextToChars(span);
    });
  }

  // Run the enhancements
  // enhanceButtons(); // Disabled to prevent double text rendering
  enhanceEyebrows();

})();
