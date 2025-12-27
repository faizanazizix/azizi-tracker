from flask import Flask, render_template, request, jsonify
from pyrogram import Client
import asyncio
import json
import os

# "template_folder='.'" ka matlab hai HTML file bahar hi dhundo
app = Flask(__name__, template_folder='.')

# --- 🔐 CREDENTIALS ---
API_ID = 39183854
API_HASH = "7f8b6bfb1b72cab65e44c6cc450cd8f8"
SESSION_STRING = "BQJV5e4Alj1enIWcX8LODbh7r0COKClAAjmDFI-w1gV4QbLTPjdL1LsYgzX2Cwdw1D0PxDHlhl2wSpLW2vdJFFr_3_gWdzKqDep4pY2AZx4wwI7ooHkfNl_-SPuA1NQOw8p5VIhoR2m6-VET_QBvm37gU0UmoecNhsZLQDDsye2vrik9LvjtLdOagKN2aCsNXrRmfgeLwCi8EhOXY5IhOyH0N9vGCR66tu3XQ9Jb_HG71QQ6dxYSr9szlcjy32b096trb3yIrTr1R2i-uK7mmcwIqcROaLjHrtmNJyUMV3FawuPmHgV8T1YYbakUyY7bMtirZTYjqJ0lAbXF3LBjVMU_uKVqBAAAAAG0950mAA"

# --- HELPER FUNCTION (ASYNC) ---
# Ye function background me bot se baat karega
async def communicate_with_bot(chat_id, message_text):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            # Message bhejo
            sent = await app_client.send_message(chat_id, message_text)
            
            # Response ka wait karo (Max 15 seconds)
            response = None
            for _ in range(15): # Retry loop
                async for message in app_client.get_chat_history(chat_id, limit=1):
                    if message.id > sent.id:
                        return message.text
                await asyncio.sleep(1) # 1 second wait karo
            
            return None # Agar timeout ho gaya
        except Exception as e:
            print(f"ERROR: {e}")
            return str(e)

@app.route('/')
def home():
    return render_template('index.html')

# --- 📱 MOBILE SEARCH ---
@app.route('/get-info', methods=['POST'])
def get_info(): # Note: Ye 'async' nahi hai, ye normal function hai
    data = request.json
    number = data.get('number')

    if not number:
        return jsonify({"error": "No number provided"})

    # 1. Try Primary (Epicmoders)
    print(f"Searching {number} on Epicmoders...")
    try:
        # ASYNC FUNCTION KO YAHAN RUN KARO
        response_text = asyncio.run(communicate_with_bot("epicmoders", number))
        
        # JSON parsing logic
        if response_text and "{" in response_text and "result" in response_text:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            json_data = json.loads(json_str)
            return jsonify({"source": "epicmoders", "data": json_data})
    except Exception as e:
        print(f"Primary Bot Error: {e}")

    # 2. Try Backup (Whosim)
    print(f"Switching to Backup (Whosim) for {number}...")
    try:
        response_text_backup = asyncio.run(communicate_with_bot("whospy_bot", number))
        if response_text_backup:
            return jsonify({"source": "whosim", "details": response_text_backup})
    except Exception as e:
        print(f"Backup Bot Error: {e}")

    return jsonify({"error": "Data not found or Bot Error"})

# --- 🚗 VEHICLE SEARCH ---
@app.route('/get-vehicle', methods=['POST'])
def get_vehicle():
    data = request.json
    number = data.get('number') 

    if not number:
        return jsonify({"error": "No vehicle number provided"})

    print(f"Searching Vehicle {number} on Epicmoders...")
    command = f"/vehicle {number}"
    
    try:
        response_text = asyncio.run(communicate_with_bot("epicmoders", command))
        if response_text:
            return jsonify({"source": "epicmoders_vehicle", "details": response_text})
    except Exception as e:
        print(f"Vehicle Bot Error: {e}")
        return jsonify({"error": f"Error: {e}"})
        
    return jsonify({"error": "Vehicle data not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
