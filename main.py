import os
import time
import requests
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot XAU/USD Gercek Spot Motoru Aktif!", 200

@app.route('/healthz')
def health():
    return "OK", 200

# YENİ TELEGRAM VE STRATEJİ AYARLARI
TOKEN = "8690793145:AAE7Z5CzLByrwz9WQZ2eWyCreat4p_J-8VE"
CHAT_ID = "-5303003876"

fiyatlar = []

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
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
    print("Bot ana döngüsü GERÇEK ANLIK SPOT XAU/USD motoru ile başlatıldı...", flush=True)
    time.sleep(3)
    
    # Akıllı Sinyal Kilidi: Üst üste ters/hatalı sinyalleri engeller
    son_sinyal = None
    
    while True:
        try:
            # Canlı Forex Spot Altın (XAU/USD=X) doğrudan veri akışı
            url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?interval=1m&range=1d"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Tamamen makassız, aracı kurumsuz net spot fiyat
                anlik_fiyat = round(float(data["chart"]["result"][0]["meta"]["regularMarketPrice"]), 2)
                
                fiyatlar.append(anlik_fiyat)
                
                if len(fiyatlar) > 100:
                    fiyatlar.pop(0)
                
                print(f"Canlı SPOT XAUUSD: {anlik_fiyat} | Havuz: {len(fiyatlar)}", flush=True)
                
                rsi = rsi_hesapla(fiyatlar)
                if rsi is not None:
                    print(f"Güncel RSI: {rsi:.2f}", flush=True)
                    
                    # RSI 67 üstü ve önceki sinyal SELL değilse tetikle
                    if rsi >= 67 and son_sinyal != "SELL":
                        telegram_mesaj_gonder(f"🔴 SELL (AŞIRI ALIM)\n💰 Canlı Spot XAUUSD: {anlik_fiyat}\n📈 RSI: {rsi:.2f}")
                        son_sinyal = "SELL"
                    
                    # RSI 33 altı ve önceki sinyal BUY değilse tetikle
                    elif rsi <= 33 and son_sinyal != "BUY":
                        telegram_mesaj_gonder(f"🟢 BUY (AŞIRI SATIM)\n💰 Canlı Spot XAUUSD: {anlik_fiyat}\n📉 RSI: {rsi:.2f}")
                        son_sinyal = "BUY"
                        
                    # RSI normale döndüğünde kilidi aç, yeni sinyale hazırlık yap
                    elif 43 <= rsi <= 57:
                        son_sinyal = None
            else:
                print(f"Spot fiyat çekilemedi, durum kodu: {response.status_code}", flush=True)
                
        except Exception as e:
            print(f"Veri akışı yenileniyor... Spot XAU/USD bekleniyor.", flush=True)
            
        # 25 saniyede bir verileri tazeleyip stabil analiz yapar
        time.sleep(25)

if __name__ == "__main__":
    t = threading.Thread(target=bot_ana_dongu)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
