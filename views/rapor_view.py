import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import get_db
from datetime import datetime

# ReportLab Şık PDF Bileşenleri
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class RaporView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db = get_db()
        self.COLOR_SIDEBAR = "#044D29"
        self.BASE_DRIVE_PATH = r"G:\Drive'ım\Haftalık Raporlar"
        
        if not os.path.exists(self.BASE_DRIVE_PATH):
            try: os.makedirs(self.BASE_DRIVE_PATH)
            except: pass

        self.secili_dosya_yolu = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.arayuz_olustur()
        
    def arayuz_olustur(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(header_frame, text="Haftalık Veli Raporları Merkezi", font=ctk.CTkFont(size=24, weight="bold"), text_color="#1A1A1A").pack(side="left")
        
        self.btn_ac = ctk.CTkButton(header_frame, text="📁 PDF RAPORU AÇ", fg_color="#D4AF37", text_color="black", font=ctk.CTkFont(weight="bold"), command=self.raporu_ac)
        self.btn_ac.pack(side="right", padx=10)
        
        self.btn_yeni = ctk.CTkButton(header_frame, text="➕ YENİ RAPOR ÜRET", fg_color=self.COLOR_SIDEBAR, text_color="white", font=ctk.CTkFont(weight="bold"), command=self.ac_yeni_rapor_popup)
        self.btn_yeni.pack(side="right")
        
        self.baslik_frame = ctk.CTkFrame(self, fg_color=self.COLOR_SIDEBAR, corner_radius=10)
        self.baslik_frame.grid(row=1, column=0, padx=40, pady=(0, 10), sticky="ew")
        self.baslik_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(self.baslik_frame, text="Öğrenci Adı", font=ctk.CTkFont(weight="bold"), text_color="white").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        ctk.CTkLabel(self.baslik_frame, text="Rapor Tarihi", font=ctk.CTkFont(weight="bold"), text_color="white").grid(row=0, column=1, padx=20, pady=10, sticky="w")
        ctk.CTkLabel(self.baslik_frame, text="Dosya Türü", font=ctk.CTkFont(weight="bold"), text_color="white").grid(row=0, column=2, padx=20, pady=10, sticky="w")

        self.liste_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.liste_frame.grid(row=2, column=0, padx=40, pady=(0, 40), sticky="nsew")
        
        self.verileri_buluttan_cek()

    def verileri_buluttan_cek(self):
        for w in self.liste_frame.winfo_children(): w.destroy()
        if not os.path.exists(self.BASE_DRIVE_PATH): return

        kayit_bulundu = False
        try:
            for ogrenci_klasor in sorted(os.listdir(self.BASE_DRIVE_PATH)):
                klasor_yolu = os.path.join(self.BASE_DRIVE_PATH, ogrenci_klasor)
                if os.path.isdir(klasor_yolu):
                    for dosya in sorted(os.listdir(klasor_yolu), reverse=True):
                        if dosya.endswith(".pdf"):
                            kayit_bulundu = True
                            dosya_tam_yolu = os.path.join(klasor_yolu, dosya)
                            rapor_tarihi = dosya.replace("Rapor_", "").replace(".pdf", "")
                            
                            satir = ctk.CTkFrame(self.liste_frame, fg_color="transparent")
                            satir.pack(fill="x", pady=2, padx=5)
                            satir.grid_columnconfigure((0, 1, 2), weight=1)
                            
                            satir.bind("<Button-1>", lambda e, p=dosya_tam_yolu, s=satir: self.satir_sec(p, s))
                            satir.bind("<Double-Button-1>", lambda e, p=dosya_tam_yolu: self.raporu_dogrudan_ac(p))
                            
                            lbl_ogr = ctk.CTkLabel(satir, text=ogrenci_klasor)
                            lbl_ogr.grid(row=0, column=0, padx=20, sticky="w")
                            
                            lbl_tar = ctk.CTkLabel(satir, text=rapor_tarihi)
                            lbl_tar.grid(row=0, column=1, padx=20, sticky="w")
                            
                            lbl_yol = ctk.CTkLabel(satir, text="PDF Belgesi 📄", text_color="#044D29", font=ctk.CTkFont(size=11, weight="bold"))
                            lbl_yol.grid(row=0, column=2, padx=20, sticky="w")
        except Exception as e: print(f"Dizin tarama hatası: {e}")

        if not kayit_bulundu:
            ctk.CTkLabel(self.liste_frame, text="Kayıtlı haftalık PDF gelişim raporu bulunamadı.", text_color="gray").pack(pady=20)

    def satir_sec(self, dosya_yolu, satir_frame):
        self.secili_dosya_yolu = dosya_yolu
        for w in self.liste_frame.winfo_children(): w.configure(fg_color="transparent")
        satir_frame.configure(fg_color="#E8F5E9")

    def raporu_ac(self):
        if not self.secili_dosya_yolu:
            messagebox.showwarning("Uyarı", "Lütfen listeden bir PDF raporu seçin.")
            return
        self.raporu_dogrudan_ac(self.secili_dosya_yolu)

    def raporu_dogrudan_ac(self, dosya_yolu):
        try: os.startfile(dosya_yolu)
        except Exception as e: messagebox.showerror("Hata", f"Dosya açılamadı: {e}")

    def ac_yeni_rapor_popup(self):
        ogrenci_isimleri = ["(Öğrenci Seçin)"]
        if hasattr(self.master, "frame_ogrenciler"):
            ogrenci_isimleri = [ogr.get("Ad Soyad") for ogr in self.master.frame_ogrenciler.ogrenci_listesi]
            
        popup = ctk.CTkToplevel(self)
        popup.title("Şık PDF Rapor Sihirbazı")
        popup.geometry("520x560")
        popup.attributes("-topmost", True)
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="Öğrenci Seçin:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 2))
        cmb_ogr = ctk.CTkOptionMenu(popup, values=ogrenci_isimleri, fg_color="#F4F1EA", text_color="black", button_color=self.COLOR_SIDEBAR, width=320)
        cmb_ogr.pack(pady=5)
        
        ctk.CTkLabel(popup, text="Haftalık Analiz Rapor İçeriği:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 2))
        txt_rapor = ctk.CTkTextbox(popup, width=460, height=290, fg_color="#F4F1EA", font=ctk.CTkFont(size=13))
        txt_rapor.pack(pady=5)
        
        def islemi_tetikle():
            secilen_ogr = cmb_ogr.get()
            icerik = txt_rapor.get("0.0", "end").strip()
            if secilen_ogr == "(Öğrenci Seçin)" or not icerik: return
            popup.destroy()
            threading.Thread(target=self.rapor_kaydet_ve_eposta_gonder, args=(secilen_ogr, icerik), daemon=True).start()

        ctk.CTkButton(popup, text="📄 ŞIK PDF ÜRET VE DAĞIT", fg_color=self.COLOR_SIDEBAR, height=42, font=ctk.CTkFont(weight="bold"), command=islemi_tetikle).pack(pady=20)

    def rapor_kaydet_ve_eposta_gonder(self, ogrenci_ad, icerik):
        tarih_str = datetime.now().strftime("%d.%m.%Y")
        ogr_klasor_yolu = os.path.join(self.BASE_DRIVE_PATH, ogrenci_ad)
        if not os.path.exists(ogr_klasor_yolu): os.makedirs(ogr_klasor_yolu)
            
        tam_dosya_yolu = os.path.join(ogr_klasor_yolu, f"Rapor_{tarih_str}.pdf")
        
        # --- REPORTLAB İLE ŞIK PDF ÜRETİM MOTORU (TÜRKÇE KARAKTER DESTEKLİ) ---
        try:
            # Windows Sistem Yazı Tiplerini Kaydet (ı, ş, ğ, ç karakterleri için zorunlu)
            pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
            font_family, font_bold = 'Arial', 'Arial-Bold'
        except:
            font_family, font_bold = 'Helvetica', 'Helvetica-Bold'
            
        try:
            doc = SimpleDocTemplate(tam_dosya_yolu, pagesize=a4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
            story = []
            
            # Kurumsal Stiller
            style_title = ParagraphStyle('Title', fontName=font_bold, fontSize=20, textColor=colors.HexColor('#044D29'), alignment=1, spaceAfter=15)
            style_meta = ParagraphStyle('Meta', fontName=font_family, fontSize=11, textColor=colors.HexColor('#2C3E50'), spaceAfter=6)
            style_body = ParagraphStyle('Body', fontName=font_family, fontSize=12, textColor=colors.HexColor('#1A1A1A'), leading=20, spaceBefore=15)
            style_footer = ParagraphStyle('Footer', fontName=font_family, fontSize=9, textColor=colors.gray, alignment=1, spaceBefore=40)
            
            # PDF İçerik Yapısı
            story.append(Paragraph("<b>HAFTALIK AKADEMİK GELİŞİM RAPORU</b>", style_title))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#D4AF37'), spaceAfter=15)) # Altın çizgi
            
            story.append(Paragraph(f"<b>Öğrenci Adı Soyadı:</b> {ogrenci_ad}", style_meta))
            story.append(Paragraph(f"<b>Rapor Tarihi:</b> {tarih_str}", style_meta))
            story.append(Paragraph("<b>Eğitim Koçu:</b> Büşra Hoca Gelişim Platformu", style_meta))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E0E0E0'), spaceBefore=10, spaceAfter=10))
            
            # --- MEVCUT İÇERİK KISMI ---
            icerik_html = icerik.replace("\n", "<br/>")
            story.append(Paragraph(icerik_html, style_body))
            
            story.append(Spacer(1, 30))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=15))
            
            # ==========================================
            # DİJİTAL İMZA / PARAF ENTEGRASYONU
            # ==========================================
            # İmza dosyasının yolunu belirliyoruz (main.py ile aynı dizinde olduğunu varsayıyoruz)
            imza_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "busra_imza.png")
            
            # Eğer logo/imza dosyası varsa onu ekle
            if os.path.exists(imza_yolu):
                imza_gorseli = RLImage(imza_yolu, width=140, height=70) # Boyutları tasarımına göre ayarlayabilirsin
                imza_gorseli.hAlign = 'RIGHT' # İmzayı sağ alt köşeye hizala
                story.append(imza_gorseli)
                
                # Resmin hemen altına unvanı ekle
                style_unvan = ParagraphStyle('Unvan', fontName=font_bold, fontSize=10, textColor=colors.HexColor('#044D29'), alignment=2)
                story.append(Paragraph("Büşra Özdoğan Aktulay<br/>Matematik Öğretmeni", style_unvan))
            else:
                # Dosya bulunamazsa (veya silinirse) şık bir yedek metin imzası at
                style_yedek_imza = ParagraphStyle('Imza', fontName=font_bold, fontSize=12, textColor=colors.HexColor('#D4AF37'), alignment=2)
                story.append(Paragraph("Büşra Özdoğan Aktulay<br/>Matematik Öğretmeni", style_yedek_imza))

            story.append(Spacer(1, 10))
            
            # Sistemin fütüristik yapısını belli eden alt bilgi
            story.append(Paragraph("Bu gelişim raporu BV Öğrenme Platformu Yapay Zeka Modülü tarafından Büşra Hoca'nın yönergeleriyle hazırlanmıştır.", style_footer))
            
            doc.build(story)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("PDF Hatası", f"PDF dosyası oluşturulamadı: {e}"))
            return

        # 3. Firestore Veritabanından Veli Mailini Çek
        veli_eposta = None
        if self.db:
            try:
                sorgu = self.db.collection("ogrenciler").where("Ad Soyad", "==", ogrenci_ad).stream()
                for doc in sorgu:
                    veli_eposta = doc.to_dict().get("veli_eposta")
                    break
            except: pass

        # 4. ÇİFT TARAFLI E-POSTA MOTORU (Veliye ve Büşra Hoca'ya)
        self.eposta_gonder_motoru(veli_eposta, ogrenci_ad, tam_dosya_yolu, tarih_str)

    def eposta_gonder_motoru(self, veli_mail, ogrenci_ad, dosya_yolu, tarih):
        gonderen_mail = os.getenv("EMAIL_USER", "kurumsal_hesap@gmail.com") 
        gonderen_sifre = os.getenv("EMAIL_PASS", "uygulama_ozel_sifresi") 
        
        # Alıcılar listesine hem veliyi hem de hocanın kendisini ekliyoruz
        alici_listesi = [gonderen_mail]
        if veli_mail:
            alici_listesi.append(veli_mail)
            
        msg = MIMEMultipart()
        msg['From'] = gonderen_mail
        msg['To'] = ", ".join(alici_listesi)
        msg['Subject'] = f"{ogrenci_ad} - Haftalık Akademik Gelişim PDF Raporu ({tarih})"
        
        govde = f"Sayın Velimiz ve Değerli Hocamız,\n\nÖğrencimiz {ogrenci_ad} için hazırlanan {tarih} tarihli haftalık akademik gelişim, performans ve analiz raporu ekte şık bir PDF belgesi olarak bilginize sunulmuştur.\n\nEğitim Platformu Otomasyon Sistemi."
        msg.attach(MIMEText(govde, 'plain', 'utf-8'))
        
        try:
            with open(dosya_yolu, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(dosya_yolu)}")
                msg.attach(part)
                
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(gonderen_mail, gonderen_sifre)
            server.sendmail(gonderen_mail, alici_listesi, msg.as_string())
            server.quit()
            
            self.after(0, lambda: messagebox.showinfo("Başarılı", "Şık PDF raporu başarıyla üretildi, Drive'a senkronize edildi, hocaya ve veliye e-posta ile ulaştırıldı."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("E-Posta Hatası", f"PDF üretildi fakat mail gönderilemedi:\n{e}"))
        
        self.after(0, self.verileri_buluttan_cek)