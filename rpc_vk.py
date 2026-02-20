from flask import Flask, request
from flask_cors import CORS
from pypresence import Presence
import logging
import time
import urllib.parse
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')

app = Flask(__name__)
CORS(app) 

RPC = None
current_song = None
last_update_time = 0
last_playing_state = False
last_history_song = None

def connect_discord():
    global RPC
    try:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        if RPC:
            try: RPC.close()
            except: pass
        RPC = Presence(CLIENT_ID)
        RPC.connect()
        print("✅ Discord успешно подключен!")
        return True
    except Exception as e:
        print(f"📡 Discord пока не виден... ({e})")
        RPC = None
        return False
    
def format_discord_string(text, min_len=2, max_len=128):
    if not text: return "  "
    text = text.replace('\n', ' ').replace('\r', '').strip()
    if len(text) < min_len: text = text + " " * (min_len - len(text))
    if len(text) > max_len: text = text[:max_len-3] + "..."
    return text

def make_progress_bar(percent, is_playing):
    if 0 < percent <= 1: percent *= 100
    bar_size = 12 
    p = max(0, min(100, percent))
    pos = int((p / 100) * bar_size)
    if pos >= bar_size: pos = bar_size - 1
    
    # ТВОЙ ВАРИАНТ: Инвертированные значки
    icon = "⏸" if is_playing else "▶"
    return f"{icon}{'─' * pos}⚪{'─' * (bar_size - pos - 1)}"

def save_to_history(artist, title):
    timestamp = time.strftime("%d.%m.%Y %H:%M")
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {artist} - {title}\n")

@app.route('/', methods=['POST'])
def receive_data():
    global current_song, last_update_time, RPC, last_playing_state, last_history_song
    try:
        data = request.json
        if not data: return "No data", 400
        
        now = time.time()
        artist_clean = format_discord_string(data.get('artist', 'Неизвестно'))
        title_clean = format_discord_string(data.get('title', 'Неизвестно'))
        song_id = f"{artist_clean} - {title_clean}"
        is_playing = data.get('isPlaying', False)

        if RPC is None: connect_discord()
        if RPC is None: return "Wait", 200
        
        is_new_song = (song_id != current_song)
        is_state_changed = (is_playing != last_playing_state)
        
        # Обновляем всегда, даже если на паузе
        if is_new_song or is_state_changed or (now - last_update_time) >= 10:
            if is_new_song:
                if is_playing and song_id != last_history_song:
                    save_to_history(artist_clean, title_clean)
                    last_history_song = song_id
                display_progress = 0
                display_time = "0:00"
            else:
                display_progress = data.get('progress', 0)
                display_time = data.get('currentTime', '0:00')
            
            bar = make_progress_bar(display_progress, is_playing)
            search_query = f"{artist_clean} {title_clean}"
            safe_url = f"https://vk.com/audio?q={urllib.parse.quote(search_query)}"

            rpc_buttons = [
                {"label": "Слушать в ВК", "url": safe_url},
                {"label": "Код на GitHub", "url": "https://github.com/Damirland/discord_bot"}
            ]
            
            song_details = f"🎶 {title_clean}"
            small_txt = "В эфире"
            if not is_playing:
                song_details += " (На паузе)"
                small_txt = "Остановлено"
            
            RPC.update(
                state=format_discord_string(f"{bar} ({display_time})"),
                details=format_discord_string(song_details),
                large_image=data.get('cover') or "https://i.imgur.com/UqL0MFT.png",
                large_text=song_id,
                small_image="https://i.imgur.com/vSpjnjG.png",
                small_text=small_txt,
                buttons=rpc_buttons
            )
            current_song = song_id
            last_update_time = now
            last_playing_state = is_playing
                
        return "OK", 200
    except Exception as e:
        print(f"❌ АВАРИЯ В PYTHON: {e}")
        return "Error", 500

if __name__ == '__main__':
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(port=8000)