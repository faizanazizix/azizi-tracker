from flask import Flask, render_template, request, jsonify
from pyrogram import Client
import asyncio
import json

# 👇 CHANGE: template_folder='.' added to fix "TemplateNotFound" error
app = Flask(__name__, template_folder='.')

# --- 🔐 TUMHARI CREDENTIALS (PRE-FILLED) ---
API_ID = 39183854
API_HASH = "7f8b6bfb1b72cab65e44c6cc450cd8f8"
SESSION_STRING = "BQJV5e4Alj1enIWcX8LODbh7r0COKClAAjmDFI-w1gV4QbLTPjdL1LsYgzX2Cwdw1D0PxDHlhl2wSpLW2vdJFFr_3_gWdzKqDep4pY2AZx4wwI7ooHkfNl_-SPuA1NQOw8p5VIhoR2m6-VET_QBvm37gU0UmoecNhsZLQDDsye2vrik9LvjtLdOagKN2aCsNXrRmfgeLwCi8EhOXY5IhOyH0N9vGCR66tu3XQ9Jb_HG71QQ6dxYSr9szlcjy32b096trb3yIrTr1R2i-uK7mmcwIqcROaLjHrtmNJyUMV3FawuPmHgV8T1YYbakUyY7bMtirZTYjqJ0lAbXF3LBjVMU_uKVqBAAAAAG0950mAA"

# Initialize Client
app_client = Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# --- HELPER FUNCTION ---
async def get_bot_response(chat_id, message_text, timeout=10):
    async with app_client:
        try:
            sent = await app_client.send_message(chat_id, message_text)
            response = None
            # Wait for response
            async for message in app_client.get_chat_history(chat_id, limit=1):
                if message.id > sent.id:
                    response = message.text
                    break
            
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

# --- 📱 MOBILE SEARCH (Primary: Epicmoders, Backup: Whosim) ---
@app.route('/get-info', methods=['POST'])
async def get_info():
    data = request.json
    number = data.get('number')

    if not number:
        return jsonify({"error": "No number provided"})

    # 1. Try Primary (Epicmoders)
    print(f"Trying Primary Bot (Epicmoders) for {number}...")
    try:
        response_text = await get_bot_response("epicmoders", number)
        # Check if valid JSON response
        if response_text and "{" in response_text and "result" in response_text:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            json_data = json.loads(json_str)
            return jsonify({"source": "epicmoders", "data": json_data})
    except:
        pass 

    # 2. Try Backup (Whosim)
    print(f"Primary failed. Switching to Backup (Whosim) for {number}...")
    try:
        response_text_backup = await get_bot_response("whospy_bot", number)
        if response_text_backup:
            return jsonify({"source": "whosim", "details": response_text_backup})
    except:
        pass

    return jsonify({"error": "Data not found on both servers"})

# --- 🚗 VEHICLE SEARCH (Epicmoders Only) ---
@app.route('/get-vehicle', methods=['POST'])
async def get_vehicle():
    data = request.json
    number = data.get('number') 

    if not number:
        return jsonify({"error": "No vehicle number provided"})

    print(f"Searching Vehicle {number} on Epicmoders...")
    command = f"/vehicle {number}"
    try:
        response_text = await get_bot_response("epicmoders", command)
        if response_text:
            return jsonify({"source": "epicmoders_vehicle", "details": response_text})
    except:
        pass
        
    return jsonify({"error": "Vehicle data not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
