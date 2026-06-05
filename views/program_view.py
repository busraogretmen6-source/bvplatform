import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as messagebox
from database import get_db
import threading
import os
import re
import json
import webbrowser
import urllib.parse

# PDF, Görselleştirme, Tablo ve Yazıcı Modülleri
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage  # Logo görseli yüklemek için
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
# PDF ÖN İZLEME VE EYLEM PENCERESİ
# ------------------------------------------------------------------
class PDFPreviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, pdf_path, content_text, student_name, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(f"📄 Program Ön İzleme - {student_name}")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        self.pdf_path = pdf_path
        self.content_text = content_text
        self.student_name = student_name
        
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
                enum_printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                yazici_listesi = [p[2] for p in enum_printers]
            except Exception:
                pass
                
        self.cmb_yazici = ctk.CTkOptionMenu(self.toolbar, values=yazici_listesi, width=200, fg_color="white", text_color="black", button_color="#044D29", button_hover_color="#03361D")
        self.cmb_yazici.pack(side="left", padx=5)
        
        self.btn_yazdir = ctk.CTkButton(self.toolbar, text="Yazdır", fg_color="#044D29", hover_color="#03361D", width=80, font=ctk.CTkFont(weight="bold"), command=self.pdf_yazdir)
        self.btn_yazdir.pack(side="left", padx=5)
        
        self.btn_whatsapp = ctk.CTkButton(self.toolbar, text="WhatsApp ile Gönder", fg_color="#25D366", hover_color="#20BA56", text_color="white", font=ctk.CTkFont(weight="bold"), command=self.whatsapp_ile_gonder)
        self.btn_whatsapp.pack(side="right", padx=15)

        self.preview_scroll = ctk.CTkScrollableFrame(self, fg_color="gray30", corner_radius=0)
        self.preview_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def pdf_sayfalarini_yukle(self):
        if not fitz:
            lbl_err = ctk.CTkLabel(self.preview_scroll, text="Ön izleme için 'pymupdf' kütüphanesi eksik.\npip install pymupdf", text_color="white")
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
            messagebox.showwarning("Yazdırma Hatası", "Windows yazıcı bileşenleri eksik.")
            return
            
        try:
            win32print.SetDefaultPrinter(secili_yazici)
            win32api.ShellExecute(0, "print", self.pdf_path, None, ".", 0)
        except Exception as e:
            messagebox.showerror("Yazdırma Hatası", f"Yazıcıya gönderilirken hata oluştu: {str(e)}")

    def whatsapp_ile_gonder(self):
        try:
            mesaj_temiz = re.sub(r'[*_]', '', self.content_text)
            kodlanmis_metin = urllib.parse.quote(mesaj_temiz)
            
            wa_url = f"whatsapp://send?text={kodlanmis_metin}"
            webbrowser.open(wa_url)
            
            if os.path.exists(self.pdf_path):
                os.system(f'explorer /select,"{os.path.abspath(self.pdf_path)}"')
                
        except Exception as e:
            messagebox.showerror("WhatsApp Hatası", f"Bağlantı kurulurken hata oluştu: {str(e)}")


