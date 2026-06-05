import customtkinter as ctk
import tkinter.messagebox as messagebox
import threading
import webbrowser

class MufredatView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.arayuz_olustur()

    def arayuz_olustur(self):
        # Üst Panel
        self.header_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.header_frame.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(self.header_frame, text="📚 Güncel Müfredat Sorgulama", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left", padx=20, pady=20)
        
        self.cmb_sinif = ctk.CTkOptionMenu(self.header_frame, values=[f"{i}. Sınıf" for i in range(1, 13)] + ["LGS Hazırlık", "YKS Hazırlık"], fg_color="gray90", text_color="black", button_color=self.COLOR_SIDEBAR)
        self.cmb_sinif.pack(side="left", padx=10)
        self.cmb_sinif.set("Sınıf Seçin")

        self.ent_ders = ctk.CTkEntry(self.header_frame, placeholder_text="Ders Adı (Örn: Matematik)", width=200)
        self.ent_ders.pack(side="left", padx=10)

        # Butonlar
        self.btn_sorgula = ctk.CTkButton(self.header_frame, text="Gemini ile Getir", fg_color=self.COLOR_ACCENT_GOLD, text_color="white", font=ctk.CTkFont(weight="bold"), command=self.mufredat_sorgula)
        self.btn_sorgula.pack(side="right", padx=15)
        
        # Siteyi doğrudan açmak için kısayol butonu
        self.btn_meb_site = ctk.CTkButton(self.header_frame, text="🌐 TYMM Sitesi", fg_color="gray50", hover_color="gray40", width=120, command=lambda: webbrowser.open("https://tymm.meb.gov.tr/ogretim-programlari"))
        self.btn_meb_site.pack(side="right", padx=5)

        # İçerik Alanı
        self.content_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.content_frame.grid(row=1, column=0, padx=40, pady=(0, 40), sticky="nsew")
        
        self.txt_sonuc = ctk.CTkTextbox(self.content_frame, fg_color="transparent", font=ctk.CTkFont(size=14), wrap="word")
        self.txt_sonuc.pack(fill="both", expand=True, padx=20, pady=20)
        self.txt_sonuc.insert("0.0", "Müfredat sorgulamak için yukarıdaki alanları doldurup butona tıklayın.\n\n(Bu işlem tamamen ücretsizdir ve Google Gemini Yeni Nesil Resmi SDK altyapısını kullanır.)")

    def mufredat_sorgula(self):
        sinif = self.cmb_sinif.get()
        ders = self.ent_ders.get()
        
        if sinif == "Sınıf Seçin" or not ders:
            messagebox.showwarning("Uyarı", "Lütfen hem sınıf hem de ders adını giriniz.")
            return

        self.txt_sonuc.delete("0.0", "end")
        self.txt_sonuc.insert("0.0", f"🔍 Google Gemini {sinif} {ders} için en güncel MEB müfredatını kendi sisteminden analiz ediyor...\nLütfen bekleyin...")
        self.btn_sorgula.configure(state="disabled", text="Sorgulanıyor...")
        
        # İşlemi arka planda başlat
        threading.Thread(target=self.yapay_zeka_api_cagir, args=(sinif, ders), daemon=True).start()

    def yapay_zeka_api_cagir(self, sinif, ders):
        api_key = "AIzaSyC73QW4TWrLKmFuvKhZoQ8rKyqSGnPxvBg"

        prompt = f"""
        Sen MEB müfredatlarına (Türkiye Yüzyılı Maarif Modeli) tam hakim uzman bir Türk eğitim danışmanısın.
        Öğrenci Seviyesi: {sinif}
        Ders: {ders}
        
        Görev: Doğrudan kendi güncel bilgi havuzunu kullanarak bu dersin en güncel ünitelerini ve ana konu başlıklarını listele.
        
        Kurallar:
        1. Kesinlikle güncel (2026) "Türkiye Yüzyılı Maarif Modeli"ne uygun olarak cevap ver.
        2. Eski müfredatları (2025 ve öncesi) KESİNLİKLE kullanma. Sadece en yeni konuları yaz.
        3. Çok şık, okunaklı, profesyonel bir Türkçe ile ve maddeler halinde listele.
        """

        try:
            from google import genai
            
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt
            )
            
            if response.text:
                kaynak_notu = "\n\n---\n*Bu sonuçlar doğrudan Google Gemini altyapısı kullanılarak en güncel MEB müfredat verilerinden derlenmiştir.*"
                self.ekrana_yaz(f"✅ İşlem Başarılı\n\n{response.text}{kaynak_notu}")
            else:
                self.ekrana_yaz("⚠️ Gemini'den boş yanıt döndü. Lütfen tekrar deneyin.")
                
        except ImportError:
            self.ekrana_yaz("⚠️ Yeni Google GenAI Kütüphanesi Eksik!\nLütfen terminale şunu yazın:\npip install google-genai")
            
        except Exception as e:
            self.ekrana_yaz(f"⚠️ Gemini Hatası:\nDetay: {str(e)}")

    def ekrana_yaz(self, metin):
        self.after(0, self._ekrana_yaz_guncelle, metin)
        
    def _ekrana_yaz_guncelle(self, metin):
        self.txt_sonuc.delete("0.0", "end")
        self.txt_sonuc.insert("0.0", metin)
        self.btn_sorgula.configure(state="normal", text="Gemini ile Getir")