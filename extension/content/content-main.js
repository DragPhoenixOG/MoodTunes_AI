// MoodTunes AI - Content Script
var DEBOUNCE_MS      = 3000;   // 3 seconds after last change
var MIN_TEXT_LENGTH  = 15;     // minimum chars to trigger
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
    if (t && t.length > 3) texts.push(t);
  }
  // Get last 10 messages for context
  return texts.slice(-10).join('\n').slice(0, MAX_CONTEXT_CHARS);
}

// Simple hash to detect new content
function simpleHash(str) {
  var hash = 0;
  for (var i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash;
  }
  return hash;
}

function safeSendMessage(payload) {
  try {
    chrome.runtime.sendMessage({ type: 'CONTEXT_UPDATE', payload: payload }, function(response) {
      if (chrome.runtime.lastError) {
        if (observer) observer.disconnect();
      }
    });
  } catch(e) {
    if (observer) observer.disconnect();
    console.log('[MoodTunes] Extension reloaded - refresh this page (F5)');
  }
}

var observer  = null;
var lastHash  = 0;
var lastCount = 0;

if (!isSensitivePage()) {
  var platform     = detectPlatform();
  var debounceTimer = null;

  console.log('[MoodTunes] Active on', platform);

  observer = new MutationObserver(function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function() {

      var raw      = extractText(platform);
      var clean    = sanitizeText(raw);
      var newHash  = simpleHash(clean);

      // Count current messages
      var sel = 'p, h1, h2, h3';
      if (platform === 'whatsapp') sel = '[data-pre-plain-text], .copyable-text';
      var count = document.querySelectorAll(sel).length;

      // Trigger if:
      // 1. Content hash changed (new messages or edits)
      // 2. AND text is long enough
      if (newHash !== lastHash && clean.length >= MIN_TEXT_LENGTH) {
        lastHash  = newHash;
        lastCount = count;
        console.log('[MoodTunes] New content detected (' + clean.length + ' chars), sending...');
        safeSendMessage({ source: platform, text: clean });
      }

    }, DEBOUNCE_MS);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Initial scan
  setTimeout(function() {
    var raw   = extractText(platform);
    var clean = sanitizeText(raw);
    if (clean.length >= MIN_TEXT_LENGTH) {
      lastHash = simpleHash(clean);
      safeSendMessage({ source: platform, text: clean });
    }
  }, 3000);

} else {
  console.log('[MoodTunes] Sensitive page, skipping');
}
