import time
import urllib.request
import urllib.parse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Senin BotFather'dan aldığın Token ve Chat ID bilgilerin koda gömüldü kanka
TELEGRAM_TOKEN = "8690793145:AAF-pOMchclA_M090MtWmyOqiS8YkfSSPDY"
CHAT_ID = "-1005303003876"


fiyat_gecmisi = []

def telegram_mesaj_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={urllib.parse.quote(mesaj)}&parse_mode=Markdown"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        print(f"Telegram Hatası: {e}")
        return False

def altin_fiyati_al():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return float(data['pax-gold']['usd'])
    except Exception as e:
        print(f"Fiyat çekilemedi: {e}")
        return None

def rsi_hesapla(fiyatlar, periyot=14):
    if len(fiyatlar) < periyot + 1:
        return 50  # Yeterli veri toplanana kadar nötr (50) döndürür
    
    kazanclar = []
    kayiplar = []
    
    for i in range(1, len(fiyatlar)):
        fark = fiyatlar[i] - fiyatlar[i-1]
        if fark > 0:
            kazanclar.append(fark)
            kayiplar.append(0)
        else:
            kazanclar.append(0)
            kayiplar.append(abs(fark))
            
    ort_kazanc = sum(kazanclar[-periyot:]) / periyot
    ort_kayip = sum(kayiplar[-periyot:]) / periyot
    
    if ort_kayip == 0:
        return 100
        
    rs = ort_kazanc / ort_kayip
    rsi = 100 - (100 / (1 + rs))
    return rsi

def bot_dongusu():
    global fiyat_gecmisi
    print("🤖 Akıllı Scalp Botu 7/24 Modunda Başlatıldı...")
    telegram_mesaj_gonder("🚀 **GoldHunter Akıllı Scalp Botu 7/24 Sunucuda Başlatıldı!**\n\n📊 RSI ve Fiyat takibi aktif.")
    
    son_sinyal = None
    
    while True:
        guncel_fiyat = altin_fiyati_al()
        if guncel_fiyat:
            fiyat_gecmisi.append(guncel_fiyat)
            if len(fiyat_gecmisi) > 30:  # Belleği şişirmemek için son 30 fiyatı tutar
                fiyat_gecmisi.pop(0)
                
            rsi = rsi_hesapla(fiyat_gecmisi)
            print(f"Anlık Fiyat: {guncel_fiyat} USD | RSI (14): {rsi:.2f}")
            
            # 📈 STRATEJİ: RSI Aşırı Alım / Aşırı Satım bölgelerine göre pozisyon önerme
            if rsi <= 33 and son_sinyal != "BUY":
                telegram_mesaj_gonder(f"🟢 **XAU/USD - BUY (SCALP)** 🟢\n\n💰 **Fiyat:** {guncel_fiyat} USD\n📉 **RSI:** {rsi:.2f} (Aşırı Satım - Tepki Alımı)")
                son_sinyal = "BUY"
            elif rsi >= 67 and son_sinyal != "SELL":
                telegram_mesaj_gonder(f"🔴 **XAU/USD - SELL (SCALP)** 🔴\n\n💰 **Fiyat:** {guncel_fiyat} USD\n📈 **RSI:** {rsi:.2f} (Aşırı Alım - Düzeltme Satışı)")
                son_sinyal = "SELL"
                
        time.sleep(20)

# Render.com sunucusunun "port açık değil" hatası vermemesi için kurulan hafif web yapısı
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Aktif!")

if __name__ == "__main__":
    # Bot döngüsünü arka planda başlatır
    t = threading.Thread(target=bot_dongusu)
    t.daemon = True
    t.start()
    
    # Sunucu portunu dinlemeye alır (Render için zorunlu)
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()
