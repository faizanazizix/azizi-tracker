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

# --- HELPER: JSON EXTRACTOR ---
def extract_clean_json(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
    except:
        pass
    return None

# --- COMMUNICATOR ---
async def communicate_with_bot(target_bot, message_text):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            sent = await app_client.send_message(target_bot, message_text)
            
            # Best Message dhoondne ke liye variables
            best_message = None
            max_length = 0
            
            # 60 Seconds Wait
            for i in range(60): 
                # Last 5 messages check karo (Kyunki bot tukdo me bhej sakta hai)
                async for message in app_client.get_chat_history(target_bot, limit=5):
                    if message.id > sent.id:
                        # Caption handle karo (kabhi kabhi photo ke sath text aata hai)
                        text = message.text or message.caption or ""
                        
                        if target_bot == "epicmoders":
                            # Ignore Wait/Join messages
                            if "getting information" in text.lower() or "please wait" in text.lower() or "join" in text.lower():
                                continue
                            
                            # Agar isme "result" ya "data" keyword hai, to ye pakka apna maal hai
                            if "result" in text.lower() or "mobile" in text.lower():
                                return text
                            
                            # Agar keyword nahi mila, to jo sabse lamba message hoga, use store kar lo
                            if len(text) > max_length:
                                max_length = len(text)
                                best_message = text
                        else:
                            return text # Whosim direct return

                # Agar abhi tak "result" wala message nahi mila, to thoda aur wait karo
                if best_message and max_length > 100:
                    # Agar 100 character se bada message mil gaya hai, to use return kardo (Time save)
                    return best_message
                
                await asyncio.sleep(1)
            
            return best_message # Timeout hone par jo best mila wo dedo
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
            json_data = extract_clean_json(response_text)
            
            if json_data and "result" in json_data:
                return jsonify({"source": "epicmoders", "data": json_data})
            else:
                # Agar JSON fail hua, to RAW TEXT bhejo (Full message)
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
