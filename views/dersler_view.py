import customtkinter as ctk
import datetime
import tkinter as tk
import tkinter.messagebox as messagebox
from database import get_db

class DerslerView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Değişkenleri en başta tanımla
        self.btn_sil = None
        self.db = get_db()
        self.ders_listesi = []
        self.secili_ogrenci_adi = None
        self.gosterilen_tarih = datetime.date.today()

        # Renk Paleti
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        
        # Arayüzü oluştur ve verileri çek
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        # 1. Header Frame (Doğrudan self üzerine pack ediliyor)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=40, pady=20) 
        
        ctk.CTkLabel(self.header_frame, text="Ders Yönetimi", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(side="left")

        # Buton oluşturuldu ama henüz görünür değil (Öğrenci seçilince görünecek)
        self.btn_sil = ctk.CTkButton(
            self.header_frame, text="Tümünü Sil", 
            fg_color="#D32F2F", hover_color="#B71C1C",
            text_color="white", corner_radius=8, height=40, width=120,
            command=self.secili_ogrencinin_derslerini_sil
        )
        
        self.btn_yeni_ders = ctk.CTkButton(
            self.header_frame, text="Yeni Ders Ekle", font=ctk.CTkFont(size=14, weight="bold"), 
            fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER,
            text_color=self.COLOR_TEXT_LIGHT, corner_radius=8, height=40,
            command=self.ac_ders_ekle_popup
        )
        self.btn_yeni_ders.pack(side="right")

        # 2. Navigasyon
        self.nav_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.nav_frame.pack(fill="x", padx=40, pady=(0, 10))
        
        btn_onceki = ctk.CTkButton(self.nav_frame, text="<", width=40, fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F0F0F0", command=self.onceki_hafta)
        btn_onceki.pack(side="left", padx=5, pady=5)
        
        self.lbl_hafta = ctk.CTkLabel(self.nav_frame, text=self.get_hafta_metni(self.gosterilen_tarih), font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_SIDEBAR)
        self.lbl_hafta.pack(side="left", expand=True)
        
        btn_sonraki = ctk.CTkButton(self.nav_frame, text=">", width=40, fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F0F0F0", command=self.sonraki_hafta)
        btn_sonraki.pack(side="right", padx=5, pady=5)

        # 3. Liste ve Detay Taşıyıcı
        self.orta_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.orta_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        # Liste (Sol taraf)
        self.frame_liste = ctk.CTkScrollableFrame(self.orta_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0", width=300)
        self.frame_liste.pack(side="left", fill="y", padx=(0, 20)) 

        # Detay (Sağ taraf)
        self.frame_detay = ctk.CTkScrollableFrame(self.orta_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.frame_detay.pack(side="left", fill="both", expand=True) 
        
        self.lbl_bos_durum = ctk.CTkLabel(self.frame_detay, text="Dersleri görmek için sol taraftan\nbir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
        self.lbl_bos_durum.pack(pady=150)

    def verileri_buluttan_cek(self):
        if not self.db: return
        try:
            docs = self.db.collection("dersler").stream()
            self.ders_listesi = []
            for doc in docs:
                veri = doc.to_dict()
                veri["id"] = doc.id
                self.ders_listesi.append(veri)
            self.listeyi_guncelle()
        except Exception as e:
            print(f"Ders verisi çekme hatası: {e}")

    def get_iso_text_tarih(self, tarih, gun_adi):
        gunler_indeks = {"Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4, "Cumartesi": 5, "Pazar": 6}
        pazartesi = tarih - datetime.timedelta(days=tarih.weekday())
        hedef_gun = pazartesi + datetime.timedelta(days=gunler_indeks[gun_adi])
        return hedef_gun.strftime("%Y-%m-%d")

    def get_iso_text_hafta(self, tarih):
        return tarih.strftime("%G-W%V")

    def get_hafta_metni(self, tarih):
        pazartesi = tarih - datetime.timedelta(days=tarih.weekday())
        pazar = pazartesi + datetime.timedelta(days=6)
        return f"{pazartesi.strftime('%d.%m.%Y')} - {pazar.strftime('%d.%m.%Y')}"

    def onceki_hafta(self):
        self.gosterilen_tarih -= datetime.timedelta(weeks=1)
        self.hafta_guncelle()

    def sonraki_hafta(self):
        self.gosterilen_tarih += datetime.timedelta(weeks=1)
        self.hafta_guncelle()

    def hafta_guncelle(self):
        self.lbl_hafta.configure(text=self.get_hafta_metni(self.gosterilen_tarih))
        self.secili_ogrenci_adi = None
        if self.btn_sil.winfo_ismapped():
            self.btn_sil.pack_forget()
        self.sag_paneli_temizle()
        self.listeyi_guncelle()

    def sag_paneli_temizle(self):
        for widget in self.frame_detay.winfo_children(): widget.destroy()
        self.lbl_bos_durum = ctk.CTkLabel(self.frame_detay, text="Dersleri görmek için sol taraftan\nbir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
        self.lbl_bos_durum.pack(pady=150)

    def listeyi_guncelle(self):
        for widget in self.frame_liste.winfo_children(): widget.destroy()
        if not self.secili_ogrenci_adi and self.btn_sil.winfo_ismapped(): 
            self.btn_sil.pack_forget()

        guncel_hafta_iso = self.get_iso_text_hafta(self.gosterilen_tarih)
        bu_haftanin_dersleri = [d for d in self.ders_listesi if d.get("yil_hafta") == guncel_hafta_iso]
        
        if not bu_haftanin_dersleri:
            ctk.CTkLabel(self.frame_liste, text="Bu haftaya ait\nkayıtlı ders yok.", font=ctk.CTkFont(slant="italic"), text_color="gray50").pack(pady=50)
            return

        ogrenciler = sorted(list(set([d.get("Öğrenci") for d in bu_haftanin_dersleri])))
        for ogrenci in ogrenciler:
            btn = ctk.CTkButton(
                self.frame_liste, text=ogrenci, font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F0F0F0",
                anchor="w", height=40, command=lambda o=ogrenci: self.ogrencinin_derslerini_goster(o)
            )
            btn.pack(fill="x", pady=2, padx=5)
            btn.bind("<Button-3>", lambda e, o=ogrenci: self.sag_tik_menusu(e, o))
            btn.bind("<Button-2>", lambda e, o=ogrenci: self.sag_tik_menusu(e, o))

    def ogrencinin_derslerini_goster(self, ogrenci_adi):
        for widget in self.frame_detay.winfo_children(): widget.destroy()
        self.secili_ogrenci_adi = ogrenci_adi
        self.btn_sil.pack(side="right", padx=(0, 10))
        
        guncel_hafta_iso = self.get_iso_text_hafta(self.gosterilen_tarih)
        ogrencinin_dersleri = [d for d in self.ders_listesi if d.get("yil_hafta") == guncel_hafta_iso and d.get("Öğrenci") == ogrenci_adi]
        
        baslik_lbl = ctk.CTkLabel(self.frame_detay, text=f"{ogrenci_adi} - Bu Haftaki Dersleri", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.COLOR_SIDEBAR)
        baslik_lbl.pack(anchor="w", padx=20, pady=(20, 10))
        
        cizgi = ctk.CTkFrame(self.frame_detay, height=2, fg_color=self.COLOR_ACCENT_GOLD)
        cizgi.pack(fill="x", padx=20, pady=(0, 20))

        for ders in ogrencinin_dersleri:
            kart = ctk.CTkFrame(self.frame_detay, fg_color="#F9F9F9", corner_radius=10, border_width=1, border_color="#E0E0E0")
            kart.pack(fill="x", padx=20, pady=10)
            
            btn_kart_sil = ctk.CTkButton(kart, text="Sil", width=40, height=24, fg_color="#D32F2F", hover_color="#B71C1C", font=ctk.CTkFont(size=11), command=lambda d=ders: self.tek_ders_sil(d))
            btn_kart_sil.place(relx=0.95, rely=0.1, anchor="ne")
            
            ctk.CTkLabel(kart, text=ders.get("Ders Adı", "-"), font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(anchor="w", padx=15, pady=(15, 5))
            ctk.CTkLabel(kart, text=f"Konu: {ders.get('Konu / Kategori', '-')}", font=ctk.CTkFont(size=13), text_color="gray40").pack(anchor="w", padx=15, pady=0)
            
            gun_saat = f"{ders.get('Gün', '')} | {ders.get('Saat', '')}"
            ctk.CTkLabel(kart, text=gun_saat, font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_SIDEBAR, justify="left").pack(anchor="w", padx=15, pady=(10, 5))
            
            link = ders.get("Online Link", "-")
            if link and link != "-":
                ctk.CTkLabel(kart, text=f"Link: {link}", font=ctk.CTkFont(size=12, slant="italic", underline=True), text_color="blue").pack(anchor="w", padx=15, pady=(0, 15))
            else:
                ctk.CTkLabel(kart, text="Link Eklenmemiş", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray60").pack(anchor="w", padx=15, pady=(0, 15))

    def sag_tik_menusu(self, event, ogrenci_adi):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Bu Haftaki Derslerini Sil", command=lambda: self.secili_ogrencinin_derslerini_sil(ogrenci_adi))
        menu.tk_popup(event.x_root, event.y_root)

    def tek_ders_sil(self, ders):
        cevap = messagebox.askyesno("Ders Silme", f"{ders.get('Ders Adı', 'Bu dersi')} silmek istediğinize emin misiniz?")
        if cevap:
            if self.db and "id" in ders:
                try:
                    self.db.collection("dersler").document(ders["id"]).delete()
                except Exception as e:
                    print(f"Ders silme hatası: {e}")
                    
            self.ders_listesi = [d for d in self.ders_listesi if d.get("id") != ders.get("id")]
            if self.secili_ogrenci_adi:
                self.ogrencinin_derslerini_goster(self.secili_ogrenci_adi)
            self.listeyi_guncelle()
            
            if hasattr(self.master, "guncelle_ana_sayfa"):
                self.master.guncelle_ana_sayfa()

    def secili_ogrencinin_derslerini_sil(self, ogrenci_adi=None):
        ogr_adi = ogrenci_adi or self.secili_ogrenci_adi
        if not ogr_adi: return
        
        guncel_hafta_iso = self.get_iso_text_hafta(self.gosterilen_tarih)
        silinecek_dersler = [d for d in self.ders_listesi if d.get("yil_hafta") == guncel_hafta_iso and d.get("Öğrenci") == ogr_adi]
        
        if not silinecek_dersler: return
        
        cevap = messagebox.askyesno("Tümünü Sil", f"{ogr_adi} isimli öğrencinin bu haftaki ({len(silinecek_dersler)}) adet dersini silmek istediğinize emin misiniz?")
        if cevap:
            if self.db:
                for ders in silinecek_dersler:
                    if "id" in ders:
                        try: self.db.collection("dersler").document(ders["id"]).delete()
                        except: pass
                            
            silinecek_idler = [d.get("id") for d in silinecek_dersler if "id" in d]
            self.ders_listesi = [d for d in self.ders_listesi if d.get("id") not in silinecek_idler]
            
            if self.secili_ogrenci_adi == ogr_adi:
                self.btn_sil.pack_forget()
                self.secili_ogrenci_adi = None
                self.sag_paneli_temizle()
                
            self.listeyi_guncelle()
            if hasattr(self.master, "guncelle_ana_sayfa"):
                self.master.guncelle_ana_sayfa()

    def ac_ders_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Yeni Ders")
        popup.geometry("550x650")
        popup.configure(fg_color="#F4F1EA")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Ders Oluşturma Formu", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(pady=(20, 5))
        bilgi_notu = f"Bu ders {self.get_hafta_metni(self.gosterilen_tarih)} haftasına eklenecek."
        ctk.CTkLabel(popup, text=bilgi_notu, font=ctk.CTkFont(size=12, slant="italic"), text_color=self.COLOR_ACCENT_GOLD).pack(pady=(0, 15))

        form_frame = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        form_frame.grid_columnconfigure(1, weight=1)

        girdiler = {}
        satir = 0

        def ekle_satir(baslik, widget):
            nonlocal satir
            lbl = ctk.CTkLabel(form_frame, text=baslik, width=120, anchor="w", text_color=self.COLOR_TEXT_DARK)
            lbl.grid(row=satir, column=0, pady=10, sticky="w")
            widget.grid(row=satir, column=1, pady=10, padx=(10, 0), sticky="ew")
            satir += 1
            return widget

        ogrenci_isimleri = ["(Kayıtlı Öğrenci Yok)"]
        try:
            if hasattr(self.master, "frame_ogrenciler") and self.master.frame_ogrenciler.ogrenci_listesi:
                ogrenci_isimleri = [ogr["Ad Soyad"] for ogr in self.master.frame_ogrenciler.ogrenci_listesi]
        except Exception: pass

        cmb_ogrenci = ctk.CTkOptionMenu(form_frame, values=ogrenci_isimleri, fg_color="white", text_color="black", button_color=self.COLOR_SIDEBAR, button_hover_color=self.COLOR_SIDEBAR_HOVER)
        girdiler["Öğrenci"] = ekle_satir("Öğrenci Seçin:", cmb_ogrenci)
        girdiler["Ders Adı"] = ekle_satir("Ders Adı:", ctk.CTkEntry(form_frame, placeholder_text="Örn: İleri Cebir"))
        girdiler["Konu / Kategori"] = ekle_satir("Konu / Kategori:", ctk.CTkEntry(form_frame, placeholder_text="Örn: Polinomlar"))
        girdiler["Online Link"] = ekle_satir("Online Ders Linki:", ctk.CTkEntry(form_frame, placeholder_text="Örn: Zoom / Meet linki"))

        lbl_gun = ctk.CTkLabel(form_frame, text="Gün Seçimi:", width=120, anchor="w", text_color=self.COLOR_TEXT_DARK)
        lbl_gun.grid(row=satir, column=0, pady=10, sticky="nw")
        
        gunler_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        gunler_frame.grid(row=satir, column=1, pady=10, padx=(10, 0), sticky="ew")
        satir += 1

        saat_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        saat_frame.grid(row=satir, column=0, columnspan=2, pady=5, sticky="ew")
        saat_frame.grid_columnconfigure(1, weight=1)
        satir += 1

        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.gun_vars = {}
        self.saat_widgets = {}

        saat_listesi = [f"{i:02d}:00 - {(i+1)%24:02d}:00" for i in range(24)]

        def guncelle_saatler():
            for widget in saat_frame.winfo_children(): widget.destroy()
            self.saat_widgets.clear()
            row_idx = 0
            for gun in gunler:
                if self.gun_vars[gun].get() == "1":
                    lbl = ctk.CTkLabel(saat_frame, text=f"{gun} Saati:", width=120, anchor="w", text_color=self.COLOR_TEXT_DARK)
                    lbl.grid(row=row_idx, column=0, pady=5, sticky="w")
                    
                    ent = ctk.CTkOptionMenu(
                        saat_frame, 
                        values=saat_listesi, 
                        fg_color="white", 
                        text_color="black", 
                        button_color=self.COLOR_SIDEBAR, 
                        button_hover_color=self.COLOR_SIDEBAR_HOVER
                    )
                    ent.set("15:00 - 16:00") 
                    ent.grid(row=row_idx, column=1, pady=5, padx=(10, 0), sticky="ew")
                    
                    self.saat_widgets[gun] = ent
                    row_idx += 1

        for i, gun in enumerate(gunler):
            var = ctk.StringVar(value="0")
            self.gun_vars[gun] = var
            chk = ctk.CTkCheckBox(gunler_frame, text=gun, variable=var, onvalue="1", offvalue="0", command=guncelle_saatler, text_color=self.COLOR_TEXT_DARK, fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER)
            chk.grid(row=i//2, column=i%2, pady=5, padx=5, sticky="w")

        def kaydet_tiklandi():
            secilen_gunler = [gun for gun in gunler if self.gun_vars[gun].get() == "1"]
            if not secilen_gunler:
                messagebox.showwarning("Uyarı", "Lütfen en az bir gün seçin.")
                return

            guncel_hafta_iso = self.get_iso_text_hafta(self.gosterilen_tarih)
            
            for gun in secilen_gunler:
                girilen_saat = self.saat_widgets[gun].get()
                
                cakisma_var = False
                cakisan_bilgi = ""
                for d in self.ders_listesi:
                    if d.get("yil_hafta") == guncel_hafta_iso and d.get("Gün") == gun and d.get("Saat") == girilen_saat:
                        cakisma_var = True
                        cakisan_bilgi = f"Öğrenci: {d.get('Öğrenci')} \nDers: {d.get('Ders Adı')} \nSaat: {gun} {girilen_saat}"
                        break
                        
                if cakisma_var:
                    cevap = messagebox.askyesno(
                        "⚠️ Takvim Çakışması!", 
                        f"Seçtiğiniz gün ve saatte halihazırda başka bir dersiniz bulunuyor:\n\n{cakisan_bilgi}\n\nEmin misiniz? Dersleri aynı saate kaydetmek (grup dersi) istiyor musunuz?"
                    )
                    if not cevap: return

                yeni_ders = {
                    "Öğrenci": girdiler["Öğrenci"].get(),
                    "Ders Adı": girdiler["Ders Adı"].get(),
                    "Ders": girdiler["Ders Adı"].get(), 
                    "Konu / Kategori": girdiler["Konu / Kategori"].get(),
                    "Online Link": girdiler["Online Link"].get(),
                    "yil_hafta": guncel_hafta_iso,
                    "tarih": self.get_iso_text_tarih(self.gosterilen_tarih, gun), 
                    "Gün": gun,
                    "Saat": girilen_saat,
                    "saat": girilen_saat, 
                    "Gün ve Saat": f"{gun}: {girilen_saat}"
                }
                
                if self.db:
                    try:
                        doc_ref = self.db.collection("dersler").document()
                        yeni_ders["id"] = doc_ref.id
                        doc_ref.set(yeni_ders)
                    except Exception as e:
                        print(f"Ders kaydetme hatası: {e}")

                self.ders_listesi.append(yeni_ders)

            self.listeyi_guncelle()
            
            if hasattr(self.master, "guncelle_ana_sayfa"):
                self.master.guncelle_ana_sayfa()
            elif hasattr(self, "master") and hasattr(self.master, "master") and hasattr(self.master.master, "guncelle_ana_sayfa"):
                self.master.master.guncelle_ana_sayfa()
            elif hasattr(self.master, "frame_ana_sayfa") and hasattr(self.master.frame_ana_sayfa, "guncelle_takvim"):
                self.master.frame_ana_sayfa.guncelle_takvim()
                
            popup.destroy()

        ctk.CTkButton(popup, text="Kaydet", font=ctk.CTkFont(size=14, weight="bold"), fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER, text_color=self.COLOR_TEXT_LIGHT, height=40, command=kaydet_tiklandi).pack(pady=(10, 20))