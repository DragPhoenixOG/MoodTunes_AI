// MoodTunes AI - Content Script (no imports, no modules)
var DEBOUNCE_MS = 5000;
var MIN_TEXT_LENGTH = 30;
var MAX_CONTEXT_CHARS = 2000;

var BLOCKED_DOMAINS = [
  'bankofamerica', 'chase.com', 'wellsfargo', 'paypal.com', 'stripe.com'
];

function isSensitivePage() {
  var host = window.location.hostname;
  for (var i = 0; i < BLOCKED_DOMAINS.length; i++) {
    if (host.indexOf(BLOCKED_DOMAINS[i]) !== -1) return true;
  }
  return false;
}

function sanitizeText(text) {
  return text
    .replace(/\b\d{4,8}\b/g, '')
    .replace(/Bearer\s+\S+/gi, '')
    .replace(/\s{3,}/g, ' ')
    .trim();
}

function detectPlatform() {
  var host = window.location.hostname;
  if (host.indexOf('web.whatsapp.com') !== -1) return 'whatsapp';
  if (host.indexOf('web.telegram.org') !== -1) return 'telegram';
  if (host.indexOf('discord.com') !== -1)      return 'discord';
  if (host.indexOf('slack.com') !== -1)        return 'slack';
  if (host.indexOf('mail.google.com') !== -1)  return 'gmail';
  if (host.indexOf('linkedin.com') !== -1)     return 'linkedin';
  if (host.indexOf('reddit.com') !== -1)       return 'reddit';
  if (host.indexOf('twitter.com') !== -1 || host.indexOf('x.com') !== -1) return 'twitter';
  if (host.indexOf('facebook.com') !== -1)     return 'messenger';
  return 'generic';
}

function extractText(platform) {
  var sel = 'p, h1, h2, h3';
  if (platform === 'whatsapp')  sel = '[data-pre-plain-text], .copyable-text';
  if (platform === 'telegram')  sel = '.tgme_widget_message_text';
  if (platform === 'discord')   sel = '[class*="messageContent"]';
  if (platform === 'slack')     sel = '[data-qa="message_content"]';
  if (platform === 'gmail')     sel = '.a3s';
  if (platform === 'reddit')    sel = '.Comment p';
  if (platform === 'twitter')   sel = '[data-testid="tweetText"]';
  if (platform === 'linkedin')  sel = '.feed-shared-update-v2__description';

  var elements = document.querySelectorAll(sel);
  var texts = [];
  for (var i = 0; i < elements.length; i++) {
    var t = elements[i].innerText && elements[i].innerText.trim();
    if (t && t.length > 5) texts.push(t);
  }
  return texts.slice(-20).join('\n').slice(0, MAX_CONTEXT_CHARS);
}

// Safe message sender - handles extension context invalidated gracefully
function safeSendMessage(payload) {
  try {
    chrome.runtime.sendMessage({
      type: 'CONTEXT_UPDATE',
      payload: payload
    }, function(response) {
      // Ignore response errors
      if (chrome.runtime.lastError) {
        // Extension was reloaded - stop the observer silently
        if (observer) {
          observer.disconnect();
        }
      }
    });
  } catch (e) {
    // Extension context invalidated - stop observing
    if (observer) {
      observer.disconnect();
    }
    console.log('[MoodTunes] Extension reloaded - please refresh this page');
  }
}

var observer = null;

if (!isSensitivePage()) {
  var platform = detectPlatform();
  console.log('[MoodTunes] Active on', platform);

  var debounceTimer = null;
  var lastText = '';

  observer = new MutationObserver(function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function() {
      var raw = extractText(platform);
      var clean = sanitizeText(raw);
      if (clean.length < MIN_TEXT_LENGTH) return;
      if (clean === lastText) return;
      lastText = clean;
      console.log('[MoodTunes] Change detected, sending update...');
      safeSendMessage({ source: platform, text: clean });
    }, DEBOUNCE_MS);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Initial scan after page loads
  setTimeout(function() {
    var raw = extractText(platform);
    var clean = sanitizeText(raw);
    if (clean.length >= MIN_TEXT_LENGTH) {
      safeSendMessage({ source: platform, text: clean });
    }
  }, 3000);

} else {
  console.log('[MoodTunes] Sensitive page, skipping');
}
