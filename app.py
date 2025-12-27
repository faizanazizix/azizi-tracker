from flask import Flask, render_template, request, jsonify
from pyrogram import Client
import asyncio
import json
import re

app = Flask(__name__, template_folder='.')

# --- 🔐 CREDENTIALS ---
API_ID = 39183854
API_HASH = "7f8b6bfb1b72cab65e44c6cc450cd8f8"
SESSION_STRING = "BQJV5e4Alj1enIWcX8LODbh7r0COKClAAjmDFI-w1gV4QbLTPjdL1LsYgzX2Cwdw1D0PxDHlhl2wSpLW2vdJFFr_3_gWdzKqDep4pY2AZx4wwI7ooHkfNl_-SPuA1NQOw8p5VIhoR2m6-VET_QBvm37gU0UmoecNhsZLQDDsye2vrik9LvjtLdOagKN2aCsNXrRmfgeLwCi8EhOXY5IhOyH0N9vGCR66tu3XQ9Jb_HG71QQ6dxYSr9szlcjy32b096trb3yIrTr1R2i-uK7mmcwIqcROaLjHrtmNJyUMV3FawuPmHgV8T1YYbakUyY7bMtirZTYjqJ0lAbXF3LBjVMU_uKVqBAAAAAG0950mAA"

# --- SMART BOT COMMUNICATOR ---
async def communicate_with_bot(target_bot, message_text):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            sent = await app_client.send_message(target_bot, message_text)
            
            # Wait loop (Max 40s)
            for i in range(40): 
                async for message in app_client.get_chat_history(target_bot, limit=1):
                    if message.id > sent.id:
                        text = message.text or ""
                        
                        # --- SKIP WAITING MESSAGES (EPICMODERS) ---
                        if target_bot == "epicmoders":
                            if "getting information" in text.lower() or "please wait" in text.lower() or "join" in text.lower():
                                continue 

                        return text # Asli data mil gaya
                await asyncio.sleep(1)
            return None
        except Exception as e:
            print(f"Error: {e}")
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
    print(f"Trying Primary Bot (Epicmoders)...")
    try:
        response_text = asyncio.run(communicate_with_bot("epicmoders", number))
        
        # Agar response aaya aur wo valid hai (Wait message nahi hai)
        if response_text and "{" in response_text:
            # JSON Clean karne ki koshish
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                json_data = json.loads(json_str)
                # SUCCESS: Return immediately! Do not call backup.
                return jsonify({"source": "epicmoders", "data": json_data})
            except:
                pass
    except Exception as e:
        print(f"Primary Failed: {e}")

    # 2. BACKUP: WHOSIM (Sirf tab chalega jab Primary fail ho)
    print(f"Switching to Backup (Whosim)...")
    try:
        response_text_backup = asyncio.run(communicate_with_bot("whosim_bot", number))
        if response_text_backup:
            return jsonify({"source": "whosim", "details": response_text_backup})
    except:
        pass

    return jsonify({"error": "Data not found on both servers"})

# --- 🚗 VEHICLE SEARCH ---
@app.route('/get-vehicle', methods=['POST'])
def get_vehicle():
    data = request.json
    number = data.get('number') 
    if not number: return jsonify({"error": "No vehicle number provided"})

    command = f"/vehicle {number}"
    try:
        response_text = asyncio.run(communicate_with_bot("epicmoders", command))
        if response_text:
            # JSON extract
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                json_data = json.loads(json_str)
                return jsonify({"source": "epicmoders_vehicle", "data": json_data})
            except:
                return jsonify({"source": "epicmoders_vehicle", "details": response_text})
    except Exception as e:
        return jsonify({"error": f"Error: {e}"})
        
    return jsonify({"error": "Vehicle data not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
