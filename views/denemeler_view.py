import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from database import get_db
from datetime import datetime
import os
import shutil
import smtplib
from email.message import EmailMessage

class DenemelerView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        
        self.db = get_db()
        self.deneme_listesi = []
        self.secili_ogrenci = None
        self.secilen_dosya_yolu = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        # Sol Taraf: Öğrenci Seçimi
        self.sidebar_liste = ctk.CTkFrame(self, width=200, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.sidebar_liste.grid(row=0, column=0, padx=(40, 10), pady=40, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_liste, text="Öğrenci Seçin", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        self.scroll_liste = ctk.CTkScrollableFrame(self.sidebar_liste, fg_color="transparent")
        self.scroll_liste.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sağ Taraf: Deneme Detayları
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Deneme dosyalarını görmek için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")

    def listeyi_yenile(self):
        for widget in self.scroll_liste.winfo_children(): widget.destroy()
        ogrenciler = getattr(self.master, "frame_ogrenciler", None)
        if ogrenciler:
            for ogr in ogrenciler.ogrenci_listesi:
                btn = ctk.CTkButton(self.scroll_liste, text=ogr.get("Ad Soyad", "-"), fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F0F0F0", anchor="w", command=lambda o=ogr: self.ogrenci_sec(o))
                btn.pack(fill="x", pady=2)

    def verileri_buluttan_cek(self):
        if not self.db: return
        try:
            docs = self.db.collection("denemeler").stream()
            self.deneme_listesi = [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e: print(f"Hata: {e}")

    def ogrenci_sec(self, ogrenci):
        self.secili_ogrenci = ogrenci
        if hasattr(self, 'lbl_info') and self.lbl_info.winfo_exists(): self.lbl_info.place_forget()
        for widget in self.main_content.winfo_children(): widget.destroy()
        
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text=f"{ogrenci['Ad Soyad']} - Deneme Takibi", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")
        ctk.CTkButton(header, text="+ Yeni Deneme Ekle", fg_color=self.COLOR_SIDEBAR, command=self.ac_deneme_ekle_popup).pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.sonuclari_listele()

    def sonuclari_listele(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        ogr_denemeler = [d for d in self.deneme_listesi if d.get("ogrenci_id") == self.secili_ogrenci["id"]]
        
        for d in reversed(ogr_denemeler):
            card = ctk.CTkFrame(self.list_frame, fg_color="#F9F9F9", corner_radius=10, border_width=1, border_color="#EEEEEE")
            card.pack(fill="x", pady=5)
            ctk.CTkLabel(card, text=f"{d.get('sinav_adi')} ({d.get('toplam_soru', 0)} Soru)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20, pady=15)
            
            def dosya_ac(path=d.get("dosya_yolu")):
                if path and os.path.exists(path): os.startfile(path)
                else: messagebox.showwarning("Hata", "Dosya bulunamadı.")
            
            ctk.CTkButton(card, text="📄 Aç", width=60, command=dosya_ac).pack(side="right", padx=10)

    def ac_deneme_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Yeni Deneme Gönderimi")
        popup.geometry("400x450")
        popup.attributes("-topmost", True)
        
        ent_ad = ctk.CTkEntry(popup, placeholder_text="Sınav Adı", width=300)
        ent_ad.pack(pady=20)
        
        ent_soru = ctk.CTkEntry(popup, placeholder_text="Toplam Soru Sayısı", width=300)
        ent_soru.pack(pady=10)
        
        # --- WEB PORTALI İÇİN YENİ GİRİŞ ALANI ---
        ent_net = ctk.CTkEntry(popup, placeholder_text="Deneme Neti (Örn: 45.5)", width=300)
        ent_net.pack(pady=10)

        def dosya_sec():
            self.secilen_dosya_yolu = filedialog.askopenfilename(filetypes=[("PDF/Resim", "*.pdf *.png *.jpg *.jpeg")])
            if self.secilen_dosya_yolu: btn_dosya.configure(text=os.path.basename(self.secilen_dosya_yolu))

        btn_dosya = ctk.CTkButton(popup, text="Dosya Seç", command=dosya_sec)
        btn_dosya.pack(pady=10)

        def kaydet():
            if not self.secilen_dosya_yolu or not ent_ad.get() or not ent_soru.get() or not ent_net.get():
                messagebox.showwarning("Uyarı", "Tüm alanları doldurun ve dosya seçin.")
                return

            hedef_klasor = r"G:\Drive'ım\Denemeler"
            os.makedirs(hedef_klasor, exist_ok=True)
            dosya_adi = f"{self.secili_ogrenci['id']}_{os.path.basename(self.secilen_dosya_yolu)}"
            yeni_yol = os.path.join(hedef_klasor, dosya_adi)
            shutil.copy2(self.secilen_dosya_yolu, yeni_yol)

            yeni = {
                "ogrenci_id": self.secili_ogrenci["id"],
                "sinav_adi": ent_ad.get(),
                "toplam_soru": int(ent_soru.get()),
                "toplam_net": ent_net.get(), # Veritabanına da neti kaydediyoruz
                "dosya_yolu": yeni_yol,
                "tarih": datetime.now().strftime("%d.%m.%Y")
            }
            self.db.collection("denemeler").document().set(yeni)
            
            # --- BULUT SENKRONİZASYONU ---
            # Burada ana uygulamadaki (App sınıfı) güncelleyiciyi tetikliyoruz
            try:
                self.master._ogrenci_verilerini_buluta_guncelle(
                    self.secili_ogrenci["Ad Soyad"], 
                    int(ent_soru.get()), 
                    ent_net.get()
                )
            except Exception as e:
                print(f"Bulut senkronizasyonu yapılamadı: {e}")

            self.mail_gonder(self.secili_ogrenci, ent_ad.get(), yeni_yol)
            self.deneme_listesi.append(yeni)
            self.sonuclari_listele()
            popup.destroy()

        ctk.CTkButton(popup, text="Gönder ve Mail At", fg_color=self.COLOR_SIDEBAR, command=kaydet).pack(pady=30)

    def mail_gonder(self, ogrenci, sinav_adi, dosya_yolu):
        # SMTP ayarlarını buraya girin
        msg = EmailMessage()
        msg['Subject'] = f"Yeni Deneme: {sinav_adi}"
        msg['To'] = ogrenci.get("veli_mail", "test@test.com")
        msg.set_content(f"Merhaba, {sinav_adi} denemesi sisteme yüklendi.")
        with open(dosya_yolu, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(dosya_yolu))
        
        # smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        # smtp_server.login("seninmailin@gmail.com", "uygulama_sifren")
        # smtp_server.send_message(msg)
        # smtp_server.quit()