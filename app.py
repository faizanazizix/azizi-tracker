from flask import Flask, render_template, request, jsonify
from pyrogram import Client, filters
import asyncio
import json
import re

app = Flask(__name__)

# --- 🛠️ SETUP YOUR TELEGRAM CONFIG HERE ---
API_ID = "YOUR_API_ID"        # my.telegram.org se milega
API_HASH = "YOUR_API_HASH"    # my.telegram.org se milega
SESSION_STRING = "YOUR_STRING_SESSION" # Pyrogram string session

# Initialize Client
app_client = Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# --- HELPER: Message Sender & Receiver ---
async def get_bot_response(chat_id, message_text, timeout=10):
    async with app_client:
        try:
            # Message bhejo
            sent = await app_client.send_message(chat_id, message_text)
            
            # Response ka wait karo
            response = None
            async for message in app_client.get_chat_history(chat_id, limit=1):
                # Check karo ki ye naya message hai (hamare bhejne ke baad ka)
                if message.id > sent.id:
                    response = message.text
                    break
            
            # Agar turant nahi aaya, thoda wait karke retry karo
            if not response:
                await asyncio.sleep(timeout)
                async for message in app_client.get_chat_history(chat_id, limit=1):
                    if message.id > sent.id:
                        response = message.text
                        break
            
            return response
        except Exception as e:
            print(f"Error fetching from {chat_id}: {e}")
            return None

@app.route('/')
def home():
    return render_template('index.html')

# --- 📱 MOBILE SEARCH ROUTE ---
@app.route('/get-info', methods=['POST'])
async def get_info():
    data = request.json
    number = data.get('number')

    if not number:
        return jsonify({"error": "No number provided"})

    # --- 1️⃣ PRIMARY: EPICMODERS ---
    print(f"Trying Primary Bot (Epicmoders) for {number}...")
    response_text = await get_bot_response("epicmoders", number)

    # Check agar valid JSON response aaya hai
    if response_text and "{" in response_text and "result" in response_text:
        # Epicmoders ka response Clean JSON string me convert karo
        # (Kabhi kabhi wo extra text bhejta hai, use hatana padega)
        try:
            # JSON start aur end dhundho
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            # Validate JSON
            json_data = json.loads(json_str)
            return jsonify({"source": "epicmoders", "data": json_data})
        except:
            pass # JSON fail hua to Backup pe jayenge

    # --- 2️⃣ BACKUP: WHOSIM (WHOSPY_BOT) ---
    print(f"Primary failed. Switching to Backup (Whosim) for {number}...")
    response_text_backup = await get_bot_response("whospy_bot", number)

    if response_text_backup:
        return jsonify({"source": "whosim", "details": response_text_backup})
    else:
        return jsonify({"error": "Data not found on both servers"})

# --- 🚗 VEHICLE SEARCH ROUTE ---
@app.route('/get-vehicle', methods=['POST'])
async def get_vehicle():
    data = request.json
    number = data.get('number') # e.g., JH05DY9094

    if not number:
        return jsonify({"error": "No vehicle number provided"})

    print(f"Searching Vehicle {number} on Epicmoders...")
    
    # Command format: /vehicle <number>
    command = f"/vehicle {number}"
    response_text = await get_bot_response("epicmoders", command)

    if response_text:
        return jsonify({"source": "epicmoders_vehicle", "details": response_text})
    else:
        return jsonify({"error": "Vehicle data not found"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
