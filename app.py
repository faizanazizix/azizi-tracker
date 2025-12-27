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

# --- JSON CLEANER ---
def smart_extract_json(text):
    try:
        # Koshish 1: Result array dhundo
        if '"result":' in text or "'result':" in text:
            # { se } tak ka sabse bada chunk dhundo
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
    except:
        pass
    return None

# --- BOT COMMUNICATOR ---
async def communicate_with_bot(target_bot, message_text):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            sent = await app_client.send_message(target_bot, message_text)
            
            best_response = None
            
            # 60 Seconds Wait
            for i in range(60): 
                # Check last 5 messages (Bot split message bhej sakta hai)
                async for message in app_client.get_chat_history(target_bot, limit=5):
                    if message.id > sent.id:
                        text = message.text or message.caption or ""
                        
                        if target_bot == "epicmoders":
                            # Ignore Wait messages
                            if "getting information" in text.lower() or "please wait" in text.lower():
                                continue
                            
                            # Agar "result" keyword mil gaya, matlab yahi asli maal hai -> RETURN
                            if '"result"' in text or "'result'" in text:
                                return text
                            
                            # Fallback: Agar result nahi mila par JSON jaisa hai, store karlo
                            if "{" in text and "}" in text:
                                best_response = text
                        else:
                            return text # Whosim direct return

                # Agar best response mil chuka hai aur 5 second beet gaye, to return kardo
                if best_response and i > 5:
                    return best_response
                
                await asyncio.sleep(1)
            
            return best_response
        except Exception as e:
            print(f"Bot Error: {e}")
            return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    try:
        data = request.json
        number = data.get('number')
        if not number: return jsonify({"error": "No number provided"})

        # 1. PRIMARY: EPICMODERS
        print(f"Trying Primary Bot (Epicmoders)...")
        response_text = asyncio.run(communicate_with_bot("epicmoders", number))
        
        if response_text:
            json_data = smart_extract_json(response_text)
            
            if json_data:
                return jsonify({"source": "epicmoders", "data": json_data})
            else:
                # Agar JSON fail hua, to raw text bhejo (backup display ke liye)
                return jsonify({"source": "epicmoders", "details": response_text})

        # 2. BACKUP: WHOSIM
        print(f"Primary Empty. Switching to Backup (Whosim)...")
        response_text_backup = asyncio.run(communicate_with_bot("whosim_bot", number))
        
        if response_text_backup:
            return jsonify({"source": "whosim", "details": response_text_backup})

        return jsonify({"error": "Data not found on both servers"})

    except Exception as e:
        return jsonify({"error": f"Internal Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
