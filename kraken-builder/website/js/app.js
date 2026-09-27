import { bindTentacleScroll } from "./tentacle-scroll.js";

const { createApp } = Vue;

const LINES = [
  "kraken tentacle add examples/tentacles/geo",
  "kraken tentacle add examples/tentacles/weather-pro",
  "kraken tentacle plan weather-pro",
  "kraken license set weather-pro YOUR_KEY",
  "kraken run weather-pro forecast --compose",
];

createApp({
  data() {
    return {
      tagline: "One binary. Many tentacles.",
      api: "https://api.topta.co",
      tentacles: [],
      typed: "",
      line: 0,
      tentacleName: "weather-pro",
      licenseKey: "",
      redeemMsg: "Offline-first. This form posts to the API when a key is present.",
    };
  },
  mounted() {
    bindTentacleScroll();
    this.loadCatalog();
    this.typeLoop();
    this.watchNav();
  },
  methods: {
    watchNav() {
      const links = [...document.querySelectorAll(".nav nav a[href^='#']")];
      const map = new Map();
      links.forEach((a) => {
        const id = a.getAttribute("href").slice(1);
        const el = document.getElementById(id);
        if (el) map.set(el, a);
      });
      if (!map.size || !("IntersectionObserver" in window)) return;
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          const a = map.get(e.target);
          if (a) a.classList.toggle("is-active", e.isIntersecting && e.intersectionRatio > 0.2);
        });
      }, { threshold: [0.25, 0.5] });
      map.forEach((_, el) => io.observe(el));
    },
    async loadCatalog() {
      try {
        const remote = await fetch(`${this.api}/api/kraken/catalog`);
        if (remote.ok) {
          const data = await remote.json();
          if (data.tentacles) {
            this.tentacles = data.tentacles;
            return;
          }
        }
      } catch (err) {
        /* fall through to static catalog */
      }
      const local = await fetch("catalog.json");
      const data = await local.json();
      this.tentacles = data.tentacles || [];
    },
    typeLoop() {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        this.typed = LINES.join(" · ");
        return;
      }
      const text = LINES[this.line % LINES.length];
      let i = 0;
      const tick = () => {
        this.typed = text.slice(0, i);
        i += 1;
        if (i <= text.length) {
          setTimeout(tick, 28);
        } else {
          setTimeout(() => {
            this.line += 1;
            this.typeLoop();
          }, 1200);
        }
      };
      tick();
    },
    async redeem() {
      if (!this.licenseKey) {
        this.redeemMsg = "missing tentacle key — kraken license set " + this.tentacleName + " <key>";
        return;
      }
      try {
        const res = await fetch(`${this.api}/api/kraken/licenses/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tentacle: this.tentacleName, key: this.licenseKey, product: "kraken" }),
        });
        const data = await res.json();
        this.redeemMsg = data.ok ? "license accepted" : (data.error || "license rejected");
      } catch (err) {
        this.redeemMsg = "API unreachable. Store locally: kraken license set " + this.tentacleName + " " + this.licenseKey;
      }
    },
  },
}).mount("#app");
