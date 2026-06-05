import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as messagebox
from database import get_db
import threading
import os
import re
import webbrowser
import urllib.parse
from datetime import datetime

# PDF, Görselleştirme, Tablo ve Yazıcı Modülleri
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    import fitz  
    from PIL import Image, ImageTk
except ImportError:
    fitz = None

try:
    import win32print
    import win32api
except ImportError:
    win32print = None

try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    PDF_FONT = 'Arial'
except Exception:
    PDF_FONT = 'Helvetica'


# ------------------------------------------------------------------
# AI SORU BANKASI PDF ÖN İZLEME PENCERESİ
# ------------------------------------------------------------------
class SoruPreviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, pdf_path, content_text, test_title, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(f"📄 Test Ön İzleme & Yazdır - {test_title}")
        self.geometry("750x850")
        self.minsize(650, 750)
        
        self.pdf_path = pdf_path
        self.content_text = content_text
        self.test_title = test_title
        
        self.after(200, self.lift)
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.arayuz_tasarla()
        self.pdf_sayfalarini_yukle()

    def arayuz_tasarla(self):
        self.toolbar = ctk.CTkFrame(self, height=60, fg_color="#F5F5F5", corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        ctk.CTkLabel(self.toolbar, text="🖨️ Yazıcı:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#1A1A1A").pack(side="left", padx=(15, 5))
        
        yazici_listesi = ["Varsayılan Yazıcı"]
        if win32print:
            try:
                yazicilar = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                yazici_listesi = [printer[2] for printer in yazicilar]
            except Exception:
                pass
                
        self.cmb_yazici = ctk.CTkOptionMenu(self.toolbar, values=yazici_listesi, width=200, fg_color="white", text_color="black", button_color="#044D29", button_hover_color="#03361D")
        self.cmb_yazici.pack(side="left", padx=5)
        
        self.btn_yazdir = ctk.CTkButton(self.toolbar, text="Yazdır", fg_color="#044D29", hover_color="#03361D", width=80, font=ctk.CTkFont(weight="bold"), command=self.pdf_yazdir)
        self.btn_yazdir.pack(side="left", padx=5)
        
        self.btn_whatsapp = ctk.CTkButton(self.toolbar, text="WhatsApp ile Paylaş", fg_color="#25D366", hover_color="#20BA56", text_color="white", font=ctk.CTkFont(weight="bold"), command=self.whatsapp_ile_gonder)
        self.btn_whatsapp.pack(side="right", padx=15)

        self.preview_scroll = ctk.CTkScrollableFrame(self, fg_color="gray30", corner_radius=0)
        self.preview_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def pdf_sayfalarini_yukle(self):
        if not fitz:
            lbl_err = ctk.CTkLabel(self.preview_scroll, text="Ön izleme bileşeni eksik.\npip install pymupdf", text_color="white")
            lbl_err.pack(pady=40)
            return

        try:
            doc = fitz.open(self.pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=120)
                img_data = pix.tobytes("ppm")
                
                img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
                img_tk = ImageTk.PhotoImage(img)
                
                lbl_page = ctk.CTkLabel(self.preview_scroll, image=img_tk, text="")
                lbl_page.image = img_tk 
                lbl_page.pack(pady=15, padx=20)
        except Exception as e:
            messagebox.showerror("Ön İzleme Hatası", f"PDF yüklenirken hata oluştu: {str(e)}")

    def pdf_yazdir(self):
        secili_yazici = self.cmb_yazici.get()
        if not win32print:
            messagebox.showwarning("Yazdırma Hatası", "Yazıcı modülleri eksik.")
            return
        try:
            win32print.SetDefaultPrinter(secili_yazici)
            win32api.ShellExecute(0, "print", self.pdf_path, None, ".", 0)
        except Exception as e:
            messagebox.showerror("Yazdırma Hatası", f"Yazıcıya gönderilirken hata oluştu: {str(e)}")

    def whatsapp_ile_gonder(self):
        try:
            mesaj_temiz = re.sub(r'[*_#]', '', self.content_text)
            kodlanmis_metin = urllib.parse.quote(mesaj_temiz)
            wa_url = f"whatsapp://send?text={kodlanmis_metin}"
            webbrowser.open(wa_url)
            
            if os.path.exists(self.pdf_path):
                os.system(f'explorer /select,"{os.path.abspath(self.pdf_path)}"')
        except Exception as e:
            messagebox.showerror("WhatsApp Hatası", f"Bağlantı kurulurken hata oluştu: {str(e)}")


# ------------------------------------------------------------------
# ANA GÖRÜNÜM: AI SORU VIEW (YENİLENMİŞ GEMINI MİMARİSİ)
# ------------------------------------------------------------------
class AISoruView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        self.uretilen_sorular = ""
        self.preview_window = None
        
        # ------------------------------------------------------------------
        # GOOGLE DRIVE MASAÜSTÜ KALICI SORU BANKASI YOLU
        # ------------------------------------------------------------------
        self.DRIVE_SORU_BANKASI_YOLU = r"G:\Drive'ım\AI Soru Bankası"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.arayuz_olustur()

    def arayuz_olustur(self):
        # --- Üst Panel ---
        self.header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.header.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(self.header, text="🧠 AI Soru Üretici", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left", padx=20, pady=20)
        
        self.cmb_ders = ctk.CTkOptionMenu(self.header, values=["Matematik", "Türkçe", "Fen Bilimleri", "Sosyal Bilgiler", "Geometri", "Tarih", "Coğrafya"], fg_color="gray90", text_color="black", button_color=self.COLOR_SIDEBAR)
        self.cmb_ders.pack(side="left", padx=5)
        
        self.ent_konu = ctk.CTkEntry(self.header, placeholder_text="Konu (Örn: Üslü Sayılar)", width=150)
        self.ent_konu.pack(side="left", padx=5)
        
        self.cmb_zorluk = ctk.CTkOptionMenu(self.header, values=["Kolay", "Orta", "Zor", "Yeni Nesil (LGS/YKS)"], width=150, button_color=self.COLOR_SIDEBAR)
        self.cmb_zorluk.pack(side="left", padx=5)
        
        self.ent_sayi = ctk.CTkEntry(self.header, placeholder_text="Soru Sayısı", width=80)
        self.ent_sayi.pack(side="left", padx=5)

        self.btn_uret = ctk.CTkButton(self.header, text="Soruları Üret", fg_color=self.COLOR_ACCENT_GOLD, font=ctk.CTkFont(weight="bold"), command=self.soru_uret)
        self.btn_uret.pack(side="right", padx=20)

        # --- İçerik Alanı ---
        self.content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.content.grid(row=1, column=0, padx=40, pady=(0, 40), sticky="nsew")
        
        self.txt_sonuc = ctk.CTkTextbox(self.content, fg_color="transparent", font=ctk.CTkFont(size=14), wrap="word")
        self.txt_sonuc.pack(fill="both", expand=True, padx=20, pady=20)
        self.txt_sonuc.insert("0.0", "Hazırlamak istediğiniz testin detaylarını girip 'Soruları Üret' butonuna tıklayın.\n\nSorular üretildikten sonra PDF otomatik olarak bulut klasörünüze derlenecektir.")

        self.btn_pdf_onizleme = ctk.CTkButton(self.content, text="📄 PDF Ön İzleme & Yazdır", fg_color=self.COLOR_SIDEBAR, height=40, font=ctk.CTkFont(weight="bold"), command=self.ac_pdf_popup)

    def soru_uret(self):
        ders = self.cmb_ders.get()
        konu = self.ent_konu.get().strip()
        zorluk = self.cmb_zorluk.get()
        sayi = self.ent_sayi.get().strip() or "3"
        
        if not konu:
            messagebox.showwarning("Uyarı", "Lütfen bir konu başlığı giriniz.")
            return

        self.btn_pdf_onizleme.pack_forget() 
        self.txt_sonuc.delete("0.0", "end")
        self.txt_sonuc.insert("0.0", f"🔍 Gemini 3.5 Flash {ders} - {konu} konusu için {sayi} adet MEB standardında soru hazırlıyor...\nLütfen bekleyin.")
        self.btn_uret.configure(state="disabled")
        
        threading.Thread(target=self.api_cagir, args=(ders, konu, zorluk, sayi), daemon=True).start()

    def api_cagir(self, ders, konu, zorluk, sayi):
        api_key = "AIzaSyC73QW4TWrLKmFuvKhZoQ8rKyqSGnPxvBg" 
        
        # --- GÜNCELLENMİŞ VE KESİN PROMPT (KOMUT) ---
        prompt = (
            f"Sen uzman bir Türk eğitimcisin ve MEB standartlarında kusursuz sorular hazırlıyorsun. "
            f"Bana {ders} dersinin '{konu}' konusu ile ilgili, {zorluk} zorluk seviyesinde "
            f"toplam {sayi} adet çoktan seçmeli (A,B,C,D,E şıklı) özgün test sorusu hazırla.\n\n"
            f"KURALLAR:\n"
            f"1. KESİNLİKLE HİÇBİR EMOJİ VEYA SEMBOL KULLANMA.\n"
            f"2. ÇOK ÖNEMLİ: Matematiksel veya fenni ifadelerde KESİNLİKLE LaTeX kodları ($, \\sqrt, \\frac, vb.) KULLANMA!\n"
            f"3. Tüm karekök, üslü sayı veya kesirleri doğrudan düz metin ve Unicode klavye işaretleri kullanarak yaz. Örneğin kesirleri yan yana (a/b) şeklinde, karekökleri '√' işareti ile, üslü sayıları 'x^2' şeklinde normal yazıyla yaz.\n"
            f"4. Sorular okunaklı, net ve alt alta düzenli paragraflar halinde olsun.\n"
            f"5. En alta da belirgin bir 'CEVAP ANAHTARI' bölümü ekle."
        )

        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
            
            if response.text:
                self.uretilen_sorular = response.text
                
                os.makedirs(self.DRIVE_SORU_BANKASI_YOLU, exist_ok=True)
                
                test_title = f"{ders}_{konu.replace(' ', '_')}"
                pdf_isim = f"{test_title}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.pdf"
                pdf_tam_yol = os.path.join(self.DRIVE_SORU_BANKASI_YOLU, pdf_isim)
                
                pdf_status = self._generate_soru_pdf(ders, konu, zorluk, response.text, pdf_tam_yol)
                
                if pdf_status == "OK":
                    self.after(0, lambda: self.txt_sonuc.delete("0.0", "end"))
                    self.after(0, lambda: self.txt_sonuc.insert("0.0", response.text))
                    self.after(0, lambda: self.txt_sonuc.insert("0.0", f"✅ [BULUT SENKRONİZASYONU] Soru bankası dökümanı başarıyla senkronize klasöre yüklendi:\n{pdf_tam_yol}\n\n" + "-"*80 + "\n\n"))
                    
                    self.after(0, lambda: self.btn_pdf_onizleme.pack(pady=10))
                    self.after(0, lambda: self._pencereyi_guvenli_ac(pdf_tam_yol, response.text, test_title))
                else:
                    self.after(0, lambda msg=pdf_status: self.txt_sonuc.insert("0.0", f"⚠️ PDF Tasarım Hatası: {msg}\n\n"))
            else:
                self.after(0, lambda: self.txt_sonuc.insert("end", "\n⚠️ Gemini'den boş yanıt döndü."))
        except Exception as e:
            hata_msg = str(e)
            self.after(0, lambda msg=hata_msg: self.txt_sonuc.insert("end", f"\n⚠️ Sistem Hatası: {msg}"))
            
        self.after(0, lambda: self.btn_uret.configure(state="normal"))

    # ------------------------------------------------------------------
    # DİKEY VE KURUMSAL REPORTLAB TEST DÖKÜMANI ÇİZİCİ
    # ------------------------------------------------------------------
    def _generate_soru_pdf(self, ders, konu, zorluk, soru_metni, output_filename):
        try:
            doc = SimpleDocTemplate(output_filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('TestTitle', fontName=PDF_FONT, fontSize=18, leading=22, textColor=colors.HexColor("#044D29"))
            meta_style = ParagraphStyle('TestMeta', fontName=PDF_FONT, fontSize=10, leading=14, textColor=colors.HexColor("#555555"), alignment=TA_RIGHT)
            body_style = ParagraphStyle('TestBody', fontName=PDF_FONT, fontSize=11, leading=16, textColor=colors.HexColor("#1A1A1A"))
            
            story = []

            # Logo ve Kurumsal Üst Bilgi Katmanı
            if os.path.exists("logo.png"):
                logo_el = RLImage("logo.png", width=45, height=45)
            else:
                logo_el = Paragraph("<font color='#044D29'><b>BV</b></font><font color='#D4AF37'><b>.</b></font>", ParagraphStyle('TestFBLogo', fontName=PDF_FONT, fontSize=20))
            
            title_el = Paragraph(f"<b>{ders.upper()} MEB STANDARTLARINDA TESTİ</b><br/><font size=11 color='#D4AF37'><b>Konu: {konu}</b></font>", title_style)
            date_str = datetime.now().strftime("%d.%m.%Y")
            meta_el = Paragraph(f"Tarih: {date_str}<br/>Zorluk: {zorluk}", meta_style)
            
            top_table = Table([[logo_el, title_el, meta_el]], colWidths=[50, 340, 140])
            top_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (1,0), (1,0), 10)]))
            story.append(top_table)
            story.append(Spacer(1, 10))
            
            # Altın Sarısı Çizgi separator
            separator = Table([[""]], colWidths=[530], rowHeights=[2.5])
            separator.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), colors.HexColor("#D4AF37"))]))
            story.append(separator)
            story.append(Spacer(1, 20))

            # Soru metnini satır bazlı analiz ederek reportlab story'sine ekleme
            clean_metin = re.sub(r'[*_#]', '', soru_metni)
            for line in clean_metin.split('\n'):
                if line.strip():
                    safe_line = line.replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe_line, body_style))
                    story.append(Spacer(1, 5))
            
            doc.build(story)
            return "OK"
        except Exception as e:
            return str(e)

    def _pencereyi_guvenli_ac(self, pdf_filename, text, test_title):
        try:
            self.preview_window = SoruPreviewWindow(self.winfo_toplevel(), pdf_filename, text, test_title)
        except Exception as e:
            messagebox.showerror("Arayüz Hatası", f"Ön izleme ekranı başlatılamadı:\n{str(e)}")

    def ac_pdf_popup(self):
        ders = self.cmb_ders.get()
        konu = self.ent_konu.get().strip()
        test_title = f"{ders}_{konu.replace(' ', '_')}"
        
        try:
            dosyalar = [os.path.join(self.DRIVE_SORU_BANKASI_YOLU, f) for f in os.listdir(self.DRIVE_SORU_BANKASI_YOLU) if f.startswith(test_title)]
            if dosyalar:
                en_guncel_pdf = max(dosyalar, key=os.path.getctime)
                self._pencereyi_guvenli_ac(en_guncel_pdf, self.uretilen_sorular, test_title)
            else:
                messagebox.showwarning("Bulunamadı", "Ön izlenecek aktif döküman bulunamadı, lütfen önce soru üretin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya aranırken hata oluştu: {str(e)}")