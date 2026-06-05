import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import get_db
import datetime
import os
from fpdf import FPDF

class HataTelafiView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_ACCENT = "#D4AF37"
        
        self.db = get_db()
        self.secili_ogrenci = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.arayuz_olustur()

    def arayuz_olustur(self):
        # --- HEADER ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(header_frame, text="Akıllı Hata Telafi Modülü", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(side="left")
        ctk.CTkLabel(header_frame, text="Kişiye Özel PDF Test Üretici", font=ctk.CTkFont(size=14, slant="italic"), text_color="gray").pack(side="left", padx=15, pady=(10,0))

        # --- ANA İÇERİK KARTI ---
        main_card = ctk.CTkFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#E0E0E0")
        main_card.grid(row=1, column=0, padx=40, pady=(0, 40), sticky="nsew")
        main_card.grid_columnconfigure(1, weight=1)

        # 1. Öğrenci Seçimi
        ctk.CTkLabel(main_card, text="1. Öğrenci Seçin", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_SIDEBAR).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        ogrenci_isimleri = ["Öğrenci Bulunamadı"]
        try:
            if hasattr(self.master, "frame_ogrenciler") and self.master.frame_ogrenciler.ogrenci_listesi:
                ogrenci_isimleri = [ogr["Ad Soyad"] for ogr in self.master.frame_ogrenciler.ogrenci_listesi]
        except: pass

        self.cmb_ogrenci = ctk.CTkOptionMenu(main_card, values=ogrenci_isimleri, width=300, fg_color="#F4F1EA", text_color="black", button_color=self.COLOR_SIDEBAR)
        self.cmb_ogrenci.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        # 2. Hatalı Konu / Kazanım Seçimi
        ctk.CTkLabel(main_card, text="2. Telafi Edilecek Konu/Kazanım", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_SIDEBAR).grid(row=2, column=0, padx=30, pady=(10, 10), sticky="w")
        
        self.ent_konu = ctk.CTkEntry(main_card, placeholder_text="Örn: Üslü Sayılar, Parabol, vb.", width=300)
        self.ent_konu.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="w")

        # 3. Soru Sayısı
        ctk.CTkLabel(main_card, text="3. Soru Sayısı", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_SIDEBAR).grid(row=4, column=0, padx=30, pady=(10, 10), sticky="w")
        
        self.ent_soru_sayisi = ctk.CTkEntry(main_card, placeholder_text="Örn: 5", width=150)
        self.ent_soru_sayisi.grid(row=5, column=0, padx=30, pady=(0, 30), sticky="w")

        # 4. Üret Butonu
        btn_uret = ctk.CTkButton(
            main_card, text="⚙️ Kişisel Telafi Testi (PDF) Üret", 
            font=ctk.CTkFont(size=16, weight="bold"), height=50, width=300,
            fg_color=self.COLOR_ACCENT, hover_color="#B8972E", text_color="white",
            command=self.pdf_uret
        )
        btn_uret.grid(row=6, column=0, padx=30, pady=10, sticky="w")

        # Sağ Taraf Bilgi Paneli
        info_frame = ctk.CTkFrame(main_card, fg_color="#F9F9F9", corner_radius=10)
        info_frame.grid(row=0, column=1, rowspan=7, padx=30, pady=30, sticky="nsew")
        
        info_text = (
            "NASIL ÇALIŞIR?\n\n"
            "1. Öğrencinin yanlış yaptığı alt kazanımı yazın.\n"
            "2. Sistem, veritabanındaki 'Soru Havuzu'ndan\n"
            "   bu konuya ait soruları yapay zeka ile çeker.\n"
            "3. Öğrenciye özel, isminin yazdığı şık bir\n"
            "   PDF test dosyası masaüstünüze kaydedilir."
        )
        ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=14), justify="left", text_color="gray40").pack(expand=True, padx=20)

    def pdf_uret(self):
        ogrenci = self.cmb_ogrenci.get()
        konu = self.ent_konu.get()
        soru_sayisi = self.ent_soru_sayisi.get()

        if not konu or not soru_sayisi.isdigit():
            messagebox.showwarning("Eksik Bilgi", "Lütfen geçerli bir konu ve soru sayısı girin.")
            return

        # Masaüstü yolunu bul
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        dosya_adi = f"{ogrenci}_{konu}_Telafi_Testi.pdf".replace(" ", "_")
        pdf_yolu = os.path.join(desktop_path, dosya_adi)

        try:
            # FPDF ile PDF Oluşturma (A4 Boyutu)
            pdf = FPDF()
            pdf.add_page()
            
            # Türkçe karakter desteği için font ayarı (Eğer hata verirse 'Arial' kullanabilirsiniz)
            pdf.set_font("Arial", size=12)

            # Başlık
            pdf.set_font("Arial", 'B', 18)
            pdf.cell(200, 15, txt=f"BV OGRENME PLATFORMU", ln=True, align='C')
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Ogrenci: {ogrenci}", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Konu: {konu} - Telafi Testi", ln=True, align='C')
            pdf.line(10, 45, 200, 45) # Çizgi çek
            pdf.ln(15)

            # Veritabanından (Soru Havuzu) sorular çekilecek.
            # Şimdilik Firebase soru havuzunuz olmadığı için dinamik metin üretiyoruz.
            pdf.set_font("Arial", size=12)
            
            for i in range(1, int(soru_sayisi) + 1):
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, txt=f"Soru {i}:", ln=True)
                pdf.set_font("Arial", size=12)
                
                # Gelecekte buraya firebase'den gelen soru resmi eklenecek: 
                # pdf.image('soru_resmi_yolu.jpg', x=10, y=pdf.get_y(), w=100)
                
                pdf.multi_cell(0, 8, txt=f"Bu alan {konu} ile ilgili ozel olarak getirilmis {i}. sorunun metni veya gorselidir. (Veritabani entegrasyonu tamamlandiginda burada gercek soru yer alacaktir.)")
                pdf.ln(10)

            pdf.output(pdf_yolu)
            messagebox.showinfo("Başarılı", f"Telafi Testi Masaüstüne Kaydedildi!\n\nDosya: {dosya_adi}")
            os.startfile(pdf_yolu) # PDF'i otomatik aç

        except Exception as e:
            messagebox.showerror("Hata", f"PDF üretilirken bir hata oluştu:\n{e}")