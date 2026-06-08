// MoodTunes AI - Service Worker

var BACKEND_URL = 'http://localhost:8000';
var MIN_INTERVAL_MS = 30000;   // 30 seconds between recommendations
var lastRecommendationAt = 0;
var lastEmotion = '';
var snoozeUntil = 0;

var EMOTION_EMOJI = {
  happy: '\u{1F60A}', sad: '\u{1F622}', motivated: '\u{1F4AA}', excited: '\u{1F389}',
  confident: '\u{1F60E}', anxious: '\u{1F630}', focused: '\u{1F3AF}', burned_out: '\u{1F629}',
  romantic: '\u{1F495}', heartbroken: '\u{1F494}', relaxed: '\u{1F60C}', angry: '\u{1F624}',
  celebratory: '\u{1F38A}', productive: '\u26A1', workout: '\u{1F3CB}'
};

// Load saved state on startup
chrome.storage.local.get(['snoozeUntil', 'lastEmotion', 'lastRecommendationAt'], function(data) {
  snoozeUntil            = data.snoozeUntil || 0;
  lastEmotion            = data.lastEmotion || '';
  lastRecommendationAt   = data.lastRecommendationAt || 0;
});

// Message listener
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  if (message.type === 'CONTEXT_UPDATE') {
    handleContextUpdate(message.payload);
  }
  if (message.type === 'FEEDBACK') {
    handleFeedback(message.payload);
    sendResponse({ ok: true });
  }
  if (message.type === 'SNOOZE') {
    handleSnooze(message.payload.minutes);
    sendResponse({ ok: true });
  }
  if (message.type === 'GET_HISTORY') {
    chrome.storage.local.get('recommendations', function(data) {
      sendResponse(data.recommendations || []);
    });
    return true;
  }
});

// Notification button clicks
chrome.notifications.onButtonClicked.addListener(function(notifId, btnIdx) {
  chrome.storage.local.get('pendingNotif_' + notifId, function(data) {
    var rec = data['pendingNotif_' + notifId];
    if (!rec) return;
    if (btnIdx === 0) {
      chrome.tabs.create({ url: rec.youtube_url });
      sendFeedback(rec.song_id, 'play');
    } else if (btnIdx === 1) {
      sendFeedback(rec.song_id, 'like');
      chrome.notifications.clear(notifId);
    } else if (btnIdx === 2) {
      sendFeedback(rec.song_id, 'dislike');
      chrome.notifications.clear(notifId);
    }
  });
});

chrome.notifications.onClicked.addListener(function(notifId) {
  chrome.storage.local.get('pendingNotif_' + notifId, function(data) {
    var rec = data['pendingNotif_' + notifId];
    if (rec) chrome.tabs.create({ url: rec.youtube_url });
  });
});

chrome.alarms.onAlarm.addListener(function(alarm) {
  if (alarm.name === 'moodtunes-snooze-end') {
    snoozeUntil = 0;
    chrome.storage.local.set({ snoozeUntil: 0 });
  }
});

function handleContextUpdate(payload) {
  var now = Date.now();

  if (snoozeUntil && now < snoozeUntil) {
    console.log('[MoodTunes SW] Snoozed until ' + new Date(snoozeUntil).toLocaleTimeString());
    return;
  }

  var timeSinceLast = now - lastRecommendationAt;
  if (timeSinceLast < MIN_INTERVAL_MS) {
    var remaining = Math.ceil((MIN_INTERVAL_MS - timeSinceLast) / 1000);
    console.log('[MoodTunes SW] Rate limited. Next recommendation in ' + remaining + 's');
    return;
  }

  chrome.storage.local.get(['settings', 'userId'], function(data) {
    var settings = data.settings || {};
    if (settings.enabled === false) return;

    var userId = data.userId;
    if (!userId) {
      userId = 'user_' + Math.random().toString(36).slice(2, 18);
      chrome.storage.local.set({ userId: userId });
    }

    console.log('[MoodTunes SW] Calling backend for recommendation...');

    fetch(BACKEND_URL + '/api/v1/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        source: payload.source,
        text: payload.text
      })
    })
    .then(function(resp) {
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return resp.json();
    })
    .then(function(result) {
      var song    = result.recommendation && result.recommendation.song;
      var emotion = result.emotion_result && result.emotion_result.emotion;
      console.log('[MoodTunes SW] Got: ' + song + ' | Emotion: ' + emotion);

      // Update state
      lastRecommendationAt = Date.now();
      lastEmotion = emotion || '';
      chrome.storage.local.set({
        lastRecommendationAt: lastRecommendationAt,
        lastEmotion: lastEmotion
      });

      saveRecommendation(result);
      showNotification(result);
    })
    .catch(function(err) {
      console.error('[MoodTunes SW] Error: ' + err.message);
    });
  });
}

function showNotification(data) {
  var rec = data.recommendation;
  if (!rec) return;

  var emotion = (data.emotion_result && data.emotion_result.emotion) || 'relaxed';
  var emoji   = EMOTION_EMOJI[emotion] || '\uD83C\uDFB5';
  var notifId = 'moodtunes-' + Date.now();

  // Ensure direct YouTube URL
  var playUrl = rec.youtube_url || '';
  if (playUrl.indexOf('watch?v=') !== -1 && playUrl.indexOf('autoplay') === -1) {
    playUrl = playUrl + '&autoplay=1';
  }

  chrome.storage.local.set({
    ['pendingNotif_' + notifId]: {
      song_id:     rec.song_id,
      youtube_url: playUrl
    }
  });

  var reason = rec.reason || '';
  if (reason.length > 100) reason = reason.slice(0, 97) + '...';

  chrome.notifications.create(notifId, {
    type:           'basic',
    iconUrl:        chrome.runtime.getURL('icons/icon128.png'),
    title:          emoji + ' ' + rec.song + ' - ' + rec.artist,
    message:        'Detected: ' + capitalize(emotion),
    contextMessage: reason,
    buttons: [
      { title: '\u25B6 Play Now' },
      { title: '\uD83D\uDC4D Like' },
      { title: '\uD83D\uDC4E Dislike' }
    ],
    priority:       2,
    requireInteraction: false
  });

  setTimeout(function() { chrome.notifications.clear(notifId); }, 25000);
}

function handleFeedback(payload) {
  chrome.storage.local.get('userId', function(data) {
    var body = {
      user_id:  data.userId || 'unknown',
      song_id:  payload.song_id,
      action:   payload.action
    };
    fetch(BACKEND_URL + '/api/v1/feedback', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body)
    }).catch(function() {});
  });
}

function sendFeedback(songId, action) {
  chrome.storage.local.get('userId', function(data) {
    fetch(BACKEND_URL + '/api/v1/feedback', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        user_id:  data.userId || 'unknown',
        song_id:  songId,
        action:   action
      })
    }).catch(function() {});
  });
}

function handleSnooze(minutes) {
  snoozeUntil = Date.now() + minutes * 60000;
  chrome.storage.local.set({ snoozeUntil: snoozeUntil });
  chrome.alarms.create('moodtunes-snooze-end', { delayInMinutes: minutes });
}

function saveRecommendation(data) {
  chrome.storage.local.get('recommendations', function(stored) {
    var list = stored.recommendations || [];
    list.unshift({
      recommendation: data.recommendation,
      emotion_result: data.emotion_result,
      context_result: data.context_result,
      intent_result:  data.intent_result,
      timestamp:      Date.now()
    });
    if (list.length > 50) list.pop();
    chrome.storage.local.set({ recommendations: list });
  });
}

function capitalize(s) {
  if (!s) return '';
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ');
}
