/* ═══════════════════════════════════════
   SACHIN DHULE — PORTFOLIO | script.js (v3)
   ═══════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─── DARK MODE ─── */
  const themeToggle = document.getElementById('themeToggle');
  const saved = localStorage.getItem('sd-theme');
  if (saved === 'dark') document.body.classList.add('dark');

  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    localStorage.setItem('sd-theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  });

  /* ─── SCROLL PROGRESS BAR ─── */
  const scrollProgress = document.getElementById('scrollProgress');
  function updateProgress() {
    const total  = document.documentElement.scrollHeight - window.innerHeight;
    const done   = window.scrollY;
    const pct    = total > 0 ? (done / total) * 100 : 0;
    scrollProgress.style.width = pct + '%';
  }
  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();

  /* ─── PRELOADER ─── */
  const preloader = document.getElementById('preloader');
  const preFill   = document.getElementById('preFill');
  let pct = 0;
  const preTimer = setInterval(() => {
    pct += Math.random() * 18;
    if (pct >= 100) { pct = 100; clearInterval(preTimer); }
    preFill.style.width = pct + '%';
    if (pct === 100) {
      setTimeout(() => preloader.classList.add('done'), 350);
    }
  }, 80);

  /* ─── CUSTOM CURSOR ─── */
  const cursor   = document.getElementById('cursor');
  const follower = document.getElementById('cursorFollower');
  let mx = 0, my = 0, fx = 0, fy = 0;

  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    cursor.style.left = mx + 'px';
    cursor.style.top  = my + 'px';
  });

  function animateFollower() {
    fx += (mx - fx) * 0.12;
    fy += (my - fy) * 0.12;
    follower.style.left = fx + 'px';
    follower.style.top  = fy + 'px';
    requestAnimationFrame(animateFollower);
  }
  animateFollower();

  document.querySelectorAll('a, button, .skill-card, .svc-card, .timeline-card, .project-card').forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.transform   = 'translate(-50%,-50%) scale(2)';
      follower.style.transform = 'translate(-50%,-50%) scale(0.5)';
      follower.style.borderColor = 'rgba(37,99,235,0.8)';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.transform   = 'translate(-50%,-50%) scale(1)';
      follower.style.transform = 'translate(-50%,-50%) scale(1)';
      follower.style.borderColor = 'rgba(37,99,235,0.35)';
    });
  });

  /* ─── PARTICLE CANVAS ─── */
  const canvas = document.getElementById('particlesCanvas');
  const ctx    = canvas.getContext('2d');
  let   particles = [];
  let   W, H;

  function resizeCanvas() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', () => { resizeCanvas(); initParticles(); });

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x  = Math.random() * W;
      this.y  = Math.random() * H;
      this.r  = Math.random() * 1.6 + 0.3;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.35 + 0.06;
      const palette = ['37,99,235','14,165,233','245,158,11','139,92,246'];
      this.color = palette[Math.floor(Math.random() * palette.length)];
    }
    update() {
      this.x += this.vx; this.y += this.vy;
      if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.color},${this.opacity})`;
      ctx.fill();
    }
  }

  function initParticles() {
    particles = [];
    const count = Math.floor((W * H) / 18000);
    for (let i = 0; i < count; i++) particles.push(new Particle());
  }
  initParticles();

  function drawConnections() {
    const maxDist = 120;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.12;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(37,99,235,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animateParticles() {
    ctx.clearRect(0, 0, W, H);
    drawConnections();
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animateParticles);
  }
  animateParticles();

  /* ─── NAVBAR SCROLL ─── */
  const navbar = document.getElementById('navbar');
  const backTop = document.getElementById('backTop');

  window.addEventListener('scroll', () => {
    const sy = window.scrollY;
    navbar.classList.toggle('scrolled', sy > 50);
    backTop.classList.toggle('visible', sy > 400);
    highlightNavLink();
  });

  /* ─── BACK TO TOP ─── */
  if (backTop) {
    backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  /* ─── HAMBURGER ─── */
  const hamburger = document.getElementById('hamburger');
  const navLinks  = document.getElementById('navLinks');
  hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const spans = hamburger.querySelectorAll('span');
    if (navLinks.classList.contains('open')) {
      spans[0].style.transform = 'translateY(7px) rotate(45deg)';
      spans[1].style.opacity   = '0';
      spans[2].style.transform = 'translateY(-7px) rotate(-45deg)';
    } else {
      spans.forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    }
  });
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburger.querySelectorAll('span').forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    });
  });

  /* ─── ACTIVE NAV HIGHLIGHT ─── */
  const sections = document.querySelectorAll('section[id]');
  function highlightNavLink() {
    const scrollY = window.scrollY + 130;
    sections.forEach(sec => {
      if (scrollY >= sec.offsetTop && scrollY < sec.offsetTop + sec.offsetHeight) {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const active = document.querySelector(`.nav-link[href="#${sec.id}"]`);
        if (active) active.classList.add('active');
      }
    });
  }

  /* ─── TYPEWRITER ─── */
  const roles = [
    'Data Analyst',
    'SQL Developer',
    'Power BI Expert',
    'Python Programmer',
    'Financial Analyst',
  ];
  let rIdx = 0, cIdx = 0, deleting = false;
  const roleDynamic = document.getElementById('roleDynamic');

  function typeRole() {
    const current = roles[rIdx];
    if (!deleting) {
      roleDynamic.textContent = current.slice(0, ++cIdx);
      if (cIdx === current.length) { deleting = true; setTimeout(typeRole, 1800); return; }
    } else {
      roleDynamic.textContent = current.slice(0, --cIdx);
      if (cIdx === 0) { deleting = false; rIdx = (rIdx + 1) % roles.length; }
    }
    setTimeout(typeRole, deleting ? 52 : 88);
  }
  setTimeout(typeRole, 900);

  /* ─── COUNTER ANIMATION ─── */
  function animateCounters() {
    document.querySelectorAll('.stat-number[data-target]').forEach(el => {
      const target = +el.dataset.target;
      let current = 0;
      const step  = Math.ceil(target / 40);
      const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(timer);
      }, 40);
    });
  }

  /* ─── SCROLL REVEAL ─── */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        entry.target.style.transitionDelay = `${i * 0.06}s`;
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  /* ─── SKILL RINGS ANIMATION ─── */
  function runRingCounter(el) {
    const target = +el.dataset.target;
    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      el.textContent = current;
      if (current >= target) { el.textContent = target; clearInterval(interval); }
    }, 15);
  }
  
  const ringsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.ring-fg').forEach((ring, i) => {
          setTimeout(() => {
            const pct = +ring.dataset.pct;
            const offset = 251.2 - (251.2 * pct / 100);
            ring.style.strokeDashoffset = offset;
          }, i * 150);
        });
        entry.target.querySelectorAll('.ring-num').forEach((num, i) => {
          setTimeout(() => runRingCounter(num), i * 150);
        });
        ringsObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  const ringsSection = document.querySelector('.skill-rings');
  if (ringsSection) ringsObserver.observe(ringsSection);

  /* ─── HERO COUNTERS ─── */
  const heroObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) { animateCounters(); heroObserver.disconnect(); }
  }, { threshold: 0.4 });
  const heroSection = document.getElementById('home');
  if (heroSection) heroObserver.observe(heroSection);

  /* ─── CONTACT FORM ─── */
  const form    = document.getElementById('contactForm');
  const success = document.getElementById('formSuccess');
  if (form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const btn  = form.querySelector('#submit-btn');
      const span = btn.querySelector('span');
      btn.disabled = true;
      span.textContent = 'Sending…';
      setTimeout(() => {
        form.reset();
        btn.disabled = false;
        span.textContent = 'Send Message';
        success.classList.add('show');
        setTimeout(() => success.classList.remove('show'), 5000);
      }, 1400);
    });
  }

  /* ─── SMOOTH ANCHOR SCROLL ─── */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ─── TILT ON CARDS ─── */
  document.querySelectorAll('.skill-card, .svc-card, .project-card, .ach-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const xOff = ((e.clientX - rect.left) / rect.width  - 0.5) * 8;
      const yOff = ((e.clientY - rect.top)  / rect.height - 0.5) * -8;
      card.style.transform = `perspective(900px) rotateX(${yOff}deg) rotateY(${xOff}deg) translateY(-5px)`;
    });
    card.addEventListener('mouseleave', () => { card.style.transform = ''; });
  });

  /* ─── ACHIEVEMENTS COUNTER ─── */
  function runAchCounter(el) {
    const target = +el.dataset.count;
    const suffix = el.dataset.suffix || '';
    let current  = 0;
    const steps    = 55;
    const inc      = target / steps;
    const interval = 1300 / steps;
    const timer = setInterval(() => {
      current = Math.min(current + inc, target);
      el.textContent = Math.floor(current) + suffix;
      if (current >= target) { el.textContent = target + suffix; clearInterval(timer); }
    }, interval);
  }
  const achObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.ach-big[data-count]').forEach(el => runAchCounter(el));
        achObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });
  const achStrip = document.querySelector('.achievements-strip');
  if (achStrip) achObserver.observe(achStrip);

  /* ─── TESTIMONIALS CAROUSEL ─── */
  const testiTrack   = document.getElementById('testiTrack');
  const testiDots    = document.querySelectorAll('.testi-dot');
  const testiBtnPrev = document.getElementById('testiBtnPrev');
  const testiBtnNext = document.getElementById('testiBtnNext');
  if (testiTrack) {
    const total   = testiTrack.querySelectorAll('.testi-card').length;
    let current   = 0;
    let autoTimer = null;
    function goTo(idx) {
      current = (idx + total) % total;
      testiTrack.style.transform = `translateX(-${current * 100}%)`;
      testiDots.forEach((d, i) => d.classList.toggle('active', i === current));
    }
    const startAuto = () => { autoTimer = setInterval(() => goTo(current + 1), 5200); };
    const stopAuto  = () => clearInterval(autoTimer);
    testiBtnPrev.addEventListener('click', () => { stopAuto(); goTo(current - 1); startAuto(); });
    testiBtnNext.addEventListener('click', () => { stopAuto(); goTo(current + 1); startAuto(); });
    testiDots.forEach(d => d.addEventListener('click', () => { stopAuto(); goTo(+d.dataset.idx); startAuto(); }));
    testiTrack.addEventListener('mouseenter', stopAuto);
    testiTrack.addEventListener('mouseleave', startAuto);
    let touchX = 0;
    testiTrack.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; }, { passive: true });
    testiTrack.addEventListener('touchend',   e => {
      const diff = touchX - e.changedTouches[0].clientX;
      if (Math.abs(diff) > 50) { stopAuto(); goTo(current + (diff > 0 ? 1 : -1)); startAuto(); }
    });
    goTo(0); startAuto();
  }

  /* ─── CURSOR TRAIL ─── */
  const trailCanvas = document.createElement('canvas');
  trailCanvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:1;mix-blend-mode:multiply;opacity:0.5;';
  document.body.appendChild(trailCanvas);
  const tc = trailCanvas.getContext('2d');
  trailCanvas.width  = window.innerWidth;
  trailCanvas.height = window.innerHeight;
  window.addEventListener('resize', () => {
    trailCanvas.width  = window.innerWidth;
    trailCanvas.height = window.innerHeight;
  });

  const trail = [];
  document.addEventListener('mousemove', e => {
    trail.push({ x: e.clientX, y: e.clientY, age: 0 });
    if (trail.length > 22) trail.shift();
  });

  function drawTrail() {
    tc.clearRect(0, 0, trailCanvas.width, trailCanvas.height);
    trail.forEach(p => {
      p.age++;
      const alpha = Math.max(0, 1 - p.age / 22) * 0.3;
      const r     = (1 - p.age / 22) * 4;
      if (r > 0) {
        tc.beginPath();
        tc.arc(p.x, p.y, r, 0, Math.PI * 2);
        tc.fillStyle = `rgba(37,99,235,${alpha})`;
        tc.fill();
      }
    });
    requestAnimationFrame(drawTrail);
  }
  drawTrail();

  /* ─── SECTION NUMBER BADGES (Services) ─── */
  // Already handled in CSS/HTML — no extra JS needed

});
