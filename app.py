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

# --- SMART COMMUNICATOR ---
async def communicate_with_bot(target_bot, message_text):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            sent = await app_client.send_message(target_bot, message_text)
            
            # 45 Seconds wait for Epicmoders (Slightly increased)
            for i in range(45): 
                async for message in app_client.get_chat_history(target_bot, limit=1):
                    if message.id > sent.id:
                        text = message.text or ""
                        # Ignore "Wait" messages strictly
                        if target_bot == "epicmoders":
                            if "getting information" in text.lower() or "please wait" in text.lower() or "join" in text.lower():
                                continue 
                        return text 
                await asyncio.sleep(1)
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

@app.route('/')
def home():
    return render_template('index.html')

# --- 📱 MOBILE SEARCH ONLY ---
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
        
        # JSON extract logic
        if response_text and "{" in response_text:
            try:
                # Find JSON part carefully
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                json_data = json.loads(json_str)
                
                # Agar result khali hai, tabhi backup pe jao
                if "result" in json_data and len(json_data["result"]) > 0:
                    return jsonify({"source": "epicmoders", "data": json_data})
            except:
                pass 
    except Exception as e:
        print(f"Primary Failed: {e}")

    # 2. BACKUP: WHOSIM (Only if Epicmoders fails/empty)
    print(f"Switching to Backup (Whosim)...")
    try:
        response_text_backup = asyncio.run(communicate_with_bot("whosim_bot", number))
        if response_text_backup:
            return jsonify({"source": "whosim", "details": response_text_backup})
    except:
        pass

    return jsonify({"error": "Data not found on both servers"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
