import os
import time
import urllib.parse
from flask import Flask, request
from flask_cors import CORS
from pypresence import Presence
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')

app = Flask(__name__)
CORS(app)

# Глобальные переменные
RPC = None
current_song = None
last_history_song = None  
last_update_time = 0
last_playing_state = False  # Отслеживаем паузу

def connect_discord():
    global RPC
    try:
        if RPC: RPC.close()
        RPC = Presence(CLIENT_ID)
        RPC.connect()
        print("✅ Discord подключен!")
        return True
    except: return False

def make_progress_bar(percent, is_playing):
    if percent is None: percent = 0
    if 0 < percent <= 1: percent *= 100
    p = max(0, min(100, percent))
    bar_size = 12 
    pos = int((p / 100) * bar_size)
    if pos >= bar_size: pos = bar_size - 1
    
    # Меняем значок в зависимости от того, играет ли музыка
    icon = "▶" if is_playing else "⏸"
    return f"{icon}{'─' * pos}⚪{'─' * (bar_size - pos - 1)}"

def format_discord_string(text, min_len=2, max_len=128):
    if not text: return "Неизвестно"
    text = text.replace('\n', ' ').replace('\r', '').strip()
    if len(text) < min_len: text = text + " " * (min_len - len(text))
    if len(text) > max_len: text = text[:max_len-3] + "..."
    return text

def save_to_history(artist, title):
    entry = f"{artist} - {title}"
    timestamp = time.strftime("%d.%m.%Y %H:%M")
    if os.path.exists("history.txt"):
        with open("history.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines and entry in lines[-1]: return 
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {entry}\n")

@app.route('/', methods=['POST'])
def receive_data():
    # ВОТ ОНА - СТРОЧКА СПАСЕНИЯ! Здесь мы строго объявляем все глобальные переменные
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
        is_state_changed = (is_playing != last_playing_state) # Теперь Python знает, откуда брать last_playing_state

        # Обновляем, если песня сменилась, ИЛИ мы нажали паузу, ИЛИ прошло 10 секунд
        if is_new_song or is_state_changed or (now - last_update_time) >= 10:
            
            if is_playing and song_id != last_history_song:
                save_to_history(artist_clean, title_clean)
                last_history_song = song_id

            if is_new_song and is_playing:
                display_progress = 0
                display_time = "0:00"
            else:
                display_progress = data.get('progress', 0)
                display_time = data.get('currentTime', '0:00')
            
            bar = make_progress_bar(display_progress, is_playing)
            
            search_query = f"{artist_clean} {title_clean}"
            safe_url = f"https://vk.com/audio?q={urllib.parse.quote(search_query)}"
            rpc_buttons = [{"label": "Слушать в ВК", "url": safe_url}]
            
            state_text = f"👤 {artist_clean}"
            if not is_playing:
                state_text += " (На паузе)"
            
            RPC.update(
                state=format_discord_string(state_text),
                details=format_discord_string(f"{bar} ({display_time})"),
                large_image=data.get('cover') or "https://i.imgur.com/UqL0MFT.png",
                large_text=f"Трек: {title_clean}",
                buttons=rpc_buttons
            )
            
            current_song = song_id
            last_update_time = now
            last_playing_state = is_playing # Обновляем состояние паузы
                
        return "OK", 200

    except Exception as e:
        print(f"❌ АВАРИЯ В PYTHON: {e}")
        return "Error", 500

if __name__ == '__main__':
    print(f"🚀 Сервер с умной паузой запущен! Жду данные...")
    app.run(port=8000)