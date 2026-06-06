// MoodTunes AI – WhatsApp Web Adapter
export class WhatsAppAdapter {
  constructor() {
    this._observer = null;
    this._callback = null;
  }

  observe(callback) {
    this._callback = callback;
    this._waitForChat();
  }

  _waitForChat() {
    const interval = setInterval(() => {
      const container = document.querySelector('#main');
      if (container) {
        clearInterval(interval);
        this._attachObserver(container);
      }
    }, 1000);
  }

  _attachObserver(container) {
    this._observer = new MutationObserver(() => {
      const text = this._extractText();
      if (text) this._callback(text);
    });
    this._observer.observe(container, { childList: true, subtree: true });
    // Initial read
    const text = this._extractText();
    if (text) this._callback(text);
  }

  _extractText() {
    // WhatsApp message bubbles: .message-in and .message-out
    const msgs = document.querySelectorAll(
      '[data-pre-plain-text], .copyable-text'
    );
    const lines = [];
    msgs.forEach(el => {
      const txt = el.innerText?.trim();
      if (txt && txt.length > 2) lines.push(txt);
    });
    // Only last 20 visible messages
    return lines.slice(-20).join('\n');
  }

  disconnect() {
    this._observer?.disconnect();
  }
}
