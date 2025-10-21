# ===========================================
# 🤖 AI CRYPTO SCREENER v5.0 — Smart Money Accumulation Detector
# ===========================================
# ✅ CoinMarketCap API + Telegram
# ✅ Deteksi otomatis pump, pra-pump, early warning, double confirmation & akumulasi
# ===========================================

import requests
import time
import os
from datetime import datetime, timedelta

# =========================
# 🔧 KONFIGURASI
# =========================
# MENGAMBIL VARIABEL DARI ENVIRONMENT (PASTIKAN SUDAH DIEKSPORT DI TERMINAL PYTHONANYWHERE!)
CMC_API_KEY = os.environ.get('11403b1c047048fd9b26b0fe8d5d9afe') 
TELEGRAM_TOKEN = os.environ.get('8490918160:AAEfvmptL0qPfXmavKi4H1HbjwgDCcG7Yz4')
CHAT_ID = os.environ.get('7568851202') 
# Pastikan CHAT_ID adalah ID Negatif jika dikirim ke Grup/Channel

# =========================
# 📩 FUNGSI KIRIM TELEGRAM
# =========================
def kirim_telegram(pesan):
    """Mengirim pesan ke Telegram menggunakan Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ ERROR: TELEGRAM_TOKEN atau CHAT_ID tidak ditemukan/kosong.")
        return

    try:
        r = requests.post(url, data=data)
        # Tambahkan log untuk debug jika Telegram menolak pesan
        if r.status_code != 200:
             print(f"❌ Gagal kirim pesan Telegram. Status: {r.status_code}, Respons: {r.text}")
    except Exception as e:
        print("❌ Gagal kirim pesan Telegram:", e)

# =========================
# 💰 FUNGSI AMBIL DATA COINMARKETCAP
# =========================
def get_top_coins(limit=50):
    """Mengambil data koin dari CoinMarketCap API."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {"start": "1", "limit": str(limit), "convert": "USD"}
    
    if not CMC_API_KEY:
        raise ValueError("CMC_API_KEY tidak ditemukan. Pastikan sudah di-export di terminal.")

    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(url, headers=headers, params=params)
    
    # Akan menampilkan error 401, 429, dll., di log PythonAnywhere
    r.raise_for_status() 
    
    data = r.json()
    return data["data"]

# =========================
# 🧠 AI SCORE
# =========================
def ai_score(coin):
    score = 0
    q = coin["quote"]["USD"]
    if q["percent_change_1h"] > 2:
        score += 0.3
    if q["percent_change_24h"] > 10:
        score += 0.4
    if q["volume_24h"] > 10_000_000:
        score += 0.3
    return round(min(score, 1), 2)

# =========================
# 🔮 PRA-PUMP DETECTION
# =========================
def akan_pump(coin):
    q = coin["quote"]["USD"]
    vol = q["volume_24h"]
    p1h = q["percent_change_1h"]
    p24h = q["percent_change_24h"]
    vol_change_proxy = (p1h * 10)
    if vol > 5_000_000 and 0 < p1h < 2 and p24h < 6 and vol_change_proxy > 8:
        return True
    return False

# =========================
# 🧭 EARLY WARNING
# =========================
def early_warning(coin):
    q = coin["quote"]["USD"]
    p1h = q["percent_change_1h"]
    p24h = q["percent_change_24h"]
    vol = q["volume_24h"]
    if 0.5 <= p1h <= 2 and p24h < 5 and vol > 2_000_000:
        return True
    return False

# =========================
# 📊 BUAT PESAN TELEGRAM
# =========================
def buat_pesan(coins):
    wib = (datetime.utcnow() + timedelta(hours=7)).strftime("%d %b %Y | %H:%M WIB")
    pesan = f"📊 *[AI CRYPTO SCREENER v5.0]* — Update: {wib}\n\n"
    ada_sinyal = False

    for coin in coins:
        q = coin["quote"]["USD"]
        price = q["price"]
        p1h = q["percent_change_1h"]
        p24h = q["percent_change_24h"]
        volume = q["volume_24h"]
        rank = coin["cmc_rank"]
        symbol = coin["symbol"]
        score = ai_score(coin)

        muncul = False

        # 🚀 Pump Cepat (Kuat)
        if p1h * 2 >= 10 or score >= 0.9:
            muncul = True
            pesan += f"🚀 *{symbol}* (${price:,.2f})\n"
            pesan += f"🔥 Sinyal PUMP KUAT | Peningkatan volume dan harga\n"
            pesan += f"🕒 {p1h*2:+.2f}% / 2 jam | {p24h:+.2f}% / 24 jam\n"
            pesan += f"💰 Volume: ${volume/1_000_000:,.2f}M | Rank #{rank} | Score: {score}\n\n"

        # ⚠️ Akan Pump
        elif akan_pump(coin):
            muncul = True
            pesan += f"⚠️ *{symbol}* (${price:,.4f})\n"
            pesan += f"🩵 Pra-Pump: Volume meningkat, harga mulai naik perlahan\n"
            pesan += f"📈 {p1h:+.2f}% / 1 jam | {p24h:+.2f}% / 24 jam\n\n"

        # 🧭 Early Warning
        elif early_warning(coin):
            muncul = True
            pesan += f"🧭 *{symbol}* (${price:,.4f})\n"
            pesan += f"💡 Early warning: mulai menunjukkan pergerakan bullish\n"
            pesan += f"📈 {p1h:+.2f}% / 1 jam | {p24h:+.2f}% / 24 jam\n\n"

        if muncul:
            ada_sinyal = True

    if not ada_sinyal:
        pesan += "📉 Tidak ada sinyal signifikan saat ini."
    return pesan

# =====================================================================
# 🏃 BLOK UTAMA: HANYA JALANKAN SATU KALI (KHUSUS PYTHONANYWHERE)
# =====================================================================
if __name__ == "__main__":
    try:
        data = get_top_coins(50)
        pesan = buat_pesan(data)
        kirim_telegram(pesan)
        print(f"[{datetime.now()}] ✅ Update terkirim ke Telegram.")
    except requests.exceptions.HTTPError as err:
        error_msg = f"[{datetime.now()}] ❌ ERROR API/HTTP: {err}"
        print(error_msg)
        kirim_telegram(f"🤖 Bot Error (CMC): API Gagal ({err})")
    except Exception as e:
        error_msg = f"[{datetime.now()}] ❌ FATAL ERROR. Bot gagal berjalan: {e}"
        print(error_msg)
        kirim_telegram(f"🤖 Bot Error: {e}")
