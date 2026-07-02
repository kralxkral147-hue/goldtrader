import os
import time
import requests
import threading
from flask import Flask

# Flask web sunucusu (Render'ı kandırmak ve ücretsiz kullanmak için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif ve calisiyor!", 200

@app.route('/healthz')
def health():
    return "OK", 200

# TELEGRAM VE STRATEJİ AYARLARI
TOKEN = "7349182394:AAH_fX39Y2kZlzM4kO9wPlR2X7mNq1uV8zo"
CHAT_ID = "-5303003876"  # Grup ID'niz hazır

# RSI için fiyat havuzu
fiyatlar = []

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hatasi: {e}")

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

# Ana Bot Döngüsü (Arka planda çalışacak)
def bot_ana_dongu():
    print("Bot döngüsü başlatıldı...")
    time.sleep(5)  # Sunucunun tam oturması için kısa bir bekleme
    telegram_mesaj_gonder("🚀 GoldHunter Akıllı Scalp Botu 7/24 Sunucuda Başlatıldı!\n\n📊 RSI ve Fiyat takibi aktif.")
    
    while True:
        try:
            # Altın fiyatını çekme (XAU/USD)
            response = requests.get("https://api.binance.com/api/3/ticker/price?symbol=XAUUSDT")
            if response.status_code == 200:
                data = response.json()
                anlik_fiyat = float(data["price"])
                fiyatlar.append(anlik_fiyat)
                
                # Belleğin şişmemesi için son 100 veriyi tutalım
                if len(fiyatlar) > 100:
                    fiyatlar.pop(0)
                
                print(f"Anlık Fiyat: {anlik_fiyat} | Havuzdaki Veri: {len(fiyatlar)}")
                
                # RSI hesaplama ve Sinyal Kontrolü
                rsi = rsi_hesapla(fiyatlar)
                if rsi is not None:
                    print(f"Güncel RSI: {rsi:.2f}")
                    if rsi >= 67:
                        telegram_mesaj_gonder(f"🔴 SELL (AŞIRI ALIM)\n💰 Fiyat: {anlik_fiyat}\n📈 RSI: {rsi:.2f}\n⚠️ Düzeltme gelebilir, Satış yönlü demo test edilebilir!")
                    elif rsi <= 33:
                        telegram_mesaj_gonder(f"🟢 BUY (AŞIRI SATIM)\n💰 Fiyat: {anlik_fiyat}\n📉 RSI: {rsi:.2f}\n⚠️ Tepki yükselişi gelebilir, Alış yönlü demo test edilebilir!")
            
        except Exception as e:
            print(f"Döngü hatası: {e}")
            
        time.sleep(20) # 20 saniyede bir kontrol

if __name__ == "__main__":
    # Bot döngüsünü ana web sunucusunu kilitlemesin diye ayrı bir iş parçacığında (Thread) başlatıyoruz
    t = threading.Thread(target=bot_ana_dongu)
    t.daemon = True
    t.start()
    
    # Render'ın istediği portu alıp web sunucusunu ayağa kaldırıyoruz
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
