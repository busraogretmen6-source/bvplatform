import customtkinter as ctk
from database import get_db
from datetime import datetime
import tkinter.messagebox as messagebox

class MuhasebeView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        
        self.db = get_db()
        self.aktif_sekme = "takip"
        self.secili_kayit = None
        
        # Üst Panel
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(self.header_frame, text="Muhasebe Yönetimi", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(side="left")

        # Butonlar
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=40, pady=(0, 20))

        self.btn_takip_tab = ctk.CTkButton(self.btn_frame, text="Ödeme Takibi", width=150, corner_radius=20, fg_color=self.COLOR_SIDEBAR, command=lambda: self.sekme_degistir("takip"))
        self.btn_takip_tab.pack(side="left", padx=(0, 10))

        self.btn_gecmis_tab = ctk.CTkButton(self.btn_frame, text="Ödeme Geçmişi", width=150, corner_radius=20, fg_color="#E0E0E0", text_color="black", command=lambda: self.sekme_degistir("gecmis"))
        self.btn_gecmis_tab.pack(side="left")

        self.btn_duzenle = ctk.CTkButton(self.btn_frame, text="Düzenle", fg_color="#F39C12", width=120, command=self.ac_duzenleme_popup)
        self.btn_duzenle.pack(side="right", padx=10)

        # Başlıklar
        self.baslik_frame = ctk.CTkFrame(self, fg_color=self.COLOR_SIDEBAR, corner_radius=10)
        self.baslik_frame.pack(fill="x", padx=40, pady=(0, 10))
        self.olustur_basliklar()

        self.liste_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.liste_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))

    def olustur_basliklar(self):
        for w in self.baslik_frame.winfo_children(): w.destroy()
        # 5 sütun yapısı: Ad, Tutar, Gün, Durum, İşlem
        cols = ["Öğrenci Adı", "Ücret Tutarı", "Ödeme Günü", "Durum", "İşlem"]
        self.baslik_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        for i, col in enumerate(cols):
            ctk.CTkLabel(self.baslik_frame, text=col, font=ctk.CTkFont(weight="bold"), text_color="white").grid(row=0, column=i, padx=20, pady=10, sticky="w")

    def sekme_degistir(self, yeni_sekme):
        self.aktif_sekme = yeni_sekme
        self.secili_kayit = None
        self.listeyi_guncelle()

    def listeyi_guncelle(self):
        for w in self.liste_frame.winfo_children(): w.destroy()
        if self.aktif_sekme == "takip": self.goster_odeme_takibi()
        else: self.goster_odeme_gecmisi()

    def goster_odeme_takibi(self):
        ogrenciler = self.master.frame_ogrenciler.ogrenci_listesi if hasattr(self.master, "frame_ogrenciler") else []
        
        # Filtreleme yapalım: Sadece "Ödenmedi" olanları göster
        aktif_ogrenciler = [o for o in ogrenciler if o.get("odeme_durumu", "Ödenmedi") == "Ödenmedi"]
        
        for ogrenci in aktif_ogrenciler:
            satir = ctk.CTkFrame(self.liste_frame, fg_color="transparent")
            satir.pack(fill="x", pady=2, padx=5)
            satir.grid_columnconfigure((0,1,2,3,4), weight=1)
            
            satir.bind("<Button-1>", lambda e, o=ogrenci, s=satir: self.sec(o, s))
            
            ctk.CTkLabel(satir, text=ogrenci.get("Ad Soyad", "-")).grid(row=0, column=0, padx=20, sticky="w")
            ctk.CTkLabel(satir, text=ogrenci.get("Ücret Bilgisi", "-")).grid(row=0, column=1, padx=20, sticky="w")
            ctk.CTkLabel(satir, text=ogrenci.get("Ödeme Günü", "-")).grid(row=0, column=2, padx=20, sticky="w")
            
            # Durum Değiştirme
            durum = "Ödenmedi"
            cmb = ctk.CTkOptionMenu(satir, values=["Ödenmedi", "Ödendi"], width=100, fg_color="#D32F2F")
            cmb.set(durum)
            # command kısmında tetiklenen fonksiyona doğrudan self.listeyi_guncelle ekliyoruz
            cmb.configure(command=lambda val, o=ogrenci, c=cmb: self.durum_degistir_takip(val, o, c))
            cmb.grid(row=0, column=3, padx=20, pady=5, sticky="w")
            
            ctk.CTkLabel(satir, text="-").grid(row=0, column=4, padx=20, sticky="w")

    def durum_degistir_takip(self, val, o):
        # 1. Veritabanını güncelle
        self.db.collection("ogrenciler").document(o["id"]).update({"odeme_durumu": val})
        
        # 2. Programın belleğindeki listeyi de güncelle ki anında yansısın
        o["odeme_durumu"] = val 
        
        if val == "Ödendi":
            # Ödeme geçmişine ekle
            self.db.collection("odemeler").add({
                "ogrenci_id": o["id"], 
                "ad": o["Ad Soyad"], 
                "tutar": o.get("Ücret Bilgisi", "-"), 
                "tarih": datetime.now().strftime("%d.%m.%Y")
            })
            # Listeyi tazele
            self.listeyi_guncelle()

    def goster_odeme_gecmisi(self):
        docs = self.db.collection("odemeler").stream()
        for doc in docs:
            odeme = doc.to_dict()
            odeme["id"] = doc.id
            satir = ctk.CTkFrame(self.liste_frame, fg_color="transparent")
            satir.pack(fill="x", pady=2, padx=5)
            satir.grid_columnconfigure((0,1,2,3,4), weight=1)
            
            ctk.CTkLabel(satir, text=odeme.get("ad", "-")).grid(row=0, column=0, padx=20, sticky="w")
            ctk.CTkLabel(satir, text=odeme.get("tutar", "-")).grid(row=0, column=1, padx=20, sticky="w")
            ctk.CTkLabel(satir, text=odeme.get("tarih", "-")).grid(row=0, column=2, padx=20, sticky="w")
            ctk.CTkLabel(satir, text="Ödendi", text_color="#388E3C").grid(row=0, column=3, padx=20, sticky="w")
            ctk.CTkButton(satir, text="Geri Al", fg_color="#D32F2F", width=80, command=lambda o=odeme: self.geri_al(o)).grid(row=0, column=4, padx=20, sticky="w")

    def sec(self, o, s):
        self.secili_kayit = o
        for w in self.liste_frame.winfo_children(): w.configure(fg_color="transparent")
        s.configure(fg_color="#E8F5E9")

    def durum_degistir_takip(self, val, o, c):
        # 1. Veritabanını güncelle
        self.db.collection("ogrenciler").document(o["id"]).update({"odeme_durumu": val})
        
        # 2. Bellekteki öğrenci objesini güncelle
        o["odeme_durumu"] = val 
        
        if val == "Ödendi":
            self.db.collection("odemeler").add({
                "ogrenci_id": o["id"], 
                "ad": o["Ad Soyad"], 
                "tutar": o.get("Ücret Bilgisi", "-"), 
                "tarih": datetime.now().strftime("%d.%m.%Y")
            })
            c.configure(fg_color="#388E3C")
        else:
            c.configure(fg_color="#D32F2F")

        # 3. YENİ: Arayüzü tazele
        self.verileri_ve_listeyi_tazele()

    def geri_al(self, odeme):
        try:
            # 1. Ödemelerden kaydı sil
            self.db.collection("odemeler").document(odeme["id"]).delete()
            
            # 2. Öğrenci durumunu güncelle
            self.db.collection("ogrenciler").document(odeme["ogrenci_id"]).update({"odeme_durumu": "Ödenmedi"})
            
            # 3. Bellekteki öğrenci listesini bul ve "Ödenmedi" olarak düzelt
            if hasattr(self.master, "frame_ogrenciler"):
                for ogrenci in self.master.frame_ogrenciler.ogrenci_listesi:
                    if ogrenci["id"] == odeme["ogrenci_id"]:
                        ogrenci["odeme_durumu"] = "Ödenmedi"
                        break
            
            # 4. Otomatik olarak Ödeme Takibi sayfasına geç ve listeyi güncelle
            self.sekme_degistir("takip")
            messagebox.showinfo("Başarılı", "Ödeme geri alındı ve Takip sayfasına eklendi.")
            
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu: {e}")

    def ac_duzenleme_popup(self):
        if not self.secili_kayit:
            messagebox.showwarning("Uyarı", "Lütfen bir satır seçin.")
            return
        
        popup = ctk.CTkToplevel(self)
        popup.title("Düzenle")
        popup.geometry("350x350") # Yüksekliği 350 yaptık ki buton kesin sığsın
        popup.attributes("-topmost", True)
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="Ücret Tutarı:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        ent_ucret = ctk.CTkEntry(popup, width=250)
        ent_ucret.insert(0, self.secili_kayit.get("Ücret Bilgisi", ""))
        ent_ucret.pack()

        ctk.CTkLabel(popup, text="Ödeme Günü:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        ent_gun = ctk.CTkEntry(popup, width=250)
        ent_gun.insert(0, self.secili_kayit.get("Ödeme Günü", ""))
        ent_gun.pack()

        def kaydet():
            # Veritabanını güncelle
            self.db.collection("ogrenciler").document(self.secili_kayit["id"]).update({
                "Ücret Bilgisi": ent_ucret.get(), 
                "Ödeme Günü": ent_gun.get()
            })
            
            # Belleği güncelle
            self.secili_kayit["Ücret Bilgisi"] = ent_ucret.get()
            self.secili_kayit["Ödeme Günü"] = ent_gun.get()
            
            messagebox.showinfo("Başarılı", "Güncellendi.")
            popup.destroy()
            
            # Ekranı anında tazele
            self.verileri_ve_listeyi_tazele()

        # Kaydet butonu burada:
        ctk.CTkButton(popup, text="Kaydet", fg_color=self.COLOR_SIDEBAR, height=40, command=kaydet).pack(pady=30)

    def verileri_ve_listeyi_tazele(self):
        # 1. Master'daki öğrenci listesini veritabanından yeniden çek (eğer metodu varsa)
        if hasattr(self.master, "frame_ogrenciler"):
            self.master.frame_ogrenciler.verileri_buluttan_cek()
        
        # 2. Muhasebe listesini yeniden çiz
        self.listeyi_guncelle()
