import speech_recognition as sr
import google.generativeai as genai
import pyttsx3
import threading
from database import get_db
import customtkinter as ctk
import os
import requests
import time
from PIL import Image
from datetime import datetime
import datetime as dt

# Görünüm (View) Importları
from views.ogrenciler_view import OgrencilerView
from views.dersler_view import DerslerView
from views.muhasebe_view import MuhasebeView
from views.akademik_view import AkademikView
from views.odevler_view import OdevlerView
from views.konu_takip_view import KonuTakipView
from views.kaynaklar_view import KaynaklarView
from views.denemeler_view import DenemelerView
from views.yoklama_view import YoklamaView
from views.mufredat_view import MufredatView
from views.soru_takip_view import SoruTakipView
from views.ai_soru_view import AISoruView
from views.rozetler_view import RozetlerView
from views.ajanda_view import AjandaView
from views.rapor_view import RaporView
from views.program_view import ProgramView
from views.hata_telafi_view import HataTelafiView
from views.asistan_view import AsistanView

# Renk Paleti
COLOR_SIDEBAR = "#044D29"
COLOR_SIDEBAR_HOVER = "#066838"
COLOR_ACCENT_GOLD = "#D4AF37"
COLOR_TEXT_LIGHT = "#FDFDFB"
COLOR_TEXT_DARK = "#1A1A1A"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Büşra Öğretmen Eğitim Platformu")
        self.geometry("1450x900")
        
        # Tema Ayarları
        ctk.set_appearance_mode("light")
        
        # Ana Grid Yapısı
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # AI Konfigürasyonu
        genai.configure(api_key="BURAYA_API_ANAHTARINI_YAZ")

        # ------------------------------------------------------------------
        # GREEN API MERKEZİ SABİTLERİ (KODUN İÇİNE GÖMÜLDÜ - GARANTİLİ)
        # ------------------------------------------------------------------
        self.GREEN_INSTANCE_ID = "BURAYA_GREEN_API_ID_INSTANCE_YAZ"
        self.GREEN_API_TOKEN = "BURAYA_GREEN_API_TOKEN_YAZ"

        self.student_menu_open = False
        self.dersler_menu_open = False

        self.create_sidebar()
        self.create_main_frames()
        
        # Başlangıç Sayfası
        self.show_dashboard()

        # TAM OTOMATİK ARKA PLAN MOTORUNU BAŞLATMA
        threading.Thread(target=self.otomasyon_zamanlayici_dongusu, daemon=True).start()

        # Kapanış Protokolü
        self.protocol("WM_DELETE_WINDOW", self.on_kapanis)

    def on_kapanis(self):
        """Program kapatılırken arka plan görevlerini güvenle sonlandırır."""
        self.quit()     
        self.destroy()  
        import sys
        sys.exit(0)

    # ------------------------------------------------------------------
    # OTOMASYON ZAMANLAYICI VE AI RAPORLAMA MOTORU
    # ------------------------------------------------------------------
    def otomasyon_zamanlayici_dongusu(self):
        """Sessizce zamanı takip eden, Rapor ve Hatırlatmaları tetikleyen döngü."""
        son_rapor_gonderim = ""
        self.hatirlatilan_dersler_cache = set() 
        
        while True:
            simdi = datetime.now()
            
            # --- DÜZENLEME: HAFTALIK AI RAPORU ARTIK PAZARTESİ SABAH 10:00'DA GİDİYOR ---
            if simdi.isoweekday() == 1 and simdi.hour == 10 and son_rapor_gonderim != simdi.strftime("%Y-%m-%d"):
                print("[OTOMASYON] Pazartesi Sendromuna Son! AI Raporlama Zinciri Başlatıldı...")
                
                # Öğrencilere giden bireysel raporlar ve şampiyonluk rozeti
                self.tum_ogrencilere_otomatik_rapor_hazirla()
                
                # BÜŞRA HOCAYA ÖZEL GECE SORULARI ANALİZİ
                db = get_db()
                if db:
                    self._busra_hoca_zayif_nokta_raporu_hazirla(db)
                    
                son_rapor_gonderim = simdi.strftime("%Y-%m-%d")
            
            # 2. DERS HATIRLATMA OTOMASYONU
            self.yaklasan_dersleri_hatirlat(simdi)
            
            time.sleep(60)

    def _busra_hoca_zayif_nokta_raporu_hazirla(self, db):
        """Haftalık biriken tüm soruları analiz eder, hocaya mail atar ve verileri kalıcı olarak siler."""
        sorular_listesi = []
        doc_referanslari = []
        
        try:
            sorular_koleksiyonu = db.collection("haftalik_sorular").stream()
            for doc in sorular_koleksiyonu:
                sorular_listesi.append(doc.to_dict().get("soru_metni", ""))
                doc_referanslari.append(doc.reference)
                
            if not sorular_listesi:
                return 
                
            sorular_metni = "\n- ".join(sorular_listesi)
            
            prompt = (
                f"Sen usta bir veri analisti ve eğitim koçusun. Öğrenciler bu hafta gece asistanına şu konularda sorular sordu:\n"
                f"{sorular_metni}\n\n"
                f"Lütfen Matematik Öğretmeni Büşra Hoca'ya hitaben profesyonel bir 'Haftalık Zayıf Nokta ve Gelişim Analizi' raporu yaz. "
                f"Öğrencilerin en çok hangi konularda zorlandığını, hangi kuralları unuttuklarını grupla ve önümüzdeki hafta derslerde neyin üzerinde durması gerektiğine dair kısa tavsiyeler ver."
            )
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            analiz_cevabi = model.generate_content(prompt).text
            
            gonderen_mail = os.getenv("EMAIL_USER", "kurumsal_hesap@gmail.com") 
            mesaj = (f"Sayın Büşra Hocam,\n\nYapay Zeka modülümüz bu haftaki öğrenci sorularını analiz etti. "
                     f"İşte haftanın Zayıf Nokta Raporu:\n\n{analiz_cevabi}")
            
            threading.Thread(target=self._bildirimleri_gonder, args=(gonderen_mail, None, "Zayıf Nokta Analizi", mesaj), daemon=True).start()
            print("[YÖNETİCİ RAPORU] Zayıf nokta analizi başarıyla oluşturuldu ve e-postaya iletildi.")
            
            for ref in doc_referanslari:
                ref.delete()
                
        except Exception as e:
            print(f"Zayıf nokta analiz hatası: {e}")

    def src_temizle_no(self, tel):
        """Numarayı sadece sayılardan oluşacak şekilde temizler ve 90 standardına sokar."""
        temiz = "".join(filter(str.isdigit, str(tel)))
        if temiz.startswith("0") and len(temiz) == 11:
            temiz = "90" + temiz[1:]
        elif len(temiz) == 10 and temiz.startswith("5"):
            temiz = "90" + temiz
        return temiz

    def yaklasan_dersleri_hatirlat(self, simdi):
        """Dersine tam 30 dakika kalan öğrencileri tespit eder ve bildirim atar."""
        hedef_zaman = simdi + dt.timedelta(minutes=30)
        
        gunler = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
        hedef_gun = gunler[hedef_zaman.weekday()]
        hedef_saat = hedef_zaman.strftime("%H:%M") 
        bugun_tarih = simdi.strftime("%Y-%m-%d")

        db = get_db()
        if not db: return

        try:
            dersler = db.collection("dersler").stream()
            for doc in dersler:
                d = doc.to_dict()
                gun = d.get("Gün", "")
                saat_verisi = d.get("Saat", "")
                ogrenci_ad = d.get("Öğrenci", "")
                
                if gun == hedef_gun and hedef_saat in saat_verisi:
                    cache_key = f"{bugun_tarih}_{ogrenci_ad}_{hedef_saat}"
                    
                    if cache_key not in self.hatirlatilan_dersler_cache:
                        print(f"[ALARM] {ogrenci_ad} dersine 30 dakika kaldı! Bildirimler tetikleniyor...")
                        
                        veli_tel, veli_mail = self._veli_iletisim_bilgilerini_al(ogrenci_ad, db)
                        
                        mesaj = (f"Büşra Öğretmen Platformu'ndan Hatırlatma 🔔\n\n"
                                 f"Değerli velimiz, öğrencimiz {ogrenci_ad}'ın dersi 30 dakika sonra ({hedef_saat}) başlayacaktır. "
                                 f"İre dersler dileriz!")
                        
                        threading.Thread(target=self._bildirimleri_gonder, args=(veli_mail, veli_tel, ogrenci_ad, mesaj), daemon=True).start()
                        self.hatirlatilan_dersler_cache.add(cache_key)
        except Exception as e:
            print(f"Hatırlatma tarama hatası: {e}")

    def _veli_iletisim_bilgilerini_al(self, ogrenci_ad, db):
        """DÜZELTME: Firestore alan isimleri popup kayıt mimarisiyle birebir eşitlendi."""
        veli_tel, veli_mail = None, None
        try:
            sorgu = db.collection("ogrenciler").where("Ad Soyad", "==", ogrenci_ad).stream()
            for doc in sorgu:
                veri = doc.to_dict()
                veli_tel = veri.get("Veli Telefonu", veri.get("veli_telefon", None))
                veli_mail = veri.get("Veli Mail", veri.get("veli_eposta", None))
                break
        except Exception as e:
            print(f"İletişim bilgisi çekme hatası: {e}")
        return veli_tel, veli_mail

    def _bildirimleri_gonder(self, mail_adres, tel_no, ogrenci_ad, mesaj):
        """E-Posta ve Green-API üzerinden tamamen arka planda WhatsApp mesajı gönderen motor."""
        # 1. ARKA PLAN E-POSTA MOTORU
        if mail_adres:
            import smtplib
            from email.mime.text import MIMEText
            gonderen_mail = os.getenv("EMAIL_USER", "kurumsal_hesap@gmail.com") 
            gonderen_sifre = os.getenv("EMAIL_PASS", "uygulama_ozel_sifresi")
            try:
                msg = MIMEText(mesaj, 'plain', 'utf-8')
                msg['Subject'] = f"Ders Hatırlatması: {ogrenci_ad}"
                msg['From'] = gonderen_mail
                msg['To'] = mail_adres
                
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(gonderen_mail, gonderen_sifre)
                server.sendmail(gonderen_mail, mail_adres, msg.as_string())
                server.quit()
                print(f"[MAIL BAŞARILI] {ogrenci_ad} hatırlatma maili uçuruldu.")
            except Exception as e:
                print(f"[MAIL HATASI] E-posta gönderilemedi: {e}")

        # 2. GREEN-API WHATSAPP MOTORU (GÜVENLİ VE BAĞIMSIZ MIMARI)
        if tel_no:
            try:
                temiz_tel = self.src_temizle_no(tel_no)
                url = f"https://api.green-api.com/waInstance{self.GREEN_INSTANCE_ID}/sendMessage/{self.GREEN_API_TOKEN}"
                
                payload = {
                    "chatId": f"{temiz_tel}@c.us",
                    "message": mesaj
                }
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"[GREEN-API BAŞARILI] {ogrenci_ad} velisine WhatsApp mesajı sessizce iletildi.")
                else:
                    print(f"[GREEN-API HATASI] Kod: {response.status_code}, Yanıt: {response.text}")
            except Exception as e:
                print(f"[GREEN-API SİSTEM HATASI] Mesaj tetiklenemedi: {e}")

    def whatsapp_rozet_gonder(self, tel_no, dosya_yolu, alt_yazi=""):
        """Green-API ile WhatsApp üzerinden şık tasarımlı rozet/görsel gönderir."""
        if not tel_no or not os.path.exists(dosya_yolu):
            return

        try:
            temiz_tel = self.src_temizle_no(tel_no)
            url = f"https://api.green-api.com/waInstance{self.GREEN_INSTANCE_ID}/sendFileByUpload/{self.GREEN_API_TOKEN}"
            
            payload = {
                'chatId': f"{temiz_tel}@c.us",
                'caption': alt_yazi
            }
            
            with open(dosya_yolu, 'rb') as file:
                files = {'file': (os.path.basename(dosya_yolu), file, 'image/png')}
                response = requests.post(url, data=payload, files=files, timeout=20)
                
            if response.status_code == 200:
                print(f"[ROZET BAŞARILI] {temiz_tel} numarasına şampiyonluk rozeti uçuruldu! 🏆")
            else:
                print(f"[ROZET HATASI] Sunucu yanıtı: {response.text}")
        except Exception as e:
            print(f"[ROZET SİSTEM HATASI] Gönderim çöktü: {e}")

    def tum_ogrencilere_otomatik_rapor_hazirla(self):
        """Tüm öğrencilere AI raporu hazırlar ve haftanın soru şampiyonuna otomatik altın rozet atar."""
        db = get_db()
        if not db: return
        
        en_yuksek_soru = 0
        sampiyon_ad = None
        sampiyon_tel = None
        
        try:
            ogrenciler = db.collection("ogrenciler").stream()
            for doc in ogrenciler:
                data = doc.to_dict()
                ogrenci_ad = data.get("Ad Soyad")
                
                if not ogrenci_ad: continue
                
                print(f"[OTOMASYON] {ogrenci_ad} için veriler analiz ediliyor...")
                
                haftalik_sonuc = self._ogrenci_haftalik_verilerini_topla(ogrenci_ad, db)
                haftalik_veri_ozeti = haftalik_sonuc["metin"]
                cozulen_soru = haftalik_sonuc["soru_sayisi"]
                ogrenci_tel = haftalik_sonuc["telefon"]
                
                if cozulen_soru > en_yuksek_soru:
                    en_yuksek_soru = cozulen_soru
                    sampiyon_ad = ogrenci_ad
                    sampiyon_tel = ogrenci_tel
                
                ai_rapor_metni = self._yapay_zekadan_otomatik_rapor_iste(ogrenci_ad, haftalik_veri_ozeti)
                
                if ai_rapor_metni and hasattr(self, "frame_raporlar"):
                    self.frame_raporlar.rapor_kaydet_ve_eposta_gonder(ogrenci_ad, ai_rapor_metni)
            
            # ==========================================================
            # 🏆 GECE GALA KAPANIŞI: HAFTANIN ŞAMPİYONUNA ROZET UÇURMA
            # ==========================================================
            if sampiyon_ad and en_yuksek_soru > 0 and sampiyon_tel:
                print(f"[MÜJDE] Haftanın Soru Şampiyonu Belirlendi: {sampiyon_ad} ({en_yuksek_soru} Soru!)")
                
                # Projenin kök dizinindeki veya public klasöründeki rozet dosyasını bulur
                current_dir = os.path.dirname(os.path.abspath(__file__))
                rozet_dosya_yolu = os.path.join(current_dir, "rozet_sampiyon.png")
                
                tebrik_mesaji = (
                    f"🏆 HAFTANIN SORU ŞAMPİYONU ÖDÜLÜ! 🏆\n\n"
                    f"Harika bir haberim var canım güzel çocuğum {sampiyon_ad}! 😍\n"
                    f"Bu hafta sistemde yaptığım büyük sayımda, tam {en_yuksek_soru} soru çözerek tüm arkadaşlarını geride bıraktın ve zirveye yerleştin!\n\n"
                    f"Bu muazzam emeğin için seni canıgönülden tebrik ediyor, bu şık 'Altın Soru Şampiyonu' dijital rozetini cebine gönderiyorum. "
                    f"Seninle gurur duyuyorum, hep böyle disiplinli ve azimli devam et tamam mı? Öpüyorum kocaman! 😘🎉"
                )
                
                if os.path.exists(rozet_dosya_yolu):
                    self.whatsapp_rozet_gonder(sampiyon_tel, rozet_dosya_yolu, tebrik_mesaji)
                else:
                    print(f"[SİSTEM UYARISI] {rozet_dosya_yolu} adresinde rozet görseli bulunamadığı için düz metin olarak tebrik ediliyor.")
                    self._bildirimleri_gonder(None, sampiyon_tel, sampiyon_ad, tebrik_mesaji)
                        
        except Exception as e:
            print(f"[OTOMASYON HATASI] Raporlama veya rozet zincirinde hata: {e}")

    def _ogrenci_haftalik_verilerini_topla(self, ogrenci_ad, db):
        """Firestore'dan öğrencinin o haftaki verilerini çeker ve soru sayısını sayısal olarak döndürür."""
        toplam_soru = 0
        son_deneme_neti = "Kayıt Yok"
        ogrenci_tel = None
        
        try:
            sorular = db.collection("soru_takip").where("ogrenci_ad", "==", ogrenci_ad).stream()
            for s in sorular:
                toplam_soru += int(s.to_dict().get("soru_sayisi", 0))
                
            denemeler = db.collection("denemeler").where("ogrenci_ad", "==", ogrenci_ad).stream()
            for d in denemeler:
                son_deneme_neti = d.to_dict().get("toplam_net", son_deneme_neti)
                
            sorgu = db.collection("ogrenciler").where("Ad Soyad", "==", ogrenci_ad).stream()
            for doc in sorgu:
                veri = doc.to_dict()
                # Öncelik öğrencinin kendi telefonunda, yoksa velininkine göndersin
                ogrenci_tel = veri.get("Ogrenci Telefonu", veri.get("Veli Telefonu", None))
                break
        except Exception as e:
            print(f"Veri toplama hatası ({ogrenci_ad}): {e}")
            
        veri_metni = f"Haftalık Çözülen Soru Sayısı: {toplam_soru}, Son Deneme Neti: {son_deneme_neti}"
        return {
            "metin": veri_metni,
            "soru_sayisi": toplam_soru,
            "telefon": ogrenci_tel
        }

    def _ogrenci_verilerini_buluta_guncelle(self, ogrenci_ad, yeni_soru_sayisi, yeni_net):
        """Python masaüstü uygulamasından verileri buluta (Firestore) iter."""
        db = get_db()
        if not db: return

        ogrenci_ref = db.collection("ogrenciler").where("Ad Soyad", "==", ogrenci_ad).get()
        if ogrenci_ref:
            doc = ogrenci_ref[0]
            data = doc.to_dict()
            grafik_verileri = data.get("grafik_verileri", [])
            
            grafik_verileri.append(yeni_soru_sayisi)
            if len(grafik_verileri) > 6:
                grafik_verileri.pop(0)
            
            doc.reference.update({
                "haftalik_toplam_soru": yeni_soru_sayisi,
                "son_deneme_neti": yeni_net,
                "grafik_verileri": grafik_verileri
            })
            print(f"[CLOUD SYNC] {ogrenci_ad} verileri web portalı için güncellendi.")
        else:
            print(f"[HATA] {ogrenci_ad} veritabanında bulunamadı!")

    def _yapay_zekadan_otomatik_rapor_iste(self, ogrenci_ad, haftalik_veri):
        """Google Gemini API'ye bağlanarak tamamen otomatik haftalık yorum üretir."""
        try:
            # Model çağrısı güncellendi
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = (
                f"Sen eğitim koçu Büşra Hoca'nın yapay zeka asistanısın. Öğrencimiz '{ogrenci_ad}' için velisine iletilmek üzere haftalık rapor yazacaksın.\n"
                f"Öğrencinin bu haftaki sistem verileri şöyledir: {haftalik_veri}\n\n"
                f"TALİMAT: Bu verilere dayanarak Büşra Hoca'nın o tatlı, anaç, motive edici ama disiplinli eğitimci üslubuyla 1-2 paragraflık bir veli bilgilendirme raporu oluştur. "
                f"Cümlelerine 'Canım velimiz', 'Güzel çocuğumuz' gibi sıcak ifadeler eklemeyi unutma."
            )
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[AI HATASI] {ogrenci_ad} için Gemini rapor üretemedi: {e}")
            return None

    # --- SESLİ ASİSTAN FONKSİYONLARI ---
    def setup_voice_button(self, parent_frame):
        self.btn_mic = ctk.CTkButton(
            parent_frame, 
            text="📢 Programı Oku",
            fg_color="#D4AF37", 
            text_color="black",
            command=self.oku_ders_programi
        )
        self.btn_mic.grid(row=14, column=0, padx=15, pady=20, sticky="ew")

    def oku_ders_programi(self):
        threading.Thread(target=self._sesli_okuma_islemi, daemon=True).start()

    def _sesli_okuma_islemi(self):
        import pygame
        from gtts import gTTS
        
        db = get_db()
        try:
            dersler = list(db.collection("dersler").stream())
            if not dersler:
                cevap = "Şu an kayıtlı bir ders programı görünmüyor hocam."
            else:
                cevap = "Haftalık ders programın şöyle: "
                for doc in dersler:
                    d = doc.to_dict()
                    ogrenci = d.get("Öğrenci", "Bilinmeyen")
                    gun = d.get("Gün", "Belirtilmemiş")
                    saat = d.get("Saat", "Belirtilmemiş")
                    
                    if "-" in saat:
                        saat = saat.split("-")[0].strip()
                        
                    cevap += f"{gun} günü saat {saat}'te {ogrenci} ile dersin var. "
            
            tts = gTTS(text=cevap, lang='tr', slow=False)
            dosya_adi = "gecici_ses.mp3"
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
            print(f"Okuma hatası: {e}")

    # --- ARAYÜZ VE MENÜ FONKSİYONLARI ---
    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "logo.png") 

        try:
            logo_img = Image.open(logo_path)
            self.logo_image = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(180, 90))
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_image)
        except Exception:
            self.logo_label = ctk.CTkLabel(
                self.sidebar_frame, text="BV\nÖĞRENME PLATFORMU", 
                font=ctk.CTkFont(family="Georgia", size=22, weight="bold"),
                text_color=COLOR_TEXT_LIGHT, justify="center"
            )
            
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 5))
        
        self.logo_line = ctk.CTkFrame(self.sidebar_frame, height=2, width=180, fg_color=COLOR_ACCENT_GOLD)
        self.logo_line.grid(row=1, column=0, pady=(0, 20))

        self.btn_kwargs = {
            "font": ctk.CTkFont(size=13, weight="bold"),
            "text_color": COLOR_TEXT_LIGHT,
            "fg_color": "transparent",
            "hover_color": COLOR_SIDEBAR_HOVER,
            "anchor": "w",
            "height": 34,
            "corner_radius": 8
        }

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Ana Sayfa", command=self.show_dashboard, **self.btn_kwargs)
        self.btn_dashboard.grid(row=2, column=0, padx=15, pady=1, sticky="ew")

        self.btn_ajanda = ctk.CTkButton(self.sidebar_frame, text="Kişisel Ajanda", command=self.show_ajanda, **self.btn_kwargs)
        self.btn_ajanda.grid(row=3, column=0, padx=15, pady=1, sticky="ew")

        self.btn_student_parent = ctk.CTkButton(self.sidebar_frame, text="Öğrenciler    ▼", command=self.toggle_student_menu, **self.btn_kwargs)
        self.btn_student_parent.grid(row=4, column=0, padx=15, pady=1, sticky="ew")

        self.student_submenu_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        
        sub_btn_kwargs = self.btn_kwargs.copy()
        sub_btn_kwargs.update({"font": ctk.CTkFont(size=12, weight="normal"), "height": 30})

        self.btn_ogrenciler = ctk.CTkButton(self.student_submenu_frame, text="      Öğrenci Listesi", command=self.show_ogrenciler, **sub_btn_kwargs)
        self.btn_ogrenciler.pack(fill="x", padx=5)

        self.btn_akademik = ctk.CTkButton(self.student_submenu_frame, text="      Akademik Takip", command=self.show_akademik, **sub_btn_kwargs)
        self.btn_akademik.pack(fill="x", padx=5)

        self.btn_odevler = ctk.CTkButton(self.student_submenu_frame, text="      Ödev Takibi", command=self.show_odevler, **sub_btn_kwargs)
        self.btn_odevler.pack(fill="x", padx=5)

        self.btn_konu_takip = ctk.CTkButton(self.student_submenu_frame, text="      Konu Takibi", command=self.show_konu_takip, **sub_btn_kwargs)
        self.btn_konu_takip.pack(fill="x", padx=5)

        self.btn_soru_takip = ctk.CTkButton(self.student_submenu_frame, text="      Soru Çözüm Takibi", command=self.show_soru_takip, **sub_btn_kwargs)
        self.btn_soru_takip.pack(fill="x", padx=5)

        self.btn_denemeler = ctk.CTkButton(self.student_submenu_frame, text="      Deneme Takibi", command=self.show_denemeler, **sub_btn_kwargs)
        self.btn_denemeler.pack(fill="x", padx=5)

        self.btn_hata_telafi = ctk.CTkButton(self.student_submenu_frame, text="      Hata Telafi Üretici", command=self.show_hata_telafi, **sub_btn_kwargs)
        self.btn_hata_telafi.pack(fill="x", padx=5)

        self.btn_rozetler = ctk.CTkButton(self.student_submenu_frame, text="      Başarı Rozetleri", command=self.show_rozetler, **sub_btn_kwargs)
        self.btn_rozetler.pack(fill="x", padx=5)

        self.btn_raporlar = ctk.CTkButton(self.student_submenu_frame, text="      Veli Raporları", command=self.show_raporlar, **sub_btn_kwargs)
        self.btn_raporlar.pack(fill="x", padx=5)

        self.btn_dersler_parent = ctk.CTkButton(self.sidebar_frame, text="Ders Programı    ▼", command=self.toggle_dersler_menu, **self.btn_kwargs)
        self.btn_dersler_parent.grid(row=6, column=0, padx=15, pady=1, sticky="ew")

        self.dersler_submenu_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")

        self.btn_ders_takibi = ctk.CTkButton(self.dersler_submenu_frame, text="      Ders Takibi", command=self.show_dersler, **sub_btn_kwargs)
        self.btn_ders_takibi.pack(fill="x", padx=5)

        self.btn_program = ctk.CTkButton(self.dersler_submenu_frame, text="      AI Çalışma Programı", command=self.show_program, **sub_btn_kwargs)
        self.btn_program.pack(fill="x", padx=5)

        self.btn_yoklama = ctk.CTkButton(self.dersler_submenu_frame, text="      Yoklama Takibi", command=self.show_yoklama, **sub_btn_kwargs)
        self.btn_yoklama.pack(fill="x", padx=5)

        self.btn_asistan = ctk.CTkButton(self.sidebar_frame, text="Büşra Hoca AI", command=self.show_asistan, **self.btn_kwargs)
        self.btn_asistan.grid(row=8, column=0, padx=15, pady=1, sticky="ew")

        self.btn_mufredat = ctk.CTkButton(self.sidebar_frame, text="Müfredat Bilgisi", command=self.show_mufredat, **self.btn_kwargs)
        self.btn_mufredat.grid(row=9, column=0, padx=15, pady=1, sticky="ew")
        
        self.btn_ai_soru = ctk.CTkButton(self.sidebar_frame, text="AI Soru Bankası", command=self.show_ai_soru, **self.btn_kwargs)
        self.btn_ai_soru.grid(row=10, column=0, padx=15, pady=1, sticky="ew")

        self.btn_kaynaklar = ctk.CTkButton(self.sidebar_frame, text="Kaynak Kütüphanesi", command=self.show_kaynaklar, **self.btn_kwargs)
        self.btn_kaynaklar.grid(row=11, column=0, padx=15, pady=1, sticky="ew")

        self.btn_muhasebe = ctk.CTkButton(self.sidebar_frame, text="Muhasebe", command=self.show_muhasebe, **self.btn_kwargs)
        self.btn_muhasebe.grid(row=12, column=0, padx=15, pady=1, sticky="ew")

        self.setup_voice_button(self.sidebar_frame)
        self.sidebar_frame.grid_rowconfigure(13, weight=1)

    def toggle_student_menu(self):
        if self.student_menu_open:
            self.student_submenu_frame.grid_forget()
            self.btn_student_parent.configure(text="Öğrenciler    ▼")
            self.student_menu_open = False
        else:
            self.student_submenu_frame.grid(row=5, column=0, sticky="ew", padx=15)
            self.btn_student_parent.configure(text="Öğrenciler    ▲")
            self.student_menu_open = True

    def toggle_dersler_menu(self):
        if self.dersler_menu_open:
            self.dersler_submenu_frame.grid_forget()
            self.btn_dersler_parent.configure(text="Ders Programı    ▼")
            self.dersler_menu_open = False
        else:
            self.dersler_submenu_frame.grid(row=7, column=0, sticky="ew", padx=15)
            self.btn_dersler_parent.configure(text="Ders Programı    ▲")
            self.dersler_menu_open = True

    def create_main_frames(self):
        frame_kwargs = {"corner_radius": 0, "fg_color": "transparent"}

        self.frame_dashboard = ctk.CTkFrame(self, **frame_kwargs)
        self.build_dashboard()

        self.frame_ajanda = AjandaView(self, **frame_kwargs)
        self.frame_ogrenciler = OgrencilerView(self, **frame_kwargs)
        self.frame_dersler = DerslerView(self, **frame_kwargs)
        self.frame_akademik = AkademikView(self, **frame_kwargs)
        self.frame_program = ProgramView(self, **frame_kwargs)
        self.frame_odevler = OdevlerView(self, **frame_kwargs)
        self.frame_konu_takip = KonuTakipView(self, **frame_kwargs)
        self.frame_soru_takip = SoruTakipView(self, **frame_kwargs)
        self.frame_hata_telafi = HataTelafiView(self, **frame_kwargs)
        self.frame_denemeler = DenemelerView(self, **frame_kwargs)
        self.frame_yoklama = YoklamaView(self, **frame_kwargs)
        self.frame_rozetler = RozetlerView(self, **frame_kwargs)
        self.frame_asistan = AsistanView(self, **frame_kwargs)
        self.frame_mufredat = MufredatView(self, **frame_kwargs)
        self.frame_ai_soru = AISoruView(self, **frame_kwargs)
        self.frame_kaynaklar = KaynaklarView(self, **frame_kwargs)
        self.frame_raporlar = RaporView(self, **frame_kwargs)
        self.frame_muhasebe = MuhasebeView(self, **frame_kwargs)

    def select_frame_by_name(self, name):
        buttons = {
            "dashboard": self.btn_dashboard, "ajanda": self.btn_ajanda, "ogrenciler": self.btn_ogrenciler,
            "dersler": self.btn_ders_takibi, "akademik": self.btn_akademik, "program": self.btn_program,
            "odevler": self.btn_odevler, "konu_takip": self.btn_konu_takip, "soru_takip": self.btn_soru_takip, 
            "hata_telafi": self.btn_hata_telafi, "denemeler": self.btn_denemeler, "yoklama": self.btn_yoklama, 
            "rozetler": self.btn_rozetler, "asistan": self.btn_asistan, "mufredat": self.btn_mufredat, 
            "ai_soru": self.btn_ai_soru, "kaynaklar": self.btn_kaynaklar, "raporlar": self.btn_raporlar, 
            "muhasebe": self.btn_muhasebe
        }
        
        for key, btn in buttons.items():
            if btn:
                if name == key:
                    btn.configure(fg_color=COLOR_SIDEBAR_HOVER, text_color=COLOR_ACCENT_GOLD if name in ["dashboard", "ajanda", "muhasebe"] else COLOR_TEXT_LIGHT)
                else:
                    btn.configure(fg_color="transparent", text_color=COLOR_TEXT_LIGHT)

        frames = {
            "dashboard": self.frame_dashboard, "ajanda": self.frame_ajanda, "ogrenciler": self.frame_ogrenciler,
            "dersler": self.frame_dersler, "akademik": self.frame_akademik, "program": self.frame_program,
            "odevler": self.frame_odevler, "konu_takip": self.frame_konu_takip, "soru_takip": self.frame_soru_takip, 
            "hata_telafi": self.frame_hata_telafi, "denemeler": self.frame_denemeler, "yoklama": self.frame_yoklama, 
            "rozetler": self.frame_rozetler, "asistan": self.frame_asistan, "mufredat": self.frame_mufredat, 
            "ai_soru": self.frame_ai_soru, "kaynaklar": self.frame_kaynaklar, "raporlar": self.frame_raporlar, 
            "muhasebe": self.frame_muhasebe
        }

        for key, frame in frames.items():
            if key == name:
                frame.grid(row=0, column=1, sticky="nsew")
                if hasattr(frame, "listeyi_yenile"): frame.listeyi_yenile()
                if hasattr(frame, "verileri_buluttan_cek"): frame.verileri_buluttan_cek()
                if name == "dashboard": self.guncelle_ana_sayfa()
            else:
                frame.grid_forget()

    def build_dashboard(self):
        self.frame_dashboard.grid_columnconfigure(0, weight=1)
        self.frame_dashboard.grid_rowconfigure(4, weight=1)
        
        lbl_welcome = ctk.CTkLabel(self.frame_dashboard, text="Hoş Geldiniz, Büşra Hanım", 
                                   font=ctk.CTkFont(family="Georgia", size=26, weight="bold"), text_color=COLOR_TEXT_DARK)
        lbl_welcome.pack(pady=(40, 20))
        
        self.stats_container = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=40)
        self.stats_container.grid_columnconfigure((0, 1, 2), weight=1)

        def create_card(title, value, color, col):
            card = ctk.CTkFrame(self.stats_container, fg_color="white", corner_radius=15, border_width=1, border_color="#E0E0E0")
            card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(15, 0))
            lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=color)
            lbl_val.pack(pady=(5, 15))
            return lbl_val

        self.lbl_stat_students = create_card("Toplam Öğrenci", "0", COLOR_SIDEBAR, 0)
        self.lbl_stat_lessons = create_card("Haftalık Ders", "0", COLOR_ACCENT_GOLD, 1)
        self.lbl_stat_payments = create_card("Bekleyen Ödemeler", "0", "#D32F2F", 2)

        self.counter_frame = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent")
        self.counter_frame.pack(fill="x", padx=40, pady=20)
        self.counter_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_lgs = ctk.CTkLabel(self.counter_frame, text="LGS'ye Kalan: -- Gün", font=ctk.CTkFont(size=16, weight="bold"), 
                                    fg_color="#E65100", text_color="white", corner_radius=10, height=50)
        self.lbl_lgs.grid(row=0, column=0, padx=10, sticky="ew")

        self.lbl_yks = ctk.CTkLabel(self.counter_frame, text="YKS'ye Kalan: -- Gün", font=ctk.CTkFont(size=16, weight="bold"), 
                                    fg_color="#0277BD", text_color="white", corner_radius=10, height=50)
        self.lbl_yks.grid(row=0, column=1, padx=10, sticky="ew")

        takvim_header = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent")
        takvim_header.pack(fill="x", padx=40, pady=(10, 5))
        
        lbl_takvim_title = ctk.CTkLabel(takvim_header, text="Bu Haftaki Programım", font=ctk.CTkFont(family="Georgia", size=22, weight="bold"), text_color=COLOR_TEXT_DARK)
        lbl_takvim_title.pack(side="left")
        
        line_takvim = ctk.CTkFrame(takvim_header, height=2, fg_color=COLOR_ACCENT_GOLD)
        line_takvim.pack(side="left", fill="x", expand=True, padx=(15, 0))

        self.takvim_frame = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent")
        self.takvim_frame.pack(fill="both", expand=True, padx=30, pady=10)
        self.takvim_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

    def guncelle_ana_sayfa(self):
        try:
            if hasattr(self.frame_ogrenciler, "ogrenci_listesi"):
                self.lbl_stat_students.configure(text=str(len(self.frame_ogrenciler.ogrenci_listesi)))
            
            bugun = dt.date.today()
            lgs_tarih = dt.date(bugun.year if bugun.month < 6 else bugun.year + 1, 6, 13)
            yks_tarih = dt.date(bugun.year if bugun.month < 6 else bugun.year + 1, 6, 20)
            
            self.lbl_lgs.configure(text=f"⏳ LGS'ye Kalan: {(lgs_tarih - bugun).days} Gün")
            self.lbl_yks.configure(text=f"⏳ YKS'ye Kalan: {(yks_tarih - bugun).days} Gün")

            for widget in self.takvim_frame.winfo_children(): widget.destroy()
            
            gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            kisa_gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
            
            bu_hafta_iso = bugun.strftime("%G-W%V")
            dersler = []
            if hasattr(self.frame_dersler, "ders_listesi"):
                dersler = self.frame_dersler.ders_listesi

            haftalik_ders_sayisi = 0

            for i, gun in enumerate(gunler):
                day_card = ctk.CTkFrame(self.takvim_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
                day_card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                
                is_today = (bugun.weekday() == i)
                header_bg = COLOR_SIDEBAR if is_today else "#F4F1EA"
                header_fg = "white" if is_today else COLOR_TEXT_DARK
                
                day_header = ctk.CTkFrame(day_card, fg_color=header_bg, corner_radius=8, height=35)
                day_header.pack(fill="x", padx=5, pady=5)
                day_header.pack_propagate(False)
                
                ctk.CTkLabel(day_header, text=kisa_gunler[i], font=ctk.CTkFont(weight="bold"), text_color=header_fg).pack(expand=True)
                
                gunluk_dersler = []
                for d in dersler:
                    if d.get("yil_hafta") == bu_hafta_iso:
                        if d.get("Gün") == gun or gun in d.get("Gün ve Saat", ""):
                            saat = d.get("Saat", d.get("saat", "Belirsiz Saat"))
                            
                            if ":" in saat and "-" not in saat and len(saat) < 5: 
                                lines = d.get("Gün ve Saat", "").split("\n")
                                for line in lines:
                                    if gun in line: saat = line.split(":")[-1].strip()

                            gunluk_dersler.append((saat, d.get("Öğrenci"), d.get("Ders Adı")))
                            haftalik_ders_sayisi += 1

                if not gunluk_dersler:
                    ctk.CTkLabel(day_card, text="Ders Yok", font=ctk.CTkFont(size=10, slant="italic"), text_color="gray").pack(pady=20)
                else:
                    for saat, ogr, ders_adi in sorted(gunluk_dersler):
                        lesson_box = ctk.CTkFrame(day_card, fg_color="#F9F9F9", corner_radius=6)
                        lesson_box.pack(fill="x", padx=5, pady=2)
                        
                        ctk.CTkLabel(lesson_box, text=saat, font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_ACCENT_GOLD).pack(anchor="w", padx=5, pady=(2,0))
                        ctk.CTkLabel(lesson_box, text=ogr, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_DARK).pack(anchor="w", padx=5)
                        ctk.CTkLabel(lesson_box, text=ders_adi, font=ctk.CTkFont(size=9), text_color="gray").pack(anchor="w", padx=5, pady=(0,2))

            self.lbl_stat_lessons.configure(text=str(haftalik_ders_sayisi))

        except Exception as e: 
            print(f"Dashboard güncelleme hatası: {e}")

    # --- Sayfa Gösterim Fonksiyonları ---
    def show_dashboard(self): self.select_frame_by_name("dashboard")
    def show_ajanda(self): self.select_frame_by_name("ajanda")
    def show_ogrenciler(self): self.select_frame_by_name("ogrenciler")
    def show_dersler(self): self.select_frame_by_name("dersler")
    def show_akademik(self): self.select_frame_by_name("akademik")
    def show_program(self): self.select_frame_by_name("program")
    def show_odevler(self): self.select_frame_by_name("odevler")
    def show_konu_takip(self): self.select_frame_by_name("konu_takip")
    def show_soru_takip(self): self.select_frame_by_name("soru_takip")
    def show_hata_telafi(self): self.select_frame_by_name("hata_telafi")
    def show_denemeler(self): self.select_frame_by_name("denemeler")
    def show_yoklama(self): self.select_frame_by_name("yoklama")
    def show_rozetler(self): self.select_frame_by_name("rozetler")
    def show_asistan(self): self.select_frame_by_name("asistan")
    def show_mufredat(self): self.select_frame_by_name("mufredat")
    def show_ai_soru(self): self.select_frame_by_name("ai_soru")
    def show_kaynaklar(self): self.select_frame_by_name("kaynaklar")
    def show_raporlar(self): self.select_frame_by_name("raporlar")
    def show_muhasebe(self): self.select_frame_by_name("muhasebe")

if __name__ == "__main__":
    app = App()
    app.mainloop()