from flask import request, jsonify
from datetime import datetime
from datetime import time as dt_time  # ➔ Saat nesnesi karşılaştırması için eklendi
from PIL import Image
import io
import requests
from database import get_db
from google.cloud.firestore_v1.base_query import FieldFilter
from whatsapp_service import whatsapp_mesaj_gonder # Senin yazdığın servis

# ------------------------------------------------------------------
# MESAİ SAATLERİ TANIMLAMALARI (09:00 - 00:00)
# ------------------------------------------------------------------
MESAI_BASLANGIC = dt_time(9, 0, 0)   # Sabah 09:00
# Saat nesnelerinde 24:00 tanımlanamadığı için günü 23:59:59'da kapatıyoruz
MESAI_BITIS = dt_time(23, 59, 59)    # Gece 00:00
# ------------------------------------------------------------------

@app.route('/webhook', methods=['POST'])
def green_api_webhook():
    data = request.json
    db = get_db()
    
    try:
        if data.get('typeWebhook') == 'incomingMessageReceived':
            mesaj_verisi = data['messageData']
            
            # Green API'den gelen numara genellikle "905xxxxxxxxx@c.us" formatındadır.
            chat_id = data['senderData']['chatId'] 
            gonderen_numara = chat_id.split('@')[0] # Sadece saf numarayı alıyoruz: "905xxxxxxxxx"
            
            # Numarayı bizim sistem formatına (05xx'li yapıya) çevirelim ki veritabanında bulabilelim
            arama_numarasi = gonderen_numara
            if gonderen_numara.startswith("90"):
                arama_numarasi = "0" + gonderen_numara[2:] # "05xxxxxxxxx" yaptık
            
            # Sunucunun anlık saatini alıyoruz
            su_an = datetime.now().time()
            
            # --- ÖĞRENCİYİ VERİTABANINDAN TESPİT ETME (AKILLI KÖPRÜ) ---
            ogrenci_id = "Bilinmeyen"
            ogrenci_adi = "Bilinmeyen Öğrenci"
            
            if db:
                try:
                    # Firestore'da telefon numarası eşleşen öğrenciyi arıyoruz
                    ogr_docs = db.collection("ogrenciler").where(filter=FieldFilter("Ogrenci Telefonu", "==", arama_numarasi)).get()
                    if not ogr_docs:
                        # Eğer öğrenci telefonundan bulunamadıysa veli numarasından tarayalım
                        ogr_docs = db.collection("ogrenciler").where(filter=FieldFilter("Veli Telefonu", "==", arama_numarasi)).get()
                        
                    if ogr_docs:
                        ogrenci_id = ogr_docs[0].id
                        ogrenci_adi = ogr_docs[0].to_dict().get("Ad Soyad", "İsimsiz Öğrenci")
                except Exception as e:
                    print(f"Öğrenci veritabanında aranırken hata oluştu: {e}")

            # --- METİN MESAJI GELDİYSE ---
            if mesaj_verisi['typeMessage'] == 'textMessage':
                gelen_mesaj = mesaj_verisi['textMessageData']['textMessage']
                
                # MESAİ KONTROLÜ
                if MESAI_BASLANGIC <= su_an <= MESAI_BITIS:
                    # Mesai saatleri içindeyse asistan araya girmez, öğretmen kendisi cevaplar
                    print(f"[MESAİ İÇİ] {ogrenci_adi} yazdı. Otomatik yanıt verilmedi.")
                    pass
                else:
                    # Asistan devreye giriyor (Gece 00:00 - Sabah 09:00)
                    prompt = f"Sen Büşra Hoca'nın yapay zeka asistanısın. WhatsApp'tan yazan öğrencinin adı: {ogrenci_adi}. Öğrenci sana şunu yazdı: '{gelen_mesaj}'. Onu motive edecek, nazik ve çok tatlı bir asistan cevabı üret."
                    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    
                    # Green API'ye mesajı basıyoruz (chat_id: '905xxxxxxxxx@c.us')
                    whatsapp_mesaj_gonder(chat_id, response.text)
                    
                    # SORUYU VE ÖĞRENCİ KİMLİĞİNİ HAFTALIK ANALİZ İÇİN KAYDET
                    if db:
                        db.collection("haftalik_sorular").add({
                            "ogrenci_id": ogrenci_id,
                            "ogrenci_adi": ogrenci_adi,
                            "telefon": arama_numarasi,
                            "soru_metni": gelen_mesaj,
                            "tip": "Metin",
                            "tarih": datetime.now()
                        })
            
            # --- FOTOĞRAFLI SORU GELDİYSE ---
            elif mesaj_verisi['typeMessage'] == 'imageMessage':
                foto_url = mesaj_verisi['fileMessageData']['downloadUrl']
                alt_yazi = mesaj_verisi['fileMessageData'].get('caption', '(Not bırakılmadı)')
                
                # MESAİ KONTROLÜ
                if MESAI_BASLANGIC <= su_an <= MESAI_BITIS:
                    print(f"[MESAİ İÇİ] {ogrenci_adi} fotoğraf gönderdi. Otomatik yanıt verilmedi.")
                    pass
                else:
                    # Yapay zeka soruyu çözüyor (Gece 00:00 - Sabah 09:00)
                    img_response = requests.get(foto_url)
                    img = Image.open(io.BytesIO(img_response.content))
                    
                    prompt = f"Sen harika bir matematik ve geometri öğretmenisin. {ogrenci_adi} isimli öğrenci sana çözemediği bir soru fotoğrafı gönderdi. Öğrencinin bıraktığı not: '{alt_yazi}'. Lütfen bu fotoğraftaki soruyu adım adım, anlaşılır ve pedagojik kurallara uygun olarak çöz."
                    response = client.models.generate_content(model='gemini-1.5-flash', contents=[prompt, img])
                    
                    whatsapp_mesaj_gonder(chat_id, response.text)
                    
                    # FOTOĞRAFLI SORU KAYDINI ÖĞRENCİ BİLGİLERİYLE İŞLE
                    if db:
                        db.collection("haftalik_sorular").add({
                            "ogrenci_id": ogrenci_id,
                            "ogrenci_adi": ogrenci_adi,
                            "telefon": arama_numarasi,
                            "soru_metni": f"Fotoğraflı Soru. Öğrenci Notu: {alt_yazi}",
                            "fotograf_url": foto_url,
                            "tip": "Görsel",
                            "tarih": datetime.now()
                        })

    except Exception as e:
        print(f"Webhook okuma hatası: {e}")

    return jsonify({"status": "success"}), 200