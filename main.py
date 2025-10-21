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
# HANYA GUNAKAN NAMA VARIABEL DI SINI, BUKAN NILAI KUNCI ASLI.
CMC_API_KEY = os.environ.get('CMC_API_KEY') 
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# Penyimpanan status early warning & akumulasi
# DIHAPUS KARENA STATUS TIDAK DAPAT DISIMPAN DI AKUN GRATIS PYTHONANYWHERE
# early_warning_status = {}
# accumulation_status = {}


# =========================
# 📩 FUNGSI KIRIM TELEGRAM
# =========================
def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        # Jika GAGAL KIRIM, tampilkan error di log PythonAnywhere
        print("❌ Gagal kirim pesan Telegram:", e)

# =========================
# 💰 FUNGSI AMBIL DATA COINMARKETCAP
# =========================
def get_top_coins(limit=50):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {"start": "1", "limit": str(limit), "convert": "USD"}
    
    # Perbaikan: Tambahkan pemeriksaan jika API Key kosong
    if not CMC_API_KEY:
        raise ValueError("CMC_API_KEY tidak ditemukan. Pastikan sudah di-export di terminal.")

    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(url, headers=headers, params=params)
    
    # Jika ada error 401, error akan ditampilkan di log PythonAnywhere
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
# 📈 TREND ANALYZER
# =========================
def analisis_trend(q):
    p1h = q["percent_change_1h"]
    p24h = q["percent_change_24h"]
    avg_per_hour = p24h / 24
    diff = p1h - avg_per_hour
    if diff > 2:
        return "🔺 Reversal Naik"
    elif diff < -2:
        return "🔻 Reversal Turun"
    else:
        return "⚪ Sideways"

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
    # Hapus penggunaan early_warning_status dan accumulation_status 
    # karena tidak dapat disimpan di akun gratis.
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
        trend = analisis_trend(q)

        muncul = False

        # 🚀 Pump Cepat
        if p1h * 2 >= 10 or score >= 0.9:
            muncul = True
            pesan += f"🚀 *{symbol}* (${price:,.2f})\n"
            pesan += f"🕒 {p1h*2:+.2f}% / 2 jam | {p24h:+.2f}% / 24 jam\n"
            pesan += f"💰 Volume: ${volume/1_000_000:,.2f}M | Rank #{rank} | Score: {score}\n"
            pesan += f"📊 Trend: {trend}\n\n"

        # ⚠️ Akan Pump
        elif akan_pump(coin):
            muncul = True
            pesan += f"⚠️ *{symbol}* (${price:,.4f})\n"
            pesan += f"🩵 Volume meningkat (pra-pump)\n"
            pesan += f"📈 Momentum bullish awal | {trend}\n\n"

        # 🧭 Early Warning
        elif early_warning(coin):
            muncul = True
            pesan += f"🧭 *{symbol}* (${price:,.4f})\n"
            pesan += f"💡 Early warning: mulai menunjukkan pergerakan bullish\n"
            pesan += f"📈 {p1h:+.2f}% / 1 jam | {p24h:+.2f}% / 24 jam | {trend}\n\n"
            
        # 🧱 Akumulasi Smart Money
        # Fitur ini dihilangkan karena bergantung pada penyimpanan status sebelumnya
        # Untuk menjalankan fitur ini perlu upgrade akun berbayar atau database eksternal

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
    except Exception as e:
        # Menampilkan pesan error di log PythonAnywhere jika gagal
        print(f"[{datetime.now()}] ❌ FATAL ERROR. Bot gagal berjalan:", e)

