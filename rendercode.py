import asyncio
import websockets
import json
import requests
from telegram import Bot
from flask import Flask
from threading import Thread

# --- BAYANANKA DA API KEYS ---
TELEGRAM_BOT_TOKEN = "8807988612:AAFkIjWN0vNd2ut-ig4crPeOY1COiEsbbOI"
TELEGRAM_CHAT_ID = "8513300977"
HELIUS_API_KEY = "8391babc-9cc0-43f7-9c08-2bcbdfd63694"

bot = Bot(token=TELEGRAM_BOT_TOKEN)

PAPER_TRADE_AMOUNT = 20.0 
ACTIVE_PAPER_TRADES = {} 
SEEN_SIGS = set()
SEEN_TOKENS = set()

# --- LISSAFIN WIN RATE DA P&L ---
TOTAL_TRADES = 0
WINNING_TRADES = 0
NET_REALIZED_PNL_USD = 0.0

# =====================================================================
# Dabarar Yaudarar Render (Fake Website domin aiki 24/7)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 KDV-Scanner (BlockchainFanatic 001) Yana aiki lafiya lau 24/7!"

def run_server():
    # Render tana amfani da port 10000 a kyauta
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# =====================================================================

async def send_msg(text):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode='HTML')
    except Exception:
        pass

def check_advanced_security(token_address):
    return True

async def send_hourly_report():
    while True:
        await asyncio.sleep(3600) 
        if not ACTIVE_PAPER_TRADES:
            continue
        msg = "⏱️ <b>RAHOTON AWA GUDA NA TOKENS (HOURLY)</b>\n\n"
        for token, data in ACTIVE_PAPER_TRADES.items():
            try:
                res = requests.get(f"[https://api.dexscreener.com/latest/dex/tokens/](https://api.dexscreener.com/latest/dex/tokens/){token}").json()
                current_price = float(res['pairs'][0]['priceUsd'])
                buy_price = data['buy_price']
                current_pnl = ((current_price - buy_price) / buy_price) * 100
                pnl_usd = PAPER_TRADE_AMOUNT * (current_pnl / 100)
                sign = "+" if current_pnl >= 0 else ""
                msg += f"🔸 <b>{data['name']}:</b> {sign}{current_pnl:.2f}% ({sign}${pnl_usd:.2f})\n"
            except:
                msg += f"🔸 <b>{data['name']}:</b> <i>Ana lissafi...</i>\n"
        await send_msg(msg)

async def send_daily_report():
    global TOTAL_TRADES, WINNING_TRADES, NET_REALIZED_PNL_USD
    while True:
        await asyncio.sleep(86400) 
        if TOTAL_TRADES > 0:
            winrate = (WINNING_TRADES / TOTAL_TRADES) * 100
            pnl_sign = "+" if NET_REALIZED_PNL_USD >= 0 else ""
            emoji = "💰" if NET_REALIZED_PNL_USD >= 0 else "💸"
            msg = (f"🗓️ <b>RAHOTON AWA 24 (DAILY MASTER REPORT)</b>\n\n"
                   f"<b>Kudin Trade:</b> ${PAPER_TRADE_AMOUNT}\n"
                   f"<b>Jimillar Ciniki:</b> {TOTAL_TRADES}\n"
                   f"<b>Nasarar Wins:</b> {WINNING_TRADES} ✅\n"
                   f"<b>Faduwar Losses:</b> {TOTAL_TRADES - WINNING_TRADES} 🛑\n\n"
                   f"🏆 <b>WIN RATE: {winrate:.2f}%</b>\n"
                   f"{emoji} <b>NET REALIZED PNL: {pnl_sign}${NET_REALIZED_PNL_USD:.2f}</b>")
            await send_msg(msg)
            TOTAL_TRADES = 0
            WINNING_TRADES = 0
            NET_REALIZED_PNL_USD = 0.0

async def monitor_active_trades():
    global TOTAL_TRADES, WINNING_TRADES, NET_REALIZED_PNL_USD
    while True:
        for token_address, trade_data in list(ACTIVE_PAPER_TRADES.items()):
            url = f"[https://api.dexscreener.com/latest/dex/tokens/](https://api.dexscreener.com/latest/dex/tokens/){token_address}"
            try:
                res = requests.get(url).json()
                if res.get('pairs'):
                    current_price = float(res['pairs'][0]['priceUsd'])
                    buy_price = trade_data['buy_price']
                    if current_price > trade_data['highest_price']:
                        trade_data['highest_price'] = current_price
                    drawdown_from_peak = ((current_price - trade_data['highest_price']) / trade_data['highest_price']) * 100
                    if drawdown_from_peak <= -30.0:
                        actual_pnl_percent = ((current_price - buy_price) / buy_price) * 100
                        trade_pnl_usd = PAPER_TRADE_AMOUNT * (actual_pnl_percent / 100)
                        TOTAL_TRADES += 1
                        NET_REALIZED_PNL_USD += trade_pnl_usd
                        if actual_pnl_percent > 0:
                            WINNING_TRADES += 1
                            result_title = "✅ <b>TRAILING TAKE PROFIT!</b>"
                        else:
                            result_title = "🛑 <b>TRAILING STOPLOSS!</b>"
                        await send_msg(f"{result_title}\n\n"
                                       f"<b>Token:</b> {trade_data['name']}\n"
                                       f"<b>Highest Peak:</b> ${trade_data['highest_price']:.6f}\n"
                                       f"<b>Riba/Asara (PNL):</b> {actual_pnl_percent:.2f}%\n"
                                       f"<b>Net Kudi:</b> ${trade_pnl_usd:.2f}\n\n"
                                       f"<i>Bot ya sayar saboda ya fado -30% daga saman da ya kai.</i>")
                        del ACTIVE_PAPER_TRADES[token_address]
            except:
                pass
        await asyncio.sleep(10)

