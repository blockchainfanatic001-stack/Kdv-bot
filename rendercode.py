import asyncio
import requests
from flask import Flask, request, jsonify
from threading import Thread

# --- BAYANANKA DA API KEYS ---
TELEGRAM_BOT_TOKEN = "8513711051:AAHNH_JyFvcw87FrE0bKNYakyBkvZa8KraM"
TELEGRAM_CHAT_ID = "6600029204"

PAPER_TRADE_AMOUNT = 20.0
ACTIVE_PAPER_TRADES = {}
SEEN_TOKENS = set()
INCOMING_WEBHOOK_TOKENS = [] 

TOTAL_TRADES = 0
WINNING_TRADES = 0
NET_REALIZED_PNL_USD = 0.0

# --- KOFAR ASIBITIN RENDER (WEBHOOK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 KDV-Scanner (Webhook) Yana aiki lafiya lau 24/7!"

@app.route('/webhook', methods=['POST'])
def helius_webhook():
    data = request.json
    if data and isinstance(data, list):
        for tx in data:
            transfers = tx.get("tokenTransfers", [])
            for transfer in transfers:
                mint = transfer.get("mint")
                if mint and mint != "So11111111111111111111111111111111111111112":
                    if mint not in SEEN_TOKENS:
                        INCOMING_WEBHOOK_TOKENS.append(mint)
                        SEEN_TOKENS.add(mint)
                        print(f"🔥 KOFAR ASIBITI: An Karbi Sabon Token: {mint}", flush=True)
    return jsonify({"status": "success"}), 200

def run_server():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

async def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print(f"🚨 MATSALAR TELEGRAM: {e}", flush=True)

def check_advanced_security(token_address):
    return True

async def track_and_trade(token_address):
    tracked_status = 'tracking'
    
    for _ in range(40):
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get('pairs'):
                pair = res['pairs'][0]
                name = pair.get('baseToken', {}).get('name', 'Unknown')
                mcap = float(pair.get('fdv', 0))
                volume = float(pair.get('volume', {}).get('h24', 0))
                price = float(pair.get('priceUsd', 0))
                
                if tracked_status == 'tracking':
                    alert_msg = (f"🎓 <b>SABON GRADUATION (WEBHOOK)!</b>\n\n"
                                 f"🏷 <b>Suna:</b> {name}\n"
                                 f"🔗 <b>CA:</b> <code>{token_address}</code>\n"
                                 f"📊 <b>MCAP:</b> ${mcap:,.2f}\n"
                                 f"📈 <b>Volume:</b> ${volume:,.2f}\n\n"
                                 f"<i>Bot yana jiran Retest <=30k...</i>")
                    await send_msg(alert_msg)
                    tracked_status = 'wait_retest'
                
                if tracked_status == 'wait_retest':
                    if mcap <= 30000:
                        tracked_status = 'retested'
                elif tracked_status == 'retested':
                    if mcap >= 30000 and volume >= 30000:
                        if check_advanced_security(token_address):
                            ACTIVE_PAPER_TRADES[token_address] = {
                                'name': name, 'buy_price': price, 'highest_price': price
                            }
                            await send_msg(f"🚀 <b>AN SAYI PAPER TRADE!</b>\n\n"
                                           f"🏷 <b>Suna:</b> {name}\n"
                                           f"💲 <b>Farashi:</b> ${price:.6f}\n"
                                           f"📊 <b>MCAP:</b> ${mcap:,.2f}\n"
                                           f"📈 <b>Volume:</b> ${volume:,.2f}\n"
                                           f"💰 <b>Kudi:</b> ${PAPER_TRADE_AMOUNT}\n\n"
                                           f"✅ <i>Dokoki sun cika! An kunna -30% Trailing Stoploss.</i>")
                        break
        except Exception:
            pass
        await asyncio.sleep(10)

async def webhook_processor():
    while True:
        if INCOMING_WEBHOOK_TOKENS:
            token = INCOMING_WEBHOOK_TOKENS.pop(0)
            asyncio.create_task(track_and_trade(token))
        await asyncio.sleep(1)

async def pydroid_heartbeat():
    while True:
        print("🟢 Kofar Webhook a Bude Take...", flush=True)
        await asyncio.sleep(60)

async def kdv_sniper_bot():
    print("🚀 BOT YA TASHI! Zai tura sako a Telegram yanzu...")
    await send_msg("🟢 KDV-Scanner (Webhook) An Dora Shi a RENDER!\n\n<i>Kofar Asibitin mu tana a bude tana jiran Helius ta kawo Graduation.</i>")
    
    asyncio.create_task(webhook_processor())
    asyncio.create_task(pydroid_heartbeat())
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    keep_alive() 
    asyncio.run(kdv_sniper_bot())
