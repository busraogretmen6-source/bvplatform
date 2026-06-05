import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import get_db
from datetime import datetime
import datetime as dt

class SoruTakipView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        
        self.db = get_db()
        self.soru_kayitlari = []
        self.hedefler = []
        self.secili_ogrenci = None
        self.guncel_hafta = dt.date.today().strftime("%G-W%V")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        self.sidebar_liste = ctk.CTkFrame(self, width=200, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.sidebar_liste.grid(row=0, column=0, padx=(40, 10), pady=40, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_liste, text="Öğrenci Seçin", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        self.scroll_liste = ctk.CTkScrollableFrame(self.sidebar_liste, fg_color="transparent")
        self.scroll_liste.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Soru çözüm takibi için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")

    def listeyi_yenile(self):
        for widget in self.scroll_liste.winfo_children(): widget.destroy()
        ogrenciler = []
        if hasattr(self.master, "frame_ogrenciler"):
            ogrenciler = self.master.frame_ogrenciler.ogrenci_listesi
        for ogr in ogrenciler:
            btn = ctk.CTkButton(self.scroll_liste, text=ogr.get("Ad Soyad", "-"), fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F0F0F0", anchor="w", command=lambda o=ogr: self.ogrenci_sec(o))
            btn.pack(fill="x", pady=2)

    def verileri_buluttan_cek(self):
        if not self.db: return
        try:
            k = self.db.collection("soru_kayitlari").stream()
            self.soru_kayitlari = [doc.to_dict() | {"id": doc.id} for doc in k]
            h = self.db.collection("soru_hedefleri").stream()
            self.hedefler = [doc.to_dict() | {"id": doc.id} for doc in h]
        except Exception as e: print(f"Soru verisi hatası: {e}")

    def ogrenci_sec(self, ogrenci):
        self.secili_ogrenci = ogrenci
        
        # --- DÜZELTME BAŞLANGICI ---
        # place_forget yapmadan önce lbl_info'nun varlığını ve görselleştirilmiş olduğunu kontrol et
        if hasattr(self, 'lbl_info') and self.lbl_info.winfo_exists():
            try:
                self.lbl_info.place_forget()
            except Exception:
                pass # Hata oluşursa görmezden gel
        # --- DÜZELTME BİTİŞİ ---

        # Ekranı temizle
        for widget in self.main_content.winfo_children(): 
            widget.destroy()
        
        # UI Yeniden Oluşturma
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text=f"{ogrenci['Ad Soyad']} - Haftalık Soru Takibi", 
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")

        # Hedef Belirleme Alanı
        hedef_frame = ctk.CTkFrame(self.main_content, fg_color="#F9F9F9", corner_radius=10)
        hedef_frame.pack(fill="x", padx=20, pady=10)
        
        mevcut_hedef = next((h.get("hedef", 0) for h in self.hedefler if h.get("ogrenci_id") == ogrenci["id"] and h.get("hafta") == self.guncel_hafta), 0)
        
        ctk.CTkLabel(hedef_frame, text=f"Bu Haftaki Hedef: {mevcut_hedef} Soru", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20, pady=15)
        
        ent_hedef = ctk.CTkEntry(hedef_frame, placeholder_text="Yeni Hedef", width=100)
        ent_hedef.pack(side="left", padx=10)
        
        def hedef_kaydet():
            yeni_hedef = ent_hedef.get()
            if not yeni_hedef.isdigit(): return
            veri = {"ogrenci_id": ogrenci["id"], "hafta": self.guncel_hafta, "hedef": int(yeni_hedef)}
            if self.db: self.db.collection("soru_hedefleri").add(veri)
            self.hedefler.append(veri)
            self.ogrenci_sec(ogrenci) # Yenile
            
        ctk.CTkButton(hedef_frame, text="Güncelle", width=80, fg_color=self.COLOR_SIDEBAR, command=hedef_kaydet).pack(side="left", padx=5)

        # İlerleme Çubuğu
        cozulen = sum(int(s.get("soru_sayisi", 0)) for s in self.soru_kayitlari if s.get("ogrenci_id") == ogrenci["id"] and s.get("hafta") == self.guncel_hafta)
        yuzde = (cozulen / mevcut_hedef * 100) if mevcut_hedef > 0 else 0
        yuzde = min(yuzde, 100)
        
        prog_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        prog_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(prog_frame, text=f"Çözülen: {cozulen} Soru (%{int(yuzde)})", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.COLOR_ACCENT_GOLD).pack(anchor="w")
        pbar = ctk.CTkProgressBar(prog_frame, progress_color=self.COLOR_SIDEBAR, fg_color="#E0E0E0")
        pbar.pack(fill="x", pady=5)
        pbar.set(yuzde / 100)

        # Yeni Kayıt Ekle
        kayit_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        kayit_frame.pack(fill="x", padx=20, pady=10)
        cmb_ders = ctk.CTkOptionMenu(kayit_frame, values=["Matematik", "Türkçe", "Fen Bilimleri", "Sosyal Bilgiler", "İngilizce"], width=150)
        cmb_ders.pack(side="left")
        ent_soru = ctk.CTkEntry(kayit_frame, placeholder_text="Çözülen Soru Sayısı", width=150)
        ent_soru.pack(side="left", padx=10)
        
        def soru_ekle():
            if not ent_soru.get().isdigit(): return
            
            yeni_sayi = int(ent_soru.get())
            veri = {
                "ogrenci_id": ogrenci["id"], 
                "hafta": self.guncel_hafta, 
                "ders": cmb_ders.get(), 
                "soru_sayisi": yeni_sayi, 
                "tarih": datetime.now().strftime("%d.%m.%Y")
            }
            
            if self.db:
                doc_ref = self.db.collection("soru_kayitlari").document()
                veri["id"] = doc_ref.id
                doc_ref.set(veri)
            
            self.soru_kayitlari.append(veri)
            
            # --- 1. ADIM: Haftalık toplamı yeniden hesapla ---
            toplam_soru = sum(int(s.get("soru_sayisi", 0)) for s in self.soru_kayitlari 
                             if s.get("ogrenci_id") == ogrenci["id"] and s.get("hafta") == self.guncel_hafta)
            
            # --- 2. ADIM: Buluta senkronize et ---
            # Not: SoruTakip ekranında deneme neti bilgisi olmadığı için "0.00" veya 
            # mevcut neti buradan çekmen gerekebilir. 
            # Eğer neti bilmiyorsan "0.00" göndermek grafiği bozmaz.
            if hasattr(self.master, "_ogrenci_verilerini_buluta_guncelle"):
                self.master._ogrenci_verilerini_buluta_guncelle(ogrenci["Ad Soyad"], toplam_soru, "0.00")
            
            self.ogrenci_sec(ogrenci) # Ekranı yenile