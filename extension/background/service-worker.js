// MoodTunes AI - Service Worker

var BACKEND_URL = 'http://localhost:8000';
var MIN_INTERVAL_MS = 60000;
var lastRecommendationAt = 0;
var snoozeUntil = 0;

var EMOTION_EMOJI = {
  happy: '😊', sad: '😢', motivated: '💪', excited: '🎉',
  confident: '😎', anxious: '😰', focused: '🎯', burned_out: '😩',
  romantic: '💕', heartbroken: '💔', relaxed: '😌', angry: '😤',
  celebratory: '🎊', productive: '⚡', workout: '🏋️'
};

// Load snooze on startup
chrome.storage.local.get('snoozeUntil', function(data) {
  snoozeUntil = data.snoozeUntil || 0;
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
  if (now - lastRecommendationAt < MIN_INTERVAL_MS) {
    console.log('[MoodTunes SW] Rate limited, skipping');
    return;
  }
  if (snoozeUntil && now < snoozeUntil) {
    console.log('[MoodTunes SW] Snoozed');
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
      console.log('[MoodTunes SW] Got:', result.recommendation && result.recommendation.song);
      lastRecommendationAt = Date.now();
      saveRecommendation(result);
      showNotification(result);
    })
    .catch(function(err) {
      console.error('[MoodTunes SW] Error:', err.message);
    });
  });
}

function showNotification(data) {
  var rec = data.recommendation;
  if (!rec) return;
  var emotion = (data.emotion_result && data.emotion_result.emotion) || 'relaxed';
  var emoji = EMOTION_EMOJI[emotion] || '🎵';
  var notifId = 'moodtunes-' + Date.now();

  chrome.storage.local.set({
    ['pendingNotif_' + notifId]: {
      song_id: rec.song_id,
      youtube_url: rec.youtube_url
    }
  });

  chrome.notifications.create(notifId, {
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icons/icon128.png'),
    title: emoji + ' MoodTunes — ' + capitalize(emotion),
    message: rec.song + ' by ' + rec.artist,
    contextMessage: rec.reason,
    buttons: [
      { title: '▶ Play Song' },
      { title: '👍 Like' },
      { title: '👎 Dislike' }
    ],
    priority: 2
  });

  setTimeout(function() { chrome.notifications.clear(notifId); }, 20000);
}

function handleFeedback(payload) {
  chrome.storage.local.get('userId', function(data) {
    var body = JSON.parse(JSON.stringify(payload));
    body.user_id = data.userId || 'unknown';
    fetch(BACKEND_URL + '/api/v1/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).catch(function() {});
  });
}

function sendFeedback(songId, action) {
  chrome.storage.local.get('userId', function(data) {
    fetch(BACKEND_URL + '/api/v1/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: data.userId || 'unknown',
        song_id: songId,
        action: action
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
    var item = {
      recommendation: data.recommendation,
      emotion_result: data.emotion_result,
      context_result: data.context_result,
      intent_result: data.intent_result,
      timestamp: Date.now()
    };
    list.unshift(item);
    if (list.length > 50) list.pop();
    chrome.storage.local.set({ recommendations: list });
  });
}

function capitalize(s) {
  if (!s) return '';
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ');
}
