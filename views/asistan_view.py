import customtkinter as ctk
import threading
import os
import speech_recognition as sr
from database import get_db
from datetime import datetime

# Yeni ses ve AI modülleri
import pygame
from gtts import gTTS
import google.generativeai as genai

class AsistanView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.COLOR_SIDEBAR = "#044D29"
        self.db = get_db()
        
        # Sadece dinleyiciyi başlatıyoruz, pyttsx3 tamamen kaldırıldı
        self.recognizer = sr.Recognizer()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.arayuz_olustur()

    def arayuz_olustur(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        header.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(header, text="Büşra Hoca AI - Sesli Asistan", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left", padx=20, pady=20)

        chat_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        chat_frame.grid(row=1, column=0, padx=40, pady=(0, 40), sticky="nsew")
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)
        
        self.txt_sohbet = ctk.CTkTextbox(chat_frame, fg_color="#F4F1EA", font=ctk.CTkFont(size=14))
        self.txt_sohbet.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.ent_mesaj = ctk.CTkEntry(input_frame, placeholder_text="Mesajınızı yazın veya sesle söyleyin...", height=40)
        self.ent_mesaj.grid(row=0, column=0, sticky="ew")
        
        self.btn_sesli = ctk.CTkButton(input_frame, text="🎤", width=40, height=40, fg_color="#C0392B", command=self.sesi_baslat)
        self.btn_sesli.grid(row=0, column=1, padx=5)
        
        self.btn_gonder = ctk.CTkButton(input_frame, text="Gönder", fg_color=self.COLOR_SIDEBAR, width=100, height=40, command=self.mesaj_gonder)
        self.btn_gonder.grid(row=0, column=2, padx=(5, 0))

        self.ent_mesaj.bind("<Return>", lambda e: self.mesaj_gonder())

    # --- SESLİ ASİSTAN FONKSİYONLARI (gTTS ile Doğal Türkçe) ---
    def konus(self, metin):
        threading.Thread(target=self._soyle, args=(metin,), daemon=True).start()

    def _soyle(self, metin):
        try:
            tts = gTTS(text=metin, lang='tr', slow=False)
            dosya_adi = "asistan_cevap.mp3"
            tts.save(dosya_adi)
            
            pygame.mixer.init()
            pygame.mixer.music.load(dosya_adi)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.quit()
            if os.path.exists(dosya_adi):
                os.remove(dosya_adi)
        except Exception as e:
            print(f"Konuşma hatası: {e}")

    def sesi_baslat(self):
        threading.Thread(target=self.dinle, daemon=True).start()

    def dinle(self):
        with sr.Microphone() as source:
            self.txt_sohbet.insert("end", "\n🤖 Asistan: Dinliyorum...\n")
            self.txt_sohbet.see("end")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
                komut = self.recognizer.recognize_google(audio, language="tr-TR")
                
                self.ent_mesaj.delete(0, 'end')
                self.ent_mesaj.insert(0, komut)
                self.mesaj_gonder()
            except sr.WaitTimeoutError:
                self.txt_sohbet.insert("end", "\n🤖 Asistan: Ses duyamadım, tekrar dener misin?\n")
            except Exception as e:
                self.txt_sohbet.insert("end", f"\n🤖 Asistan: Anlayamadım, tekrar dener misin?\n")
            self.txt_sohbet.see("end")

    # --- MESAJ GÖNDERME VE GEMINI AI MANTIĞI ---
    def mesaj_gonder(self):
        mesaj = self.ent_mesaj.get()
        if not mesaj: return
        
        self.ent_mesaj.delete(0, 'end')
        self.txt_sohbet.insert("end", f"\n👤 Siz: {mesaj}\n")
        self.txt_sohbet.see("end")
        
        self.btn_gonder.configure(state="disabled")
        threading.Thread(target=self._ai_yanit, args=(mesaj,), daemon=True).start()

    def _takvim_verilerini_topla(self):
        takvim_metni = ""
        if self.db:
            try:
                dersler_docs = self.db.collection("dersler").stream()
                for doc in dersler_docs:
                    d = doc.to_dict()
                    ogrenci = d.get("Öğrenci", d.get("ogrenci_ad", "Bilinmeyen Öğrenci"))
                    gun = d.get("Gün", d.get("gun", ""))
                    saat = d.get("Saat", d.get("saat", ""))
                    ders_adi = d.get("Ders", d.get("ders_adi", "Matematik"))
                    
                    takvim_metni += f"- Öğrenci: {ogrenci}, Gün: {gun}, Saat: {saat}, Ders: {ders_adi}\n"
            except Exception as e:
                takvim_metni = "Takvim verileri şu an yüklenemedi."
        
        if not takvim_metni:
            takvim_metni = "Takvimde kayıtlı aktif bir ders programı bulunmuyor."
        return takvim_metni

    def _ai_yanit(self, mesaj):
        # GEMINI API ENTEGRASYONU
        api_key = os.getenv("GEMINI_API_KEY", "YENI_GEMINI_API_KEYINIZI_BURAYA_YAZIN")
        
        if not api_key or api_key == "YENI_GEMINI_API_KEYINIZI_BURAYA_YAZIN":
            self.after(0, lambda: self.txt_sohbet.insert("end", "\n🤖 Asistan: Lütfen Gemini API anahtarınızı kodun içine veya sistem ortam değişkenlerine ekleyin.\n"))
            self.after(0, lambda: self.btn_gonder.configure(state="normal"))
            return

        guncel_takvim = self._takvim_verilerini_topla()

        prompt = (
            f"Sen Büşra Hoca'nın dijital asistanısın. Görevin, onun öğrencilerine veya velilerine onun üslubuyla kısa ve öz cevap vermek. "
            f"Çok tatlı, anaç ama akademik olarak tam donanımlı ve disiplinli bir dille yazacaksın. "
            f"Gerektiğinde 'canım, tatlım, güzel çocuğum' gibi ifadeler kullanabilirsin.\n\n"
            f"SİSTEMDEKİ GÜNCEL DERS TAKVİMİ / PROGRAMI:\n"
            f"{guncel_takvim}\n\n"
            f"KURUMSAL TALİMAT:\n"
            f"Eğer gelen mesajda öğrenci veya veli dersin ne zaman olduğunu, hangi gün olduğunu soruyorsa, yukarıdaki güncel ders takviminden o öğrencinin adını bul, gün ve saat bilgisini tespit ederek doğrudan öğrenciye/veliye hitaben tatlı bir dille cevapla. Eğer takvimde ismi yoksa veya eşleşmiyorsa, 'Sistemde kaydını göremedim tatlım, kontrol etmem için tam adını yazar mısın?' şeklinde yanıt ver.\n\n"
            f"İşte gelen mesaj/soru: '{mesaj}'"
        )

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            text = response.text
            
            self.after(0, lambda: self.txt_sohbet.insert("end", f"\n🤖 Büşra Hoca AI: {text}\n\n"))
            self.konus(text)  # Gemini'nin verdiği metni otomatik olarak sesli okutur
            
        except Exception as e:
            hata_metni = str(e)
            self.after(0, lambda msg=hata_metni: self.txt_sohbet.insert("end", f"\n⚠️ Gemini Bağlantı Hatası: {msg}\n"))
            
        self.after(0, lambda: self.txt_sohbet.see("end"))
        self.after(0, lambda: self.btn_gonder.configure(state="normal", text="Gönder"))