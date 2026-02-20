from flask import Flask, request
from flask_cors import CORS
from pypresence import Presence
import logging
import time
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv('DISCORD_CLIENT_ID') # Вставь свой ID приложения Discord

app = Flask(__name__)
CORS(app) 

RPC = None
current_song = None
current_state = None
last_update_time = 0

def connect_discord():
    """Безопасное подключение к Discord с исправлением ошибок цикла событий"""
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

def save_to_history(artist, title):
    timestamp = time.strftime("%d.%m.%Y %H:%M")
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {artist} - {title}\n")

@app.route('/', methods=['POST'])
def receive_data():
    global current_song, current_state, last_update_time, RPC
    data = request.json
    if not data: return "No data", 400

    now = time.time()
    song_id = f"{data['artist']} - {data['title']}"
    time_info = data.get('timeInfo', "[0:00 / 0:00]")

    if data['isPlaying']:
        if RPC is None:
            connect_discord()
            if RPC is None: return "Waiting for Discord", 200

        # Обновляем по таймеру 15с или при смене песни
        if song_id != current_song or current_state != 'playing' or (now - last_update_time) >= 15:
            try:
                if song_id != current_song:
                    save_to_history(data['artist'], data['title'])

                # Пытаемся обновить статус
                RPC.update(
                    state=f"👤 {data['artist']}",
                    details=f"🎧 {data['title']} {time_info}",
                    large_image=data.get('cover', "https://i.imgur.com/UqL0MFT.png"),
                    large_text=f"{data['artist']} - {data['title']}"
                )
                current_song = song_id
                current_state = 'playing'
                last_update_time = now
                print(f"🎵 {song_id} {time_info}")
            except Exception as e:
                print(f"🔄 Ошибка обновления: {e}")
                RPC = None
    else:
        if current_state != 'paused' and RPC:
            try:
                RPC.clear()
                print("⏸ Пауза")
            except: 
                RPC = None
            current_state = 'paused'
            current_song = None
            
    return "OK", 200

if __name__ == '__main__':
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("Cервер запущен!")
    app.run(port=8000)