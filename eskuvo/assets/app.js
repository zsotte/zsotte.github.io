(async function () {
  const $ = (id) => document.getElementById(id);
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  let data;
  try {
    data = await (await fetch("media.json", { cache: "no-cache" })).json();
  } catch (e) {
    data = { photos: [], videos: [] };
  }

  const info = data.info || {};
  if (info.date) $("wedding-date").textContent = info.date;
  $("wedding-place").textContent = info.place || "";
  (info.intro || []).forEach((t) => {
    const p = document.createElement("p");
    p.className = "reveal";
    p.textContent = t;
    $("intro-text").appendChild(p);
  });
  $("intro-signature").textContent = info.signature || "";

  const photos = data.photos || [];
  const videos = data.videos || [];
  $("photo-count").textContent = photos.length || "";
  $("video-count").textContent = videos.length || "";

  // Megjelenés görgetéskor
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  const observe = (el) => (reduceMotion ? el.classList.add("in") : io.observe(el));
  document.querySelectorAll(".reveal").forEach(observe);

  // Fotók
  const gallery = $("gallery");
  let visible = photos;

  // Időrendben balra-jobbra töltött oszlopok: mindig a legrövidebb oszlop kapja a következő képet
  const colCount = () => (innerWidth >= 1100 ? 4 : innerWidth >= 760 ? 3 : 2);
  let cols = 0;

  function renderGallery() {
    cols = colCount();
    gallery.innerHTML = "";
    const columns = Array.from({ length: cols }, () => {
      const c = document.createElement("div");
      c.className = "gcol";
      gallery.appendChild(c);
      return c;
    });
    const heights = new Array(cols).fill(0);
    visible.forEach((p, i) => {
      const a = document.createElement("a");
      a.href = p.src;
      a.style.transitionDelay = `${(i % cols) * 70}ms`;
      const img = document.createElement("img");
      img.src = p.thumb;
      img.alt = p.caption || "";
      img.loading = "lazy";
      img.decoding = "async";
      img.width = p.w;
      img.height = p.h;
      a.appendChild(img);
      a.addEventListener("click", (e) => { e.preventDefault(); openLb(i); });
      let k = 0;
      for (let j = 1; j < cols; j++) if (heights[j] < heights[k] - 0.01) k = j;
      columns[k].appendChild(a);
      heights[k] += p.h / p.w;
      observe(a);
    });
    $("photos-empty").hidden = visible.length > 0;
  }

  const groups = [...new Set(photos.map((p) => p.group).filter(Boolean))];
  if (groups.length > 1) {
    const filters = $("filters");
    ["Összes", ...groups].forEach((g, idx) => {
      const b = document.createElement("button");
      b.textContent = g;
      b.setAttribute("aria-pressed", idx === 0 ? "true" : "false");
      b.onclick = () => {
        filters.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", "false"));
        b.setAttribute("aria-pressed", "true");
        visible = idx === 0 ? photos : photos.filter((p) => p.group === g);
        renderGallery();
      };
      filters.appendChild(b);
    });
  }
  renderGallery();
  addEventListener("resize", () => { if (colCount() !== cols) renderGallery(); });

  // Videók
  const vwrap = $("videos");
  videos.forEach((v) => {
    const card = document.createElement("article");
    card.className = "video-card reveal";
    const el = document.createElement("video");
    el.controls = true;
    el.preload = "none";
    el.playsInline = true;
    if (v.poster) el.poster = v.poster;
    const s = document.createElement("source");
    s.src = v.src;
    s.type = "video/mp4";
    el.appendChild(s);
    const h = document.createElement("h3");
    h.textContent = v.title || "";
    card.append(el, h);
    if (v.duration) {
      const p = document.createElement("p");
      p.textContent = v.duration;
      card.appendChild(p);
    }
    vwrap.appendChild(card);
    observe(card);
  });
  if (!videos.length) {
    $("videok").hidden = true;
    document.querySelector('.tab[href="#videok"]').hidden = true;
  }

  // Zene
  const audio = $("audio"), btn = $("music");
  let resumeMusic = false;
  if (info.music) {
    audio.src = info.music;
    btn.hidden = false;
  }
  function fade(to, done) {
    const step = (to - audio.volume) / 20;
    let n = 0;
    const t = setInterval(() => {
      audio.volume = Math.min(1, Math.max(0, audio.volume + step));
      if (++n >= 20) { clearInterval(t); done && done(); }
    }, 40);
  }
  function setMusic(on) {
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.setAttribute("aria-label", on ? "Zene ki" : "Zene be");
    if (on) {
      audio.volume = 0;
      audio.play().then(() => fade(0.6)).catch(() => setMusic(false));
    } else {
      fade(0, () => audio.pause());
    }
  }
  btn.onclick = () => setMusic(audio.paused);
  audio.addEventListener("error", () => { btn.hidden = true; });

  // Videó indításakor a zene és a többi videó megáll
  document.addEventListener("play", (e) => {
    if (e.target.tagName !== "VIDEO") return;
    document.querySelectorAll("video").forEach((v) => { if (v !== e.target) v.pause(); });
    if (!audio.paused) { resumeMusic = true; setMusic(false); }
  }, true);
  document.addEventListener("pause", (e) => {
    if (e.target.tagName === "VIDEO" && resumeMusic) {
      const anyPlaying = [...document.querySelectorAll("video")].some((v) => !v.paused);
      if (!anyPlaying) { resumeMusic = false; setMusic(true); }
    }
  }, true);

  // Lightbox
  const lb = $("lightbox"), lbImg = $("lb-img");
  let cur = 0;

  function show(i) {
    cur = (i + visible.length) % visible.length;
    const p = visible[cur];
    lbImg.src = p.src;
    lbImg.alt = p.caption || "";
    $("lb-caption").textContent = p.caption || "";
    $("lb-pos").textContent = `${cur + 1} / ${visible.length}`;
    $("lb-download").href = p.download || p.src;
    [cur + 1, cur - 1].forEach((n) => {
      const q = visible[(n + visible.length) % visible.length];
      if (q) new Image().src = q.src;
    });
  }
  function openLb(i) { lb.hidden = false; document.body.style.overflow = "hidden"; show(i); }
  function closeLb() { lb.hidden = true; document.body.style.overflow = ""; lbImg.src = ""; }

  $("lb-close").onclick = closeLb;
  $("lb-prev").onclick = () => show(cur - 1);
  $("lb-next").onclick = () => show(cur + 1);
  lb.addEventListener("click", (e) => { if (e.target === lb) closeLb(); });
  document.addEventListener("keydown", (e) => {
    if (lb.hidden) return;
    if (e.key === "Escape") closeLb();
    if (e.key === "ArrowLeft") show(cur - 1);
    if (e.key === "ArrowRight") show(cur + 1);
  });
  let x0 = null;
  lb.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener("touchend", (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) show(cur + (dx < 0 ? 1 : -1));
    x0 = null;
  });

  // Lassan hulló szirmok a háttérben
  if (!reduceMotion) {
    const cv = $("petals"), ctx = cv.getContext("2d");
    const rgb = getComputedStyle(document.documentElement).getPropertyValue("--petal").trim();
    let W, H, dpr, petals = [];
    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = cv.width = innerWidth * dpr;
      H = cv.height = innerHeight * dpr;
      const n = Math.round(Math.min(34, innerWidth / 40));
      petals = Array.from({ length: n }, () => newPetal(true));
    }
    function newPetal(anywhere) {
      return {
        x: Math.random() * W,
        y: anywhere ? Math.random() * H : -20 * dpr,
        r: (4 + Math.random() * 6) * dpr,
        vy: (0.15 + Math.random() * 0.35) * dpr,
        sway: Math.random() * Math.PI * 2,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.01,
        a: 0.25 + Math.random() * 0.35,
      };
    }
    function frame() {
      ctx.clearRect(0, 0, W, H);
      petals.forEach((p, i) => {
        p.sway += 0.008;
        p.y += p.vy;
        p.x += Math.sin(p.sway) * 0.35 * dpr;
        p.rot += p.vr;
        if (p.y > H + 20 * dpr) petals[i] = newPetal(false);
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = `rgba(${rgb}, ${p.a})`;
        ctx.beginPath();
        ctx.ellipse(0, 0, p.r, p.r * 0.55, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });
      if (!document.hidden) requestAnimationFrame(frame);
    }
    document.addEventListener("visibilitychange", () => { if (!document.hidden) requestAnimationFrame(frame); });
    addEventListener("resize", resize);
    const hero = document.querySelector(".hero");
    new IntersectionObserver(([e]) => cv.classList.toggle("dim", !e.isIntersecting), { threshold: 0.15 }).observe(hero);
    resize();
    requestAnimationFrame(frame);
  }
})();
