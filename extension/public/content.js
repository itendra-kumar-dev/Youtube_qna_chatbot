(function () {
  const key = 'nova-enabled'; let enabled = true; let button; let frame;
  const getVideoId = () => new URLSearchParams(location.search).get('v');
  const update = () => { button.classList.toggle('nova-off', !enabled); frame.classList.toggle('nova-hidden', !enabled); button.textContent = enabled ? 'NOVA' : 'NOVA · off'; };
  const render = () => { if (!button) { button = document.createElement('button'); button.id = 'nova-toggle'; document.body.appendChild(button); button.onclick = () => { enabled = !enabled; chrome.storage.local.set({ [key]: enabled }); update(); }; } if (!frame) { frame = document.createElement('iframe'); frame.id = 'nova-panel'; frame.title = 'NOVA video assistant'; document.body.appendChild(frame); } frame.src = chrome.runtime.getURL(`index.html?videoId=${encodeURIComponent(getVideoId() || '')}`); update(); };
  chrome.storage.local.get(key, (value) => { enabled = value[key] !== false; render(); }); let lastUrl = location.href; setInterval(() => { if (location.href !== lastUrl) { lastUrl = location.href; render(); } }, 800);
})();