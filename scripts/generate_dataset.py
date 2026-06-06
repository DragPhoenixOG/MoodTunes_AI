#!/usr/bin/env python3
"""
MoodTunes AI – Song Dataset Generator (Groq edition)
Generates 5,000+ songs and ingests them into local ChromaDB.

Usage:
    cd backend
    python ../scripts/generate_dataset.py
"""

import asyncio, json, sys
from pathlib import Path
from urllib.parse import quote_plus

# ── Curated seed songs (diverse genres, moods, languages) ───────────────────
SONGS_RAW = [
    # Motivational / Rock
    {"title":"Hall Of Fame","artist":"The Script ft. will.i.am","genre":"Pop/Rock",
     "energy_level":"high","mood_tags":["motivational","confident","empowering"],
     "context_tags":["career","interview","startup"],
     "lyrics_summary":"Anyone can become legendary through dedication and hard work."},
    {"title":"Eye of the Tiger","artist":"Survivor","genre":"Rock",
     "energy_level":"high","mood_tags":["workout","energetic","powerful"],
     "context_tags":["gym","workout","competition"],
     "lyrics_summary":"Rising to the challenge, fighting to stay alive."},
    {"title":"Lose Yourself","artist":"Eminem","genre":"Hip-Hop",
     "energy_level":"high","mood_tags":["motivational","focused","intense"],
     "context_tags":["career","interview","startup","study"],
     "lyrics_summary":"One shot, one opportunity — seize the moment."},
    {"title":"Believer","artist":"Imagine Dragons","genre":"Rock",
     "energy_level":"high","mood_tags":["motivational","resilient","empowering"],
     "context_tags":["career","gym","workout"],
     "lyrics_summary":"Pain made me a believer, turning suffering into strength."},
    {"title":"Stronger","artist":"Kanye West","genre":"Hip-Hop",
     "energy_level":"high","mood_tags":["confident","motivational","workout"],
     "context_tags":["gym","workout","career"],
     "lyrics_summary":"What doesn't kill you makes you stronger, better, faster."},
    {"title":"Till I Collapse","artist":"Eminem","genre":"Hip-Hop",
     "energy_level":"high","mood_tags":["workout","energetic","powerful"],
     "context_tags":["gym","workout"],
     "lyrics_summary":"Giving everything until physically unable to go on."},
    {"title":"Thunder","artist":"Imagine Dragons","genre":"Rock",
     "energy_level":"high","mood_tags":["motivated","confident","triumphant"],
     "context_tags":["career","startup"],
     "lyrics_summary":"Rising from obscurity to claim your destiny."},
    {"title":"Can't Hold Us","artist":"Macklemore & Ryan Lewis","genre":"Hip-Hop",
     "energy_level":"high","mood_tags":["celebratory","energetic","triumphant"],
     "context_tags":["celebration","career"],
     "lyrics_summary":"Nothing can stop the momentum of success."},
    {"title":"POWER","artist":"Kanye West","genre":"Hip-Hop",
     "energy_level":"high","mood_tags":["powerful","confident","intense"],
     "context_tags":["career","startup","gym"],
     "lyrics_summary":"Confronting power, influence, and the weight of greatness."},
    {"title":"Run the World (Girls)","artist":"Beyoncé","genre":"Pop",
     "energy_level":"high","mood_tags":["confident","celebratory","empowering"],
     "context_tags":["career","celebration"],
     "lyrics_summary":"Women's power, strength and dominance celebrated."},
    # Sad / Emotional
    {"title":"Someone Like You","artist":"Adele","genre":"Pop",
     "energy_level":"low","mood_tags":["sad","heartbroken","emotional"],
     "context_tags":["breakup","relationship"],
     "lyrics_summary":"Letting go of a lost love while wishing them happiness."},
    {"title":"Fix You","artist":"Coldplay","genre":"Rock",
     "energy_level":"low","mood_tags":["comforting","sad","healing"],
     "context_tags":["stress","breakup","career"],
     "lyrics_summary":"When you feel lost and broken, you will be guided through."},
    {"title":"The Night We Met","artist":"Lord Huron","genre":"Indie",
     "energy_level":"low","mood_tags":["sad","nostalgic","heartbroken"],
     "context_tags":["breakup","relationship"],
     "lyrics_summary":"Longing to go back to before everything went wrong."},
    {"title":"Skinny Love","artist":"Bon Iver","genre":"Indie Folk",
     "energy_level":"low","mood_tags":["sad","melancholic","vulnerable"],
     "context_tags":["breakup","relationship"],
     "lyrics_summary":"A fragile love breaking under its own weight."},
    {"title":"Let Her Go","artist":"Passenger","genre":"Folk Pop",
     "energy_level":"low","mood_tags":["sad","nostalgic","reflective"],
     "context_tags":["breakup","relationship"],
     "lyrics_summary":"You only know what you have once you've lost it."},
    # Study / Focus
    {"title":"Experience","artist":"Ludovico Einaudi","genre":"Classical/Ambient",
     "energy_level":"low","mood_tags":["focus","calm","concentration"],
     "context_tags":["study","coding","learning"],
     "lyrics_summary":"Minimal piano piece evoking deep contemplation."},
    {"title":"Weightless","artist":"Marconi Union","genre":"Ambient",
     "energy_level":"low","mood_tags":["calming","focus","relaxing"],
     "context_tags":["study","coding","stress"],
     "lyrics_summary":"Scientifically designed to reduce anxiety."},
    {"title":"Brain Food","artist":"Glass Animals","genre":"Indie/Electronic",
     "energy_level":"medium","mood_tags":["focus","dreamy","concentration"],
     "context_tags":["study","coding"],
     "lyrics_summary":"Hazy dreamlike soundscape for creative focus."},
    {"title":"Strobe","artist":"deadmau5","genre":"Progressive House",
     "energy_level":"medium","mood_tags":["focus","productive","flow"],
     "context_tags":["coding","study"],
     "lyrics_summary":"Long-form electronic journey for deep work."},
    {"title":"Genesis","artist":"Justice","genre":"Electronic",
     "energy_level":"high","mood_tags":["powerful","focused","energetic"],
     "context_tags":["coding","startup"],
     "lyrics_summary":"Heavy distorted synth that commands attention."},
    # Happy / Celebratory
    {"title":"Happy","artist":"Pharrell Williams","genre":"Pop/Soul",
     "energy_level":"high","mood_tags":["happy","cheerful","uplifting"],
     "context_tags":["celebration","travel","general"],
     "lyrics_summary":"Pure unapologetic happiness and joy."},
    {"title":"Good as Hell","artist":"Lizzo","genre":"Pop/R&B",
     "energy_level":"high","mood_tags":["happy","confident","empowering"],
     "context_tags":["celebration","career","breakup"],
     "lyrics_summary":"Self-love anthem for feeling unstoppable."},
    {"title":"Blinding Lights","artist":"The Weeknd","genre":"Synth-Pop",
     "energy_level":"high","mood_tags":["excited","energetic","romantic"],
     "context_tags":["relationship","travel","celebration"],
     "lyrics_summary":"Neon-lit rush of longing and desire."},
    {"title":"Dancing Queen","artist":"ABBA","genre":"Pop",
     "energy_level":"high","mood_tags":["happy","celebratory","carefree"],
     "context_tags":["celebration","general"],
     "lyrics_summary":"Eternal dance floor anthem of youthful freedom."},
    {"title":"Levitating","artist":"Dua Lipa","genre":"Pop/Disco",
     "energy_level":"high","mood_tags":["happy","excited","romantic"],
     "context_tags":["celebration","relationship"],
     "lyrics_summary":"Floating on love and euphoria."},
    # Relaxation
    {"title":"Sunset Lover","artist":"Petit Biscuit","genre":"Electronic",
     "energy_level":"low","mood_tags":["relaxed","chill","dreamy"],
     "context_tags":["travel","general"],
     "lyrics_summary":"Golden hour feelings in electronic form."},
    {"title":"Coffee","artist":"beabadoobee","genre":"Indie Pop",
     "energy_level":"low","mood_tags":["relaxed","chill","nostalgic"],
     "context_tags":["general","study"],
     "lyrics_summary":"Lazy morning vibes and simple pleasures."},
    {"title":"Retrograde","artist":"James Blake","genre":"Electronic Soul",
     "energy_level":"low","mood_tags":["melancholic","reflective","chill"],
     "context_tags":["stress","general"],
     "lyrics_summary":"Haunting electronic soul for introspection."},
    # Workout
    {"title":"Titanium","artist":"David Guetta ft. Sia","genre":"Electronic Pop",
     "energy_level":"high","mood_tags":["powerful","resilient","workout"],
     "context_tags":["gym","workout","career"],
     "lyrics_summary":"Bulletproof and unbreakable against all adversity."},
    {"title":"Turn Down for What","artist":"DJ Snake & Lil Jon","genre":"Electronic",
     "energy_level":"high","mood_tags":["energetic","workout","party"],
     "context_tags":["gym","workout","celebration"],
     "lyrics_summary":"Maximum energy party anthem."},
    {"title":"Pump It","artist":"Black Eyed Peas","genre":"Hip-Hop/Dance",
     "energy_level":"high","mood_tags":["workout","energetic","pump"],
     "context_tags":["gym","workout"],
     "lyrics_summary":"Pumping up the crowd with relentless energy."},
    # Romantic
    {"title":"All of Me","artist":"John Legend","genre":"R&B/Soul",
     "energy_level":"low","mood_tags":["romantic","love","emotional"],
     "context_tags":["relationship"],
     "lyrics_summary":"Loving someone completely, flaws and all."},
    {"title":"Perfect","artist":"Ed Sheeran","genre":"Pop",
     "energy_level":"low","mood_tags":["romantic","love","sweet"],
     "context_tags":["relationship","celebration"],
     "lyrics_summary":"Finding the perfect person and dancing in the dark."},
    {"title":"Can't Help Falling in Love","artist":"Elvis Presley","genre":"Pop",
     "energy_level":"low","mood_tags":["romantic","classic","sweet"],
     "context_tags":["relationship"],
     "lyrics_summary":"Helplessly, inevitably falling in love."},
    # Heartbreak
    {"title":"drivers license","artist":"Olivia Rodrigo","genre":"Pop",
     "energy_level":"low","mood_tags":["heartbroken","sad","emotional"],
     "context_tags":["breakup","relationship"],
     "lyrics_summary":"Driving past the places that remind you of them."},
    {"title":"happier","artist":"Olivia Rodrigo","genre":"Pop",
     "energy_level":"low","mood_tags":["heartbroken","sad","bittersweet"],
     "context_tags":["breakup","relationship"],
     "lyrics_summary":"Wanting your ex to be happy even though it hurts."},
    # Gaming
    {"title":"Megalovania","artist":"Toby Fox","genre":"Video Game",
     "energy_level":"high","mood_tags":["intense","epic","focused"],
     "context_tags":["gaming"],
     "lyrics_summary":"Undertale's iconic battle theme of determination."},
    {"title":"One-Winged Angel","artist":"Nobuo Uematsu","genre":"Orchestral",
     "energy_level":"high","mood_tags":["epic","intense","dramatic"],
     "context_tags":["gaming"],
     "lyrics_summary":"Final Fantasy VII final boss theme."},
    # Travel
    {"title":"Don't Stop Me Now","artist":"Queen","genre":"Rock",
     "energy_level":"high","mood_tags":["happy","energetic","carefree"],
     "context_tags":["travel","celebration"],
     "lyrics_summary":"Having a good time and nothing can stop it."},
    {"title":"Life is a Highway","artist":"Tom Cochrane","genre":"Rock",
     "energy_level":"high","mood_tags":["adventurous","free","happy"],
     "context_tags":["travel"],
     "lyrics_summary":"Life's journey is a long open road."},
    # Bollywood / Hindi
    {"title":"Jai Ho","artist":"A.R. Rahman","genre":"Bollywood",
     "energy_level":"high","mood_tags":["celebratory","motivational","triumphant"],
     "context_tags":["celebration","career"],
     "lyrics_summary":"Victory anthem from Slumdog Millionaire."},
    {"title":"Tum Hi Ho","artist":"Arijit Singh","genre":"Bollywood",
     "energy_level":"low","mood_tags":["romantic","emotional","love"],
     "context_tags":["relationship"],
     "lyrics_summary":"You are my everything — iconic Bollywood love ballad."},
    {"title":"Kabira","artist":"Arijit Singh","genre":"Bollywood",
     "energy_level":"low","mood_tags":["romantic","melancholic","soulful"],
     "context_tags":["relationship","breakup"],
     "lyrics_summary":"Soulful longing for a lost love."},
    {"title":"Chaiyya Chaiyya","artist":"A.R. Rahman","genre":"Bollywood",
     "energy_level":"high","mood_tags":["happy","celebratory","romantic"],
     "context_tags":["celebration","travel"],
     "lyrics_summary":"Joyful Bollywood classic about dancing on a train."},
    # K-Pop
    {"title":"Dynamite","artist":"BTS","genre":"K-Pop",
     "energy_level":"high","mood_tags":["happy","energetic","celebratory"],
     "context_tags":["celebration","general"],
     "lyrics_summary":"Pure joy and positive energy."},
    {"title":"How You Like That","artist":"BLACKPINK","genre":"K-Pop",
     "energy_level":"high","mood_tags":["confident","powerful","comeback"],
     "context_tags":["career","gym"],
     "lyrics_summary":"Rising from rock bottom in style."},
    # Latin
    {"title":"Despacito","artist":"Luis Fonsi ft. Daddy Yankee","genre":"Reggaeton",
     "energy_level":"medium","mood_tags":["romantic","sensual","happy"],
     "context_tags":["relationship","celebration"],
     "lyrics_summary":"Slow, sensual summer romance."},
    {"title":"Waka Waka","artist":"Shakira","genre":"Pop/African",
     "energy_level":"high","mood_tags":["celebratory","energetic","happy"],
     "context_tags":["celebration","gym"],
     "lyrics_summary":"Celebratory World Cup anthem."},
    # Anxiety relief
    {"title":"Breathe (2 AM)","artist":"Anna Nalick","genre":"Folk Pop",
     "energy_level":"low","mood_tags":["calming","comforting","anxious"],
     "context_tags":["stress","study","career"],
     "lyrics_summary":"Just breathe — life is overwhelming but manageable."},
    {"title":"Fade Into You","artist":"Mazzy Star","genre":"Dream Pop",
     "energy_level":"low","mood_tags":["calming","dreamy","soothing"],
     "context_tags":["stress","general"],
     "lyrics_summary":"Ethereal hazy soundscape for de-stressing."},
]

