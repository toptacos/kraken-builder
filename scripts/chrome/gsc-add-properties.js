(() => {
  const log = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const text = (el) => ((el && (el.innerText || el.textContent)) || "").trim();

  function clickByText(re) {
    const els = [...document.querySelectorAll("button, [role=button], div, span, a")];
    const el = els.find((e) => re.test(text(e)) && text(e).length < 80);
    if (el) {
      el.click();
      return text(el).slice(0, 60);
    }
    return null;
  }

  function fillPrefix(url) {
    const inputs = [...document.querySelectorAll("input")];
    const input = inputs.find((i) => /http|url|prefix|website/i.test((i.placeholder || "") + (i.getAttribute("aria-label") || "") + (i.name || ""))) || inputs[inputs.length - 1];
    if (!input) return false;
    input.focus();
    input.value = url;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  async function addOne(url) {
    const step = { url };
    clickByText(/^URL prefix$/i) || clickByText(/URL prefix/i);
    await sleep(400);
    step.filled = fillPrefix(url);
    await sleep(400);
    step.continue = clickByText(/^Continue$/i) || clickByText(/^Add$/i) || clickByText(/^Next$/i);
    await sleep(2500);
    step.verify = clickByText(/^Verify$/i) || clickByText(/Verify ownership/i);
    await sleep(2500);
    step.body = (document.body.innerText || "").slice(0, 500);
    step.ok = /ownership verified|property added|already verified|success/i.test(step.body);
    log.push(step);
    return step;
  }

  window.__gscAdd = addOne;
  window.__gscLog = log;
  return "ready";
})()
