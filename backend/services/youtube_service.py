# MoodTunes AI – YouTube URL Builder (no API key required)
from urllib.parse import urlencode, quote_plus

YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query="
YOUTUBE_PLAYLIST_QUERIES: dict[str, str] = {
    "happy":       "happy feel good music playlist",
    "sad":         "sad emotional songs playlist",
    "motivated":   "motivational songs playlist",
    "excited":     "exciting upbeat music playlist",
    "confident":   "confidence boost songs playlist",
    "anxious":     "calming anxiety relief music",
    "focused":     "study focus music playlist",
    "burned_out":  "chill lofi beats burnout recovery",
    "romantic":    "romantic love songs playlist",
    "heartbroken": "heartbreak songs playlist",
    "relaxed":     "chill relaxing music playlist",
    "angry":       "intense powerful music playlist",
    "celebratory": "celebration party songs playlist",
    "productive":  "productivity focus music playlist",
    "workout":     "workout gym motivation playlist",
}

CONTEXT_PLAYLIST_QUERIES: dict[str, str] = {
    "interview":    "interview preparation confidence music",
    "coding":       "coding music programmer playlist",
    "study":        "study music concentration playlist",
    "gym":          "gym workout energy music",
    "workout":      "workout motivation music playlist",
    "startup":      "startup hustle motivation music",
    "career":       "career motivation songs",
    "relationship": "love songs romantic playlist",
    "breakup":      "breakup healing music playlist",
    "gaming":       "gaming music epic playlist",
    "travel":       "travel adventure music playlist",
    "celebration":  "celebration party songs",
}


class YouTubeService:
    @staticmethod
    def build_url(song_title: str, artist: str) -> str:
        """Direct song search URL."""
        query = f"{song_title} {artist} official"
        return YOUTUBE_SEARCH + quote_plus(query)

    @staticmethod
    def build_playlist_url(emotion: str, context: str) -> str:
        """Mood/context playlist search URL."""
        query = (
            CONTEXT_PLAYLIST_QUERIES.get(context)
            or YOUTUBE_PLAYLIST_QUERIES.get(emotion)
            or f"{emotion} music playlist"
        )
        return YOUTUBE_SEARCH + quote_plus(query)

    # Future: inject real YouTubeAPIService here without changing callers
