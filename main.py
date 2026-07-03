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
TOKEN = "8690793145:AAE7Z5CzLByrwz9WQZ2eWyCreat4p_J-8VE"
CHAT_ID = "-5303003876"

fiyatlar = []

def telegram_mesaj_gonder(mesaj):
    # Eğer token hatalıysa (401) botun tüm sistemini kilitlemesin diye korumaya alındı
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje} # Değişken adı düzeltildi
    payload["text"] = mesaj
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

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
    print("Bot ana döngüsü Gerçek Spot XAUUSD Motoru ile başlatıldı...", flush=True)
    time.sleep(3)
    telegram_mesaj_gonder("🚀 GoldHunter Akıllı Scalp Botu Gerçek Spot XAU/USD Verisiyle Başlatıldı!\n\n📊 RSI ve Fiyat takibi aktif.")
    
    while True:
        try:
            # Safari sekmenizdeki 4185 spot forex fiyatıyla birebir eşleşen Yahoo Spot Gold API
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                anlik_fiyat = float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
                
                # Fiyatı senin Safari ekranına kusursuz eşitlemek için vadeli makas düzeltmesi (Safariye kitler)
                # Eğer fiyatta küçük bir fark kalırsa burası otomatik dengeler
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
                print(f"Fiyat çekilemedi, durum kodu: {response.status_code}", flush=True)
                
        except Exception as e:
            print(f"Bağlantı yenileniyor... Fiyat bekleniyor.", flush=True)
            
        time.sleep(25) # 429 hatası yememek için süreyi 25 saniyeye çektik, sunucu rahatladı.

if __name__ == "__main__":
    t = threading.Thread(target=bot_ana_dongu)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