# ── Bulk generator ─────────────────────────────────────────────────────────────
GENRE_SETS = [
    ("Jazz",       ["mellow","sophisticated","chill"],         ["study","general"]),
    ("Blues",      ["soulful","melancholic","raw"],            ["stress","general"]),
    ("R&B",        ["sensual","smooth","romantic"],            ["relationship","celebration"]),
    ("Metal",      ["aggressive","intense","powerful"],        ["gym","workout","gaming"]),
    ("Country",    ["nostalgic","warm","storytelling"],        ["general","travel"]),
    ("Afrobeats",  ["happy","dance","energetic"],              ["celebration","general"]),
    ("Reggae",     ["relaxed","positive","chill"],             ["travel","general"]),
    ("Electronic", ["focused","hypnotic","energetic"],         ["coding","gym"]),
    ("Gospel",     ["uplifting","inspiring","spiritual"],      ["career","celebration"]),
    ("Folk",       ["nostalgic","peaceful","storytelling"],    ["study","general"]),
    ("Pop Punk",   ["angry","energetic","rebellious"],         ["gym","general"]),
    ("Classical",  ["focused","calm","sophisticated"],         ["study","learning"]),
    ("Trap",       ["confident","intense","dark"],             ["gym","gaming"]),
    ("Indie Folk", ["melancholic","intimate","nostalgic"],     ["breakup","general"]),
    ("House",      ["dance","euphoric","energetic"],           ["gym","celebration"]),
    ("Lo-Fi",      ["chill","relaxed","focus"],                ["study","coding"]),
    ("Ambient",    ["peaceful","spacious","focus"],            ["study","stress"]),
    ("Disco",      ["happy","dance","nostalgic"],              ["celebration","general"]),
    ("Punk Rock",  ["angry","energetic","rebellious"],         ["gym","general"]),
    ("Soul",       ["warm","emotional","soulful"],             ["relationship","general"]),
]

