// MoodTunes AI – Background Service Worker (MV3)

import { StorageService } from '../storage/storage-service.js';
import { NotificationManager } from '../notifications/notification-manager.js';

const BACKEND_URL = 'http://localhost:8000';
const MIN_INTERVAL_MS = 60_000; // 1 minute between recommendations

let lastRecommendationAt = 0;

// --- Message router ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
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
    StorageService.getRecentRecommendations().then(sendResponse);
    return true;
  }
});

// --- Notification click handler ---
chrome.notifications.onButtonClicked.addListener((notifId, btnIdx) => {
  NotificationManager.handleButtonClick(notifId, btnIdx);
});

chrome.notifications.onClicked.addListener((notifId) => {
  NotificationManager.handleClick(notifId);
});

// --- Alarm for snooze ---
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'moodtunes-snooze-end') {
    StorageService.clearSnooze();
  }
});

async function handleContextUpdate(payload) {
  const now = Date.now();
  // Rate limit
  if (now - lastRecommendationAt < MIN_INTERVAL_MS) return;

  // Check snooze
  const snoozeUntil = await StorageService.getSnoozeUntil();
  if (snoozeUntil && now < snoozeUntil) return;

  // Check enabled
  const settings = await StorageService.getSettings();
  if (!settings.enabled) return;

  try {
    const userId = await StorageService.getUserId();
    const response = await fetch(`${BACKEND_URL}/api/v1/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload, user_id: userId }),
    });

    if (!response.ok) return;
    const data = await response.json();

    if (!data.recommendation) return;

    lastRecommendationAt = now;
    await StorageService.addRecommendation(data);
    NotificationManager.show(data);
  } catch (err) {
    console.warn('[MoodTunes] Backend unavailable:', err.message);
  }
}

async function handleFeedback(payload) {
  const userId = await StorageService.getUserId();
  await fetch(`${BACKEND_URL}/api/v1/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, user_id: userId }),
  }).catch(() => {});
  await StorageService.recordFeedback(payload);
}

function handleSnooze(minutes) {
  const until = Date.now() + minutes * 60_000;
  StorageService.setSnooze(until);
  chrome.alarms.create('moodtunes-snooze-end', { delayInMinutes: minutes });
}
