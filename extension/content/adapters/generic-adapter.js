// MoodTunes AI – Generic Website Adapter
// Reads visible text from common content elements

const CONTENT_SELECTORS = [
  'p', 'h1', 'h2', 'h3', 'article', 'main',
  '[role="main"]', '.content', '#content',
];

export class GenericAdapter {
  constructor() {
    this._observer = null;
  }

  observe(callback) {
    this._callback = callback;
    this._attachObserver();
    callback(this._extractText());
  }

  _attachObserver() {
    this._observer = new MutationObserver(() => {
      callback(this._extractText());
    });
    this._observer.observe(document.body, { childList: true, subtree: true });
  }

  _extractText() {
    const texts = [];
    CONTENT_SELECTORS.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        if (!this._isVisible(el)) return;
        const txt = el.innerText?.trim();
        if (txt && txt.length > 20) texts.push(txt);
      });
    });
    return [...new Set(texts)].join('\n').slice(0, 3000);
  }

  _isVisible(el) {
    const style = window.getComputedStyle(el);
    return style.display !== 'none' &&
           style.visibility !== 'hidden' &&
           style.opacity !== '0';
  }

  disconnect() {
    this._observer?.disconnect();
  }
}

// Telegram, Discord, Slack, Gmail, LinkedIn, Reddit, Twitter, Messenger adapters
// follow same pattern with platform-specific selectors

export class TelegramAdapter {
  observe(callback) {
    this._callback = callback;
    const observer = new MutationObserver(() => {
      const msgs = document.querySelectorAll('.message .text-content');
      const text = [...msgs].slice(-20).map(m => m.innerText).join('\n');
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class DiscordAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const msgs = document.querySelectorAll('[class*="messageContent"]');
      const text = [...msgs].slice(-20).map(m => m.innerText).join('\n');
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class SlackAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const msgs = document.querySelectorAll('[data-qa="message_content"]');
      const text = [...msgs].slice(-20).map(m => m.innerText).join('\n');
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class GmailAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const body = document.querySelector('[role="main"] .a3s');
      if (body) callback(body.innerText?.slice(0, 2000) || '');
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class LinkedInAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const feed = document.querySelectorAll('.feed-shared-update-v2__description, .msg-s-event-listitem__body');
      const text = [...feed].slice(-15).map(m => m.innerText).join('\n');
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class RedditAdapter {
  observe(callback) {
    const text = [...document.querySelectorAll('[data-testid="post-content"] p, .Comment p')]
      .slice(-20).map(m => m.innerText).join('\n');
    if (text) callback(text);
    new MutationObserver(() => {
      const t = [...document.querySelectorAll('.Comment p')].slice(-20).map(m => m.innerText).join('\n');
      if (t) callback(t);
    }).observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class TwitterAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const tweets = document.querySelectorAll('[data-testid="tweetText"]');
      const text = [...tweets].slice(-20).map(m => m.innerText).join('\n');
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}

export class MessengerAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const msgs = document.querySelectorAll('[dir="auto"][class*="x1lliihq"]');
      const text = [...msgs].slice(-20).map(m => m.innerText).join('\n');
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  disconnect() {}
}