MOODS_POOL    = ["happy","sad","motivated","excited","confident","anxious","focused",
                 "burned_out","romantic","heartbroken","relaxed","angry","celebratory",
                 "productive","workout"]
CONTEXTS_POOL = ["interview","coding","study","gym","workout","startup","career",
                 "relationship","breakup","gaming","travel","celebration","business",
                 "learning","stress"]
ENERGY_LEVELS = ["low","medium","high"]


def generate_bulk(count_per_genre: int = 250) -> list[dict]:
    import random
    random.seed(42)
    songs = []
    for genre, moods, contexts in GENRE_SETS:
        for i in range(count_per_genre):
            extra_moods    = random.sample(MOODS_POOL, min(2, len(MOODS_POOL)))
            extra_contexts = random.sample(CONTEXTS_POOL, 1)
            songs.append({
                "title": f"{genre} Vibes {i+1:03d}",
                "artist": f"Artist {random.randint(1, 300)}",
                "genre": genre,
                "energy_level": random.choice(ENERGY_LEVELS),
                "mood_tags": list(dict.fromkeys(moods[:2] + extra_moods))[:4],
                "context_tags": list(dict.fromkeys(contexts + extra_contexts))[:3],
                "lyrics_summary": f"A {genre.lower()} track perfect for {random.choice(contexts)} vibes.",
            })
    return songs


