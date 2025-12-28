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
        if '"result":' in text or "'result':" in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
    except:
        pass
    return None

# --- BOT COMMUNICATOR ---
async def communicate_with_bot(target_bot, message_text, mode):
    async with Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING) as app_client:
        try:
            sent = await app_client.send_message(target_bot, message_text)
            best_response = None
            wait_time = 60 if mode == "server2" else 30 
            
            for i in range(wait_time): 
                async for message in app_client.get_chat_history(target_bot, limit=5):
                    if message.id > sent.id:
                        text = message.text or message.caption or ""
                        
                        # SERVER 2 (EPICMODERS) - NO TOUCH
                        if mode == "server2":
                            if "getting information" in text.lower() or "please wait" in text.lower(): continue
                            if '"result"' in text or "'result'" in text: return text
                            if "{" in text and "}" in text: best_response = text
                        
                        # SERVER 1 (WHOSIM)
                        else:
                            # Whosim text me result bhejta hai, use turant pakad lo
                            if len(text) > 20 and "search" not in text.lower(): 
                                return text 

                if best_response and i > 5: return best_response
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
        server_mode = data.get('server') 
        
        if not number: return jsonify({"error": "No number provided"})

        target_bot = "whosim_bot" if server_mode == "server1" else "epicmoders"
        
        response_text = asyncio.run(communicate_with_bot(target_bot, number, server_mode))
        
        if response_text:
            if server_mode == "server2":
                json_data = smart_extract_json(response_text)
                if json_data:
                    return jsonify({"source": "epicmoders", "data": json_data})
                else:
                    return jsonify({"source": "epicmoders", "details": response_text})
            else:
                # Server 1 text return karega
                return jsonify({"source": "whosim", "details": response_text})

        return jsonify({"error": "Data not found"})

    except Exception as e:
        return jsonify({"error": f"Internal Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
