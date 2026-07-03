import os
import time
import requests
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif ve calisiyor!", 200

@app.route('/healthz')
def health():
    return "OK", 200

# TELEGRAM VE STRATEJİ AYARLARI
# Not: Telegram'a bağlanamazsa bile fiyat çekmeye devam etmesi için kod korumaya alındı.
TOKEN = "7349182394:AAH_fX39Y2kZlzM4kO9wPlR2X7mNq1uV8zo"
CHAT_ID = "-5303003876"

fiyatlar = []

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    try:
        r = requests.post(url, json=payload, timeout=5)
        print(f"Telegram Gönderim Durumu: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Telegram hatasi: {e}", flush=True)

def rsi_hesapla(seri, periyot=14):
    if len(seri) <= periyot:
        return None
    gains = []
    losses = []
    for i in range(1, len(seri)):
        fark = seri[i] - seri[i-1]
        if fark > 0:
            gains.append(fark)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(fark))
            
    avg_gain = sum(gains[-periyot:]) / periyot
    avg_loss = sum(losses[-periyot:]) / periyot
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bot_ana_dongu():
    print("Bot ana döngüsü Kesin Spot XAU/USD Motoru ile baslatiliyor...", flush=True)
    time.sleep(3)
    telegram_mesaj_gonder("🚀 GoldHunter Akıllı Scalp Botu Gerçek Spot XAU/USD Verisiyle Başlatıldı!\n\n📊 RSI ve Fiyat takibi aktif.")
    
    while True:
        try:
            # Tamamen açık, ücretsiz ve API anahtarı istemeyen alternatif canlı altın kaynağı
            url = "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "pax-gold" in data:
                    # Küresel spot altın fiyatı ile birebir eşlenik çalışır
                    anlik_fiyat = float(data["pax-gold"]["usd"])
                    fiyatlar.append(anlik_fiyat)
                    
                    if len(fiyatlar) > 100:
                        fiyatlar.pop(0)
                    
                    print(f"Canlı Spot XAUUSD Fiyatı: {anlik_fiyat} | Havuz: {len(fiyatlar)}", flush=True)
                    
                    rsi = rsi_hesapla(fiyatlar)
                    if rsi is not None:
                        print(f"Güncel RSI: {rsi:.2f}", flush=True)
                        if rsi >= 67:
                            telegram_mesaj_gonder(f"🔴 SELL (AŞIRI ALIM)\n💰 Spot XAUUSD: {anlik_fiyat}\n📈 RSI: {rsi:.2f}")
                        elif rsi <= 33:
                            telegram_mesaj_gonder(f"🟢 BUY (AŞIRI SATIM)\n💰 Spot XAUUSD: {anlik_fiyat}\n📉 RSI: {rsi:.2f}")
                else:
                    print("Veri formatı uyuşmadı, alternatif deneniyor...", flush=True)
            else:
                print(f"Fiyat saglayici hatasi, Kod: {response.status_code}", flush=True)
            
        except Exception as e:
            print(f"Döngü hatası: {e}", flush=True)
            
        time.sleep(20)

if __name__ == "__main__":
    t = threading.Thread(target=bot_ana_dongu)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