# ------------------------------------------------------------------
# ANA GÖRÜNÜM: PROGRAM VIEW
# ------------------------------------------------------------------
class ProgramView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        
        self.db = get_db()
        self.secili_ogrenci = None
        self.preview_window = None 
        
        self.PROJE_ANA_DIZIN = r"H:\Drive'ım\Öğrencilerim"
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.arayuz_olustur()

    def arayuz_olustur(self):
        self.sidebar_liste = ctk.CTkFrame(self, width=200, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.sidebar_liste.grid(row=0, column=0, padx=(40, 10), pady=40, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_liste, text="Öğrenci Seçin", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        self.scroll_liste = ctk.CTkScrollableFrame(self.sidebar_liste, fg_color="transparent")
        self.scroll_liste.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Çalışma programı hazırlamak için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")

    def listeyi_yenile(self):
        for widget in self.scroll_liste.winfo_children(): widget.destroy()
        if hasattr(self.master, "frame_ogrenciler"):
            for ogr in self.master.frame_ogrenciler.ogrenci_listesi:
                ctk.CTkButton(self.scroll_liste, text=ogr.get("Ad Soyad", "-"), fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F0F0F0", anchor="w", command=lambda o=ogr: self.ogrenci_sec(o)).pack(fill="x", pady=2)

    def ogrenci_sec(self, ogrenci):
        self.secili_ogrenci = ogrenci
        self.lbl_info.place_forget()
        for widget in self.main_content.winfo_children(): widget.destroy()
        
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text=f"{ogrenci['Ad Soyad']} - AI Çalışma Programı", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")

        form_frame = ctk.CTkFrame(self.main_content, fg_color="#F9F9F9", corner_radius=10)
        form_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(form_frame, text="Müsait Vakitler (Örn: Hafta içi 17:00 sonrası, h.sonu tüm gün):").pack(anchor="w", padx=20, pady=(15, 5))
        self.ent_vakit = ctk.CTkEntry(form_frame, width=500)
        self.ent_vakit.pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkLabel(form_frame, text="Odaklanılacak Zayıf Konular (Örn: Geometri Katı Cisimler, TYT Türkçe):").pack(anchor="w", padx=20, pady=(10, 5))
        self.ent_konu = ctk.CTkEntry(form_frame, width=500)
        self.ent_konu.pack(anchor="w", padx=20, pady=5)
        
        self.btn_uret = ctk.CTkButton(form_frame, text="Program Oluştur", fg_color=self.COLOR_ACCENT_GOLD, font=ctk.CTkFont(weight="bold"), command=self.program_uret)
        self.btn_uret.pack(anchor="e", padx=20, pady=15)

        self.txt_sonuc = ctk.CTkTextbox(self.main_content, fg_color="white", border_width=1, border_color="#E0E0E0", font=ctk.CTkFont(size=14))
        self.txt_sonuc.pack(fill="both", expand=True, padx=20, pady=20)

    def program_uret(self):
        vakitler = self.ent_vakit.get()
        konular = self.ent_konu.get()
        
        if not vakitler:
            messagebox.showwarning("Uyarı", "Lütfen öğrencinin müsait vakitlerini girin.")
            return

        self.txt_sonuc.delete("0.0", "end")
        self.txt_sonuc.insert("0.0", "🔄 Yapay Zeka döküman mimarisini kurumsal tasarıma dönüştürüyor...\nLütfen bekleyin.")
        self.btn_uret.configure(state="disabled")
        threading.Thread(target=self._api_cagir, args=(vakitler, konular), daemon=True).start()

    # ------------------------------------------------------------------
    # Gelişmiş Kurumsal Tasarımlı PDF Üretici
    # ------------------------------------------------------------------
    def _generate_pdf(self, student_name, json_data_str, motivation_text, output_filename):
        try:
            clean_json = re.sub(r'```json|```', '', json_data_str).strip()
            schedule_data = json.loads(clean_json)

            # Yatay A4 düzeni ayarları
            doc = SimpleDocTemplate(output_filename, pagesize=landscape(letter), leftMargin=35, rightMargin=35, topMargin=35, bottomMargin=35)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('TitleStyle', fontName=PDF_FONT, fontSize=20, leading=24, textColor=colors.HexColor("#044D29"), alignment=TA_LEFT)
            header_style = ParagraphStyle('HeaderStyle', fontName=PDF_FONT, fontSize=11, textColor=colors.white, alignment=TA_CENTER)
            cell_style = ParagraphStyle('CellStyle', fontName=PDF_FONT, fontSize=10, textColor=colors.black, alignment=TA_CENTER)
            
            story = []

            # 1. LOGO VE BAŞLIK ENTEGRASYONU (Üst Bölüm)
            if os.path.exists("logo.png"):
                logo_element = RLImage("logo.png", width=50, height=50)
            else:
                # Dosya yoksa çökmeyi önleyen modern tipografik fallback logo
                logo_element = Paragraph("<font color='#044D29'><b>BV</b></font><font color='#D4AF37'><b>.</b></font>", ParagraphStyle('FBLogo', fontName=PDF_FONT, fontSize=22, leading=24))
            
            title_element = Paragraph(f"<b>{student_name.upper()} - HAFTALIK AKADEMİK GELİŞİM PLANI</b>", title_style)
            
            # Başlık tablosu yerleşimi
            header_top_table = Table([[logo_element, title_element]], colWidths=[60, 660])
            header_top_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'LEFT'),
                ('LEFTPADDING', (1,0), (1,0), 10)
            ]))
            story.append(header_top_table)
            story.append(Spacer(1, 10))
            
            # Altın Sarısı Kurumsal Çizgi
            gold_line = Table([[""]], colWidths=[720], rowHeights=[3])
            gold_line.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), colors.HexColor("#D4AF37"))]))
            story.append(gold_line)
            story.append(Spacer(1, 20))
            
            # 2. KURUMSAL EXCEL TABLOSU MATRİSİ
            headers = ["Saat", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            header_row = [Paragraph(f"<b>{h}</b>", header_style) for h in headers]
            
            data = [header_row]
            for row in schedule_data:
                data.append([
                    Paragraph(str(row.get("Saat", "-")), cell_style),
                    Paragraph(str(row.get("Pazartesi", "-")), cell_style),
                    Paragraph(str(row.get("Salı", "-")), cell_style),
                    Paragraph(str(row.get("Çarşamba", "-")), cell_style),
                    Paragraph(str(row.get("Perşembe", "-")), cell_style),
                    Paragraph(str(row.get("Cuma", "-")), cell_style),
                    Paragraph(str(row.get("Cumartesi", "-")), cell_style),
                    Paragraph(str(row.get("Pazar", "-")), cell_style)
                ])

            col_widths = [75, 92, 92, 92, 92, 92, 92, 92]
            table = Table(data, colWidths=col_widths)
            
            # Kurumsal Temaya Göre Tablo Tasarımı (Koyu Yeşil Başlık, Altın Sarısı İnce Izgara Çizgileri)
            table_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#044D29")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")), # Çizgiler artık kurumsal Altın Sarısı
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('TOPPADDING', (0,0), (-1,0), 10),
            ])
            
            for i in range(1, len(data)):
                bg_color = "#FFFFFF" if i % 2 == 0 else "#F4F7F5" # Çok hafif yeşil-gri kurumsal geçiş tonu
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(bg_color))
                table_style.add('BOTTOMPADDING', (0, i), (-1, i), 8)
                table_style.add('TOPPADDING', (0, i), (-1, i), 8)
                
            table.setStyle(table_style)
            story.append(table)
            
            # 3. EN ALT BÖLÜM: KURUMSAL MOTİVASYON KONUŞMASI
            if motivation_text:
                story.append(Spacer(1, 20))
                
                # Motivasyon kutusu başlığı
                motiv_title_style = ParagraphStyle('MotivTitle', fontName=PDF_FONT, fontSize=11, leading=13, textColor=colors.HexColor("#044D29"))
                story.append(Paragraph("<b>🎯 AKADEMİK KOÇLUK VE MOTİVASYON NOTU</b>", motiv_title_style))
                story.append(Spacer(1, 6))
                
                # Kurumsal çerçeveli motivasyon kutusu tasarımı
                motiv_body_style = ParagraphStyle('MotivBody', fontName=PDF_FONT, fontSize=10, leading=15, textColor=colors.HexColor("#1A1A1A"))
                
                motiv_box = Table([[Paragraph(motivation_text, motiv_body_style)]], colWidths=[720])
                motiv_box.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F9FBF9")),     # Hafif soft arka plan
                    ('BOX', (0,0), (0,0), 1, colors.HexColor("#044D29")),          # Koyu yeşil dış çerçeve
                    ('LINELEFT', (0,0), (0,0), 4, colors.HexColor("#D4AF37")),     # Sol kenarda kalın altın sarısı şerit
                    ('TOPPADDING', (0,0), (0,0), 12),
                    ('BOTTOMPADDING', (0,0), (0,0), 12),
                    ('LEFTPADDING', (0,0), (0,0), 15),
                    ('RIGHTPADDING', (0,0), (0,0), 15),
                ]))
                story.append(motiv_box)
            
            doc.build(story)
            return "OK"
        except Exception as e:
            return f"Tasarım çizim hatası: {str(e)}"

    def _api_cagir(self, vakitler, konular):
        api_key = "AIzaSyC73QW4TWrLKmFuvKhZoQ8rKyqSGnPxvBg" 
        student_name = self.secili_ogrenci.get('Ad Soyad', 'Ogrenci')
        
        # Yapay zekaya 3 bölümlü çıktı düzeni dikte ediliyor
        prompt = (
            f"Sen profesyonel bir eğitim koçusun. Öğrencin {student_name} için "
            f"7 günlük bir çalışma programı hazırlayacaksın.\n"
            f"Müsait saatler: {vakitler}\n"
            f"Odaklanılacak konular: {konular}\n\n"
            f"Bana KESİNLİKLE şu 3 ana bölümden oluşan bir yanıt ver ve aralarına tam olarak belirtilen etiketleri koy:\n\n"
            f"---WHATSAPP---\n"
            f"Buraya öğrenciye WhatsApp'tan gönderilecek emojili, samimi ve motive edici mesajı yaz.\n\n"
            f"---JSON---\n"
            f"Buraya SADECE PDF tablosu çiziminde kullanılacak saatleri ve günleri içeren geçerli bir JSON dizisi ver. Başka hiçbir şey yazma. Format:\n"
            f"[\n"
            f"  {{\"Saat\": \"17:00 - 18:00\", \"Pazartesi\": \"Konu\", \"Salı\": \"Konu\", \"Çarşamba\": \"Konu\", \"Perşembe\": \"Konu\", \"Cuma\": \"Konu\", \"Cumartesi\": \"Konu\", \"Pazar\": \"Konu\"}}\n"
            f"]\n\n"
            f"---MOTIVASYON---\n"
            f"Buraya PDF dökümanının en altına kurumsal kutu içine yerleştirilecek resmi, profesyonel, ilham verici ve etkileyici bir motivasyon konuşması/notu yaz. Kesinlikle emoji kullanma."
        )

        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            
            if response.text:
                text_clean = response.text
                whatsapp_metni = ""
                json_verisi = "[]"
                motivasyon_metni = ""

                # Gelişmiş içerik ayrıştırma mimarisi
                try:
                    wa_match = re.search(r'---WHATSAPP---(.*?)---JSON---', text_clean, re.DOTALL)
                    js_match = re.search(r'---JSON---(.*?)---MOTIVASYON---', text_clean, re.DOTALL)
                    mo_match = re.search(r'---MOTIVASYON---(.*)', text_clean, re.DOTALL)
                    
                    if wa_match: whatsapp_metni = wa_match.group(1).strip()
                    if js_match: json_verisi = js_match.group(1).strip()
                    if mo_match: motivasyon_metni = mo_match.group(1).strip()
                except Exception:
                    whatsapp_metni = text_clean
                
                self.after(0, lambda: self.txt_sonuc.delete("0.0", "end"))
                self.after(0, lambda: self.txt_sonuc.insert("0.0", whatsapp_metni))
                
                ogrenci_klasoru = os.path.join(self.PROJE_ANA_DIZIN, student_name)
                os.makedirs(ogrenci_klasoru, exist_ok=True)
                
                pdf_isim = f"{student_name.replace(' ', '_')}_Program.pdf"
                pdf_tam_yol = os.path.join(ogrenci_klasoru, pdf_isim)
                
                # Tablo verisi ve motivasyon yazısı PDF motoruna gönderiliyor
                pdf_status = self._generate_pdf(student_name, json_verisi, motivasyon_metni, pdf_tam_yol)
                
                if pdf_status == "OK":
                    self.after(0, lambda: self.txt_sonuc.insert("0.0", f"🚀 [BULUT SENKRONİZASYONU] Döküman kurumsal tasarım çizgileriyle '{student_name}' klasörüne kaydedildi.\n\n"))
                    self.after(0, lambda: self._pencereyi_guvenli_ac(pdf_tam_yol, whatsapp_metni, student_name))
                else:
                    self.after(0, lambda: self.txt_sonuc.insert("end", f"\n⚠️ PDF Çizim Hatası: {pdf_status}"))
            else:
                self.after(0, lambda: self.txt_sonuc.insert("end", "\n⚠️ Yanıt boş döndü."))
        except Exception as e:
            hata_mesaji = str(e) # e silinmeden önce metni güvenli bir değişkene kopyalıyoruz
            self.after(0, lambda msg=hata_mesaji: self.txt_sonuc.insert("end", f"\n⚠️ Sistem Hatası: {msg}"))
        
        self.after(0, lambda: self.btn_uret.configure(state="normal"))

    def _pencereyi_guvenli_ac(self, pdf_filename, text, student_name):
        try:
            self.preview_window = PDFPreviewWindow(self.winfo_toplevel(), pdf_filename, text, student_name)
        except Exception as e:
            messagebox.showerror("Arayüz Hatası", f"Ön izleme ekranı başlatılamadı:\n{str(e)}")