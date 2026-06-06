// MoodTunes AI – Storage Service

const KEYS = {
  USER_ID: 'userId',
  SETTINGS: 'settings',
  SNOOZE_UNTIL: 'snoozeUntil',
  RECOMMENDATIONS: 'recommendations',
  FEEDBACK: 'feedback',
  MEMORY: 'userMemory',
};

export const StorageService = {
  async getUserId() {
    const data = await chrome.storage.local.get(KEYS.USER_ID);
    if (data[KEYS.USER_ID]) return data[KEYS.USER_ID];
    const id = 'user_' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
    await chrome.storage.local.set({ [KEYS.USER_ID]: id });
    return id;
  },

  async getSettings() {
    const defaults = {
      enabled: true,
      cloudMode: false,
      backendUrl: 'http://localhost:8000',
      minInterval: 60,
      notificationsEnabled: true,
    };
    const data = await chrome.storage.local.get(KEYS.SETTINGS);
    return { ...defaults, ...(data[KEYS.SETTINGS] || {}) };
  },

  async saveSettings(settings) {
    await chrome.storage.local.set({ [KEYS.SETTINGS]: settings });
  },

  async getSnoozeUntil() {
    const data = await chrome.storage.local.get(KEYS.SNOOZE_UNTIL);
    return data[KEYS.SNOOZE_UNTIL] || null;
  },

  async setSnooze(timestamp) {
    await chrome.storage.local.set({ [KEYS.SNOOZE_UNTIL]: timestamp });
  },

  async clearSnooze() {
    await chrome.storage.local.remove(KEYS.SNOOZE_UNTIL);
  },

  async addRecommendation(rec) {
    const data = await chrome.storage.local.get(KEYS.RECOMMENDATIONS);
    const list = data[KEYS.RECOMMENDATIONS] || [];
    list.unshift({ ...rec, timestamp: Date.now() });
    if (list.length > 50) list.pop();
    await chrome.storage.local.set({ [KEYS.RECOMMENDATIONS]: list });
  },

  async getRecentRecommendations(limit = 20) {
    const data = await chrome.storage.local.get(KEYS.RECOMMENDATIONS);
    return (data[KEYS.RECOMMENDATIONS] || []).slice(0, limit);
  },

  async recordFeedback(payload) {
    const data = await chrome.storage.local.get(KEYS.FEEDBACK);
    const list = data[KEYS.FEEDBACK] || [];
    list.unshift({ ...payload, timestamp: Date.now() });
    if (list.length > 200) list.pop();
    await chrome.storage.local.set({ [KEYS.FEEDBACK]: list });
  },

  async getUserMemory() {
    const data = await chrome.storage.local.get(KEYS.MEMORY);
    return data[KEYS.MEMORY] || {
      liked_songs: [],
      disliked_songs: [],
      favorite_artists: [],
      favorite_genres: [],
      recent_recommendations: [],
    };
  },

  async updateUserMemory(updates) {
    const current = await this.getUserMemory();
    await chrome.storage.local.set({ [KEYS.MEMORY]: { ...current, ...updates } });
  },
};