async def track_and_trade(signature):
    await asyncio.sleep(8)
    token_address = None
    tx_url = f"[https://api.helius.xyz/v0/transactions/?api-key=](https://api.helius.xyz/v0/transactions/?api-key=){HELIUS_API_KEY}"
    try:
        tx_res = requests.post(tx_url, json={"transactions": [signature]}).json()
        if len(tx_res) > 0:
            for acc in tx_res[0].get("accountData", []):
                if acc["account"] != "So11111111111111111111111111111111111111112":
                    token_address = acc["account"]
                    break
    except:
        pass
    if not token_address or token_address in SEEN_TOKENS:
        return 
    SEEN_TOKENS.add(token_address)
    tracked_status = 'tracking'
    for _ in range(40): 
        url = f"[https://api.dexscreener.com/latest/dex/tokens/](https://api.dexscreener.com/latest/dex/tokens/){token_address}"
        try:
            res = requests.get(url).json()
            if res.get('pairs'):
                pair = res['pairs'][0]
                name = pair.get('baseToken', {}).get('name', 'Unknown')
                mcap = float(pair.get('fdv', 0))
                volume = float(pair.get('volume', {}).get('h24', 0))
                price = float(pair.get('priceUsd', 0))
                if tracked_status == 'tracking':
                    alert_msg = (f"🎓 <b>SABON GRADUATION (BONDED)!</b>\n\n"
                                 f"<b>Suna:</b> {name}\n"
                                 f"<b>CA:</b> <code>{token_address}</code>\n"
                                 f"<b>MCAP:</b> ${mcap:,.2f}\n"
                                 f"<b>Volume:</b> ${volume:,.2f}\n\n"
                                 f"<i>Bot yana jiran Retest <=30k da Bounce >=30k...</i>")
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
                                           f"<b>Suna:</b> {name}\n"
                                           f"<b>Farashi:</b> ${price:.6f}\n"
                                           f"<b>MCAP:</b> ${mcap:,.2f}\n"
                                           f"<b>Volume:</b> ${volume:,.2f}\n"
                                           f"<b>Kudi:</b> ${PAPER_TRADE_AMOUNT}\n\n"
                                           f"✅ <i>Dokoki sun cika! An kunna -30% Trailing Stoploss.</i>")
                            break 
        except:
            pass
        await asyncio.sleep(10)

async def pydroid_heartbeat():
    while True:
        print("🟢 Injin yana numfashi a cikin Render...")
        await asyncio.sleep(10)

async def kdv_snipe_bot():
    print("🚀 BOT YA TASHI! Zai tura sako a Telegram yanzu...")
    await send_msg("🟢 <b>KDV-Scanner An Dora Shi a RENDER (Cloud)!</b>\n<i>Yanzu Bot din ya zama na kansa. Baya bukatar wayarka ko intanet dinka. Zai yi aiki 24/7 ba dare ba rana!</i>")
    uri = f"wss://[mainnet.helius-rpc.com/?api-key=](https://mainnet.helius-rpc.com/?api-key=){HELIUS_API_KEY}"
    asyncio.create_task(monitor_active_trades())
    asyncio.create_task(send_hourly_report())
    asyncio.create_task(send_daily_report())
    asyncio.create_task(pydroid_heartbeat()) 
    while True:
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as ws:
                req = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [
                        {"mentions": ["39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg"]}, 
                        {"commitment": "processed"}
                    ]
                }
                await ws.send(json.dumps(req))
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if "params" in data:
                        sig = data["params"]["result"]["value"]["signature"]
                        logs = str(data["params"]["result"]["value"]["logs"])
                        if sig not in SEEN_SIGS:
                            if "InitializeInstruction2" in logs:
                                SEEN_SIGS.add(sig)
                                asyncio.create_task(track_and_trade(sig))
        except Exception as e:
            await asyncio.sleep(2) 

if __name__ == "__main__":
    # Fara kunna gidan yauwarar nan tukunna (Fake website)
    keep_alive()
    # Sannan a kaddamar da asalin Bot din!
    asyncio.run(kdv_snipe_bot())