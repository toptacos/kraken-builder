function lengthOf(path) {
  return path.getTotalLength();
}

function placeSuckers(path, group, count) {
  group.replaceChildren();
  const len = lengthOf(path);
  for (let i = 1; i <= count; i += 1) {
    const t = i / (count + 1);
    const pt = path.getPointAtLength(len * t);
    const nxt = path.getPointAtLength(Math.min(len, len * t + 8));
    const ang = Math.atan2(nxt.y - pt.y, nxt.x - pt.x);
    const r = 7 - t * 4;
    const off = 16 - t * 8;
    const cx = pt.x + Math.cos(ang + Math.PI / 2) * off;
    const cy = pt.y + Math.sin(ang + Math.PI / 2) * off;
    const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    ring.setAttribute("cx", String(cx));
    ring.setAttribute("cy", String(cy));
    ring.setAttribute("r", String(r));
    ring.setAttribute("class", "sucker");
    ring.dataset.t = String(t);
    group.appendChild(ring);
    const hole = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    hole.setAttribute("cx", String(cx));
    hole.setAttribute("cy", String(cy));
    hole.setAttribute("r", String(r * 0.35));
    hole.setAttribute("class", "sucker-hole");
    hole.dataset.t = String(t);
    group.appendChild(hole);
  }
}

export function bindTentacleScroll() {
  const path = document.getElementById("fill-path");
  const suckers = document.getElementById("suckers");
  if (!path) return;
  const len = lengthOf(path);
  path.style.strokeDasharray = String(len);
  path.style.strokeDashoffset = String(len);
  if (suckers) placeSuckers(path, suckers, 26);

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const paint = (t) => {
    path.style.strokeDashoffset = reduced ? "0" : String(len * (1 - t));
    document.querySelectorAll(".sucker, .sucker-hole").forEach((el) => {
      const st = Number(el.dataset.t || 0);
      const on = t >= st - 0.02;
      el.style.opacity = on ? "1" : "0";
      el.classList.toggle("on", on);
    });
    document.querySelectorAll("[data-latch]").forEach((el) => {
      const latch = Number(el.getAttribute("data-latch") || 0);
      el.classList.toggle("latched", t >= latch);
    });
    document.documentElement.style.setProperty("--awake", t.toFixed(3));
    document.documentElement.classList.toggle("scrolled", t > 0.2);
  };

  const onScroll = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const raw = max <= 0 ? 1 : Math.min(1, Math.max(0, window.scrollY / max));
    const t = reduced ? 1 : 0.18 + raw * 0.82;
    paint(t);
  };
  paint(reduced ? 1 : 0.12);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);

  const layer = document.querySelector("#tentacle-layer svg");
  if (layer && !reduced) {
    const tick = (now) => {
      const x = Math.sin(now / 1600) * 10;
      const y = Math.sin(now / 2300) * 6;
      layer.style.transform = `translate(${x}px, ${y}px)`;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
}
