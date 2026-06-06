// MoodTunes AI – Popup

import { StorageService } from '../storage/storage-service.js';

const SNOOZE_OPTIONS = [
  { label: '30 min', minutes: 30 },
  { label: '1 hour', minutes: 60 },
  { label: 'Today',  minutes: minutesUntilMidnight() },
  { label: 'Tomorrow', minutes: minutesUntilMidnight() + 1440 },
];

async function render() {
  const settings = await StorageService.getSettings();
  const history = await getHistory();
  const snoozeUntil = await StorageService.getSnoozeUntil();
  const snoozed = snoozeUntil && Date.now() < snoozeUntil;

  const root = document.getElementById('root');
  root.innerHTML = `
    <div class="popup">
      <header>
        <span class="logo">🎵 MoodTunes AI</span>
        <label class="toggle">
          <input type="checkbox" id="enable-toggle" ${settings.enabled ? 'checked' : ''}>
          <span class="slider"></span>
        </label>
      </header>

      <div class="snooze-bar ${snoozed ? 'active' : ''}">
        ${snoozed
          ? `<span>Snoozed until ${new Date(snoozeUntil).toLocaleTimeString()}</span>
             <button id="clear-snooze">Resume</button>`
          : `<span>Snooze:</span>
             ${SNOOZE_OPTIONS.map(o =>
               `<button class="snooze-btn" data-minutes="${o.minutes}">${o.label}</button>`
             ).join('')}`
        }
      </div>

      <section class="history">
        <h2>Recent Recommendations</h2>
        ${history.length === 0
          ? '<p class="empty">No recommendations yet. Start a conversation!</p>'
          : history.slice(0, 10).map(item => renderHistoryItem(item)).join('')
        }
      </section>

      <footer>
        <a href="../options/settings.html" target="_blank">⚙ Settings</a>
        <span class="version">v1.0.0</span>
      </footer>
    </div>
  `;

  // Wire events
  document.getElementById('enable-toggle')?.addEventListener('change', async (e) => {
    await StorageService.saveSettings({ ...settings, enabled: e.target.checked });
  });

  document.getElementById('clear-snooze')?.addEventListener('click', async () => {
    await StorageService.clearSnooze();
    render();
  });

  document.querySelectorAll('.snooze-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const minutes = parseInt(btn.dataset.minutes);
      chrome.runtime.sendMessage({ type: 'SNOOZE', payload: { minutes } });
      render();
    });
  });

  document.querySelectorAll('.play-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chrome.tabs.create({ url: btn.dataset.url });
    });
  });
}

function renderHistoryItem(item) {
  const { recommendation, emotion_result, timestamp } = item;
  if (!recommendation) return '';
  const { song, artist, reason, youtube_url } = recommendation;
  const emotion = emotion_result?.emotion || '';
  const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return `
    <div class="rec-card">
      <div class="rec-meta">
        <span class="emotion-tag">${EMOTION_EMOJI[emotion] || '🎵'} ${emotion}</span>
        <span class="time">${time}</span>
      </div>
      <div class="rec-title">${song}</div>
      <div class="rec-artist">${artist}</div>
      <div class="rec-reason">${reason}</div>
      <button class="play-btn" data-url="${youtube_url}">▶ Play</button>
    </div>
  `;
}

function getHistory() {
  return new Promise(resolve => {
    chrome.runtime.sendMessage({ type: 'GET_HISTORY' }, (resp) => {
      resolve(resp || []);
    });
  });
}

function minutesUntilMidnight() {
  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(24, 0, 0, 0);
  return Math.round((midnight - now) / 60000);
}

const EMOTION_EMOJI = {
  happy:'😊', sad:'😢', motivated:'💪', excited:'🎉',
  confident:'😎', anxious:'😰', focused:'🎯', burned_out:'😩',
  romantic:'💕', heartbroken:'💔', relaxed:'😌', angry:'😤',
  celebratory:'🎊', productive:'⚡', workout:'🏋️',
};

render();
