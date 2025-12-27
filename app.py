from flask import Flask, render_template, request, jsonify
from pyrogram import Client
import asyncio
import json
import time

app = Flask(__name__, template_folder='.')

# --- 🔐 CREDENTIALS ---
API_ID = 39183854
API_HASH = "7f8b6bfb1b72cab65e44c6cc450cd8f8"
SESSION_STRING = "BQJV5e4Alj1enIWcX8LODbh7r0COKClAAjmDFI-w1gV4QbLTPjdL1LsYgzX2Cwdw1D0PxDHlhl2wSpLW2vdJFFr_3_gWdzKqDep4pY2AZx4wwI7ooHkfNl_-SPuA1NQOw8p5VIhoR2m6-VET_QBvm37gU0UmoecNhsZLQDDsye2vrik9LvjtLdOagKN2aCsNXrRmfgeLwCi8EhOXY5IhOyH0N9vGCR66tu3XQ9Jb_HG71QQ6dxYSr9szlcjy32b096trb3yIrTr1R2i-uK7mmcwIqcROaLjHrtmNJyUMV3FawuPmHgV8T1YYbakUyY7bMtirZTYjqJ0lAbXF3LBjVMU_uKVqBAAAAAG0950mAA"

# --- SMART BOT COMMUNICATOR ---
async def communicate_with_bot(target_bot, message_text):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            # 1. Message bhejo
            sent = await app_client.send_message(target_bot, message_text)
            print(f"Sent message to {target_bot}. Waiting for reply...")

            # 2. Response ka wait karo (Max 40 seconds)
            for i in range(40): 
                async for message in app_client.get_chat_history(target_bot, limit=1):
                    # Check karo ki ye naya message hai
                    if message.id > sent.id:
                        text = message.text or ""
                        
                        # --- 🛑 EPICMODERS SPECIFIC LOGIC (WAIT INGORE) ---
                        if target_bot == "epicmoders":
                            if "getting information" in text.lower() or "please wait" in text.lower():
                                print("Bot said wait... waiting for real data.")
                                continue 
                            
                            # Agar "Join Channel" ya promotion message hai
                            if "join" in text.lower() and len(text) < 100:
                                continue

                        # Agar Data aa gaya, to return karo!
                        return text
                
                # Har 1 second me check karo
                await asyncio.sleep(1)
            
            return None # Timeout ho gaya
        except Exception as e:
            print(f"ERROR connecting to {target_bot}: {e}")
            return None

@app.route('/')
def home():
    return render_template('index.html')

# --- 📱 MOBILE SEARCH ---
@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    number = data.get('number')

    if not number:
        return jsonify({"error": "No number provided"})

    # 1. PRIMARY: EPICMODERS
    print(f"Attempting Primary Bot (Epicmoders) for {number}...")
    try:
        response_text = asyncio.run(communicate_with_bot("epicmoders", number))
        
        # Check agar sahi response aaya (JSON hona chahiye)
        if response_text and "{" in response_text and "result" in response_text:
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                json_data = json.loads(json_str)
                return jsonify({"source": "epicmoders", "data": json_data})
            except:
                print("JSON Parsing Failed on Primary")
    except Exception as e:
        print(f"Primary Bot Failed: {e}")

    # 2. BACKUP: WHOSIM_BOT (CORRECTED HERE)
    print(f"⚠️ Primary failed/slow. Switching to Backup (Whosim Bot)...")
    try:
        # 👇 YAHAN CHANGE KIYA HAI: 'whosim_bot' 👇
        response_text_backup = asyncio.run(communicate_with_bot("whosim_bot", number))
        
        if response_text_backup:
            return jsonify({"source": "whosim", "details": response_text_backup})
    except Exception as e:
        print(f"Backup Bot Failed: {e}")

    return jsonify({"error": "Data not found on both servers"})

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
        return jsonify({"error": f"Error: {e}"})
        
    return jsonify({"error": "Vehicle data not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
