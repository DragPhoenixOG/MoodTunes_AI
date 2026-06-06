// MoodTunes AI – Notification Manager

const NOTIFICATION_PREFIX = 'moodtunes-';
const pendingNotifications = new Map(); // notifId → recommendation data

export const NotificationManager = {
  show(data) {
    const { recommendation, emotion_result, context_result } = data;
    const { song, artist, reason, youtube_url, playlist_url } = recommendation;

    const notifId = `${NOTIFICATION_PREFIX}${Date.now()}`;
    const emotionLabel = emotion_result?.emotion || 'unknown';
    const emoji = EMOTION_EMOJI[emotionLabel] || '🎵';

    const options = {
      type: 'basic',
      iconUrl: '../icons/icon128.png',
      title: `${emoji} MoodTunes AI`,
      message: `${song} – ${artist}\n${reason}`,
      contextMessage: `Detected: ${capitalize(emotionLabel)}`,
      buttons: [
        { title: '▶ Play Song' },
        { title: '📋 Playlist' },
        { title: '👍 Like' },
        { title: '👎 Dislike' },
      ],
      priority: 2,
      requireInteraction: false,
    };

    pendingNotifications.set(notifId, { ...data, youtube_url, playlist_url });
    chrome.notifications.create(notifId, options);

    // Auto-dismiss after 15 seconds
    setTimeout(() => chrome.notifications.clear(notifId), 15_000);
  },

  handleButtonClick(notifId, btnIdx) {
    const data = pendingNotifications.get(notifId);
    if (!data) return;

    const { youtube_url, playlist_url, recommendation } = data;

    switch (btnIdx) {
      case 0: // Play
        chrome.tabs.create({ url: youtube_url });
        this._sendFeedback(recommendation.song_id, 'play');
        break;
      case 1: // Playlist
        chrome.tabs.create({ url: playlist_url || youtube_url });
        this._sendFeedback(recommendation.song_id, 'playlist');
        break;
      case 2: // Like
        this._sendFeedback(recommendation.song_id, 'like');
        chrome.notifications.clear(notifId);
        break;
      case 3: // Dislike
        this._sendFeedback(recommendation.song_id, 'dislike');
        chrome.notifications.clear(notifId);
        break;
    }
  },

  handleClick(notifId) {
    const data = pendingNotifications.get(notifId);
    if (data?.youtube_url) {
      chrome.tabs.create({ url: data.youtube_url });
      this._sendFeedback(data.recommendation?.song_id, 'play');
    }
  },

  _sendFeedback(songId, action) {
    if (!songId) return;
    chrome.runtime.sendMessage({
      type: 'FEEDBACK',
      payload: { song_id: songId, action, timestamp: Date.now() },
    });
  },
};

const EMOTION_EMOJI = {
  happy: '😊', sad: '😢', motivated: '💪', excited: '🎉',
  confident: '😎', anxious: '😰', focused: '🎯', burned_out: '😩',
  romantic: '💕', heartbroken: '💔', relaxed: '😌', angry: '😤',
  celebratory: '🎊', productive: '⚡', workout: '🏋️',
};

function capitalize(s) {
  return s ? s[0].toUpperCase() + s.slice(1).replace(/_/g, ' ') : '';
}
