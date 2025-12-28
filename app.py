from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient
from telethon.sessions import StringSession
from flask_cors import CORS
import asyncio
import re

# --- DETAILS ---
api_id = 39183854
api_hash = '7f8b6bfb1b72cab65e44c6cc450cd8f8'
bot_username = '@whosim_bot'

# Tumhari Generated String (Maine yaha laga di hai)
session_string = '1BVtsOMQBuyNf34N8jj1kcjrHqHem9QC84Y-E3XG3yKPDTw7IcRqB2z8Wu5wc7uKDhLu9VB3QEfWEq7fdvKbK9OEeXav1okTF9lBUoifjF5xgs3pnTJf_DWKn_6lN8Awe-vXAU61brJdhlflxS7fjuAsf-XeMsi_9VC_-2sO43EjDtkklq1R3Il-MDthTTnOs5WyOnsAs3Fc-ddsutS6vd_z7Xxv_WRmke9SbcczQVGTL2N6sC35w6bsc8y_8sO-ActGQp57k8w3OB51HjScQN9P8NWkEclaJ976Y0gySocyTw7A9mDe2sad_w96AZWoemwb9nwL1-lFh_b-183IvIbo-WoCoVSw='

app = Flask(__name__, template_folder='.')
CORS(app)

# Async Loop Setup
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(StringSession(session_string), api_id, api_hash, loop=loop)

def clean_and_format_text(text):
    if not text: return ""
    
    # 1. Naam badalna
    text = text.replace("MAXX", "FAIZAN AZIZI")
    
    # 2. "ID" ya "id" ko "Aadhaar Number" karna
    text = re.sub(r'\bID\b', 'Aadhaar Number', text, flags=re.IGNORECASE)
    text = re.sub(r'\bid\b', 'Aadhaar Number', text, flags=re.IGNORECASE)
    
    return text

async def ask_telegram_final(mobile_number):
    try:
        # Check connection
        if not client.is_connected():
            await client.connect()
        
        # Message send karo
        await client.send_message(bot_username, mobile_number)
        
        # Response ka wait karo (Max 30 seconds)
        for i in range(30):
            await asyncio.sleep(1) 
            history = await client.get_messages(bot_username, limit=1)
            
            if history:
                msg = history[0]
                content = msg.message or msg.caption or ""
                
                if not msg.out: # Agar message Bot ki taraf se aaya hai
                    # Check conditions
                    if "Results" in content or "Name" in content or "Mobile" in content:
                        return clean_and_format_text(content)
                    
                    if len(content) > 15 and "Search" not in content and "Wait" not in content:
                        return clean_and_format_text(content)

        return "Timeout: Data not found or Bot is slow."
    except Exception as e:
        return f"System Error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    mobile_number = data.get('number')
    if not mobile_number: return jsonify({'error': 'No Number'}), 400

    try:
        # Client loop me run karo
        result = client.loop.run_until_complete(ask_telegram_final(mobile_number))
        return jsonify({'details': result})
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Server...")
    client.start()

    app.run(debug=True, port=5000)
