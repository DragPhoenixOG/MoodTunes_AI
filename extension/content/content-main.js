// MoodTunes AI – Content Script Main Entry
// Detects platform, loads appropriate adapter, throttles and sends context

import { WhatsAppAdapter } from './adapters/whatsapp-adapter.js';
import { TelegramAdapter } from './adapters/telegram-adapter.js';
import { DiscordAdapter } from './adapters/discord-adapter.js';
import { SlackAdapter } from './adapters/slack-adapter.js';
import { GmailAdapter } from './adapters/gmail-adapter.js';
import { LinkedInAdapter } from './adapters/linkedin-adapter.js';
import { RedditAdapter } from './adapters/reddit-adapter.js';
import { TwitterAdapter } from './adapters/twitter-adapter.js';
import { MessengerAdapter } from './adapters/messenger-adapter.js';
import { GenericAdapter } from './adapters/generic-adapter.js';
import { SecurityFilter } from './security-filter.js';

const DEBOUNCE_MS = 3000;         // 3 s between sends
const MIN_TEXT_LENGTH = 20;       // ignore tiny snippets
const MAX_CONTEXT_CHARS = 2000;   // cap what we ship to backend

const PLATFORM_MAP = [
  { match: /web\.whatsapp\.com/,  Adapter: WhatsAppAdapter,  source: 'whatsapp'  },
  { match: /web\.telegram\.org/,  Adapter: TelegramAdapter,  source: 'telegram'  },
  { match: /discord\.com/,        Adapter: DiscordAdapter,   source: 'discord'   },
  { match: /app\.slack\.com/,     Adapter: SlackAdapter,     source: 'slack'     },
  { match: /mail\.google\.com/,   Adapter: GmailAdapter,     source: 'gmail'     },
  { match: /linkedin\.com/,       Adapter: LinkedInAdapter,  source: 'linkedin'  },
  { match: /reddit\.com/,         Adapter: RedditAdapter,    source: 'reddit'    },
  { match: /twitter\.com|x\.com/, Adapter: TwitterAdapter,   source: 'twitter'   },
  { match: /facebook\.com/,       Adapter: MessengerAdapter, source: 'messenger' },
];

class ContentController {
  constructor() {
    this.adapter = null;
    this.source = 'generic';
    this.lastText = '';
    this.debounceTimer = null;
    this.enabled = true;
  }

  async init() {
    // Load user settings
    const settings = await this.loadSettings();
    if (!settings.enabled) return;
    this.enabled = true;

    // Detect platform
    const url = window.location.hostname;
    const platform = PLATFORM_MAP.find(p => p.match.test(url));
    if (platform) {
      this.adapter = new platform.Adapter();
      this.source = platform.source;
    } else {
      this.adapter = new GenericAdapter();
      this.source = 'generic';
    }

    // Block sensitive pages
    if (SecurityFilter.isSensitivePage(url, document.title)) {
      console.log('[MoodTunes] Skipping sensitive page');
      return;
    }

    this.adapter.observe((text) => this.onTextChanged(text));
    console.log(`[MoodTunes] Active on ${this.source}`);
  }

  onTextChanged(rawText) {
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      const cleaned = SecurityFilter.sanitize(rawText).slice(0, MAX_CONTEXT_CHARS);
      if (cleaned.length < MIN_TEXT_LENGTH) return;
      if (cleaned === this.lastText) return;
      this.lastText = cleaned;
      this.sendToBackground({ source: this.source, text: cleaned });
    }, DEBOUNCE_MS);
  }

  sendToBackground(payload) {
    chrome.runtime.sendMessage({ type: 'CONTEXT_UPDATE', payload });
  }

  async loadSettings() {
    return new Promise(resolve =>
      chrome.storage.local.get({ enabled: true }, resolve)
    );
  }
}

const controller = new ContentController();
controller.init().catch(console.error);