async def main():
    import httpx, os

    all_songs = SONGS_RAW + generate_bulk()
    final = []
    for i, s in enumerate(all_songs):
        yt = f"https://www.youtube.com/results?search_query={quote_plus(s['title']+' '+s['artist'])}"
        final.append({"song_id": f"song_{i:05d}", "youtube_url": yt, "playlist_url": None, **s})

    # Save JSON
    Path("./data").mkdir(exist_ok=True)
    with open("./data/songs_dataset.json", "w") as f:
        json.dump(final, f, indent=2)
    print(f"✅ Generated {len(final)} songs → data/songs_dataset.json")

    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    batch_size = 50
    ingested = 0
    print(f"Ingesting into backend at {backend_url}...")
    async with httpx.AsyncClient(timeout=180.0) as client:
        for i in range(0, len(final), batch_size):
            batch = final[i:i+batch_size]
            try:
                resp = await client.post(f"{backend_url}/api/v1/songs/ingest", json=batch)
                resp.raise_for_status()
                ingested += len(batch)
                print(f"  {ingested}/{len(final)} ingested...")
            except Exception as e:
                print(f"  Batch {i} failed: {e}")
    print(f"✅ Done! {ingested} songs in ChromaDB.")


if __name__ == "__main__":
    asyncio.run(main())
