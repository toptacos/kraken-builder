/* Custom portrait player — still + audio, no talking-head chrome. */
(function () {
  function fmt(s) {
    s = Math.max(0, s || 0);
    const m = Math.floor(s / 60);
    const r = Math.floor(s % 60);
    return m + ":" + String(r).padStart(2, "0");
  }
  document.querySelectorAll("[data-voice]").forEach((card) => {
    const audio = card.querySelector("audio");
    const btn = card.querySelector(".voice-play");
    const time = card.querySelector(".voice-time");
    if (!audio || !btn) return;
    const sync = () => {
      const on = !audio.paused;
      card.classList.toggle("is-playing", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.textContent = on ? "❚❚" : "▶";
      btn.setAttribute("aria-label", on ? "Pause Nyx" : "Play Nyx");
      if (time) time.textContent = fmt(audio.currentTime) + " / " + fmt(audio.duration || 0);
    };
    btn.addEventListener("click", () => {
      if (audio.paused) audio.play();
      else audio.pause();
    });
    audio.addEventListener("play", sync);
    audio.addEventListener("pause", sync);
    audio.addEventListener("timeupdate", sync);
    audio.addEventListener("loadedmetadata", sync);
    sync();
  });
})();
