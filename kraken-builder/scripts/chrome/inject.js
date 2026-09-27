(() => {
  const probe = {
    href: location.href,
    title: document.title,
    h1: (document.querySelector("h1") || {}).textContent || "",
    mit: /MIT|open source/i.test(document.body.innerText || ""),
    exchange: /not the (crypto )?exchange/i.test(document.body.innerText || ""),
    buttons: [...document.querySelectorAll("button, [role=button], input[type=submit]")]
      .map((el) => (el.textContent || el.value || "").trim())
      .filter(Boolean)
      .slice(0, 12),
  };
  const submit = [...document.querySelectorAll("button, span, div")]
    .find((el) => /submit sitemap|add sitemap/i.test(el.textContent || ""));
  if (submit && /search\.google\.com\/search-console/.test(location.href)) {
    probe.searchConsoleHint = submit.textContent.trim();
  }
  return JSON.stringify(probe);
})()
