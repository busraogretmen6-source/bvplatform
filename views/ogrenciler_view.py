import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from PIL import Image
import os
import shutil
import urllib.parse
from firebase_admin import storage  # FOTOĞRAFLARI BULUTA YÜKLEMEK İÇİN EKLENDİ
from database import get_db

class OgrencilerView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        
        self.db = get_db()
        self.ogrenci_listesi = []
        self.secili_ogrenci = None
        
        # ------------------------------------------------------------------
        # FOTOĞRAF BULUT VE YEREL SENKRONİZASYON KLASÖRÜ
        # ------------------------------------------------------------------
        self.PROFIL_FOTO_DIZIN = r"G:\Drive'ım\Öğrenci_Profilleri"
        os.makedirs(self.PROFIL_FOTO_DIZIN, exist_ok=True)
        
        self.FIREBASE_BUCKET_NAME = "busra-hoca-platform.firebasestorage.app"
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        # --- SOL PANEL: ÖĞRENCİ LİSTESİ ---
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.sidebar.grid(row=0, column=0, padx=(40, 10), pady=40, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="Öğrenci Listesi", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.COLOR_SIDEBAR).grid(row=0, column=0, pady=(20, 10))
        
        self.btn_yeni = ctk.CTkButton(
            self.sidebar, text="ÖĞRENCİ EKLE", font=ctk.CTkFont(weight="bold"),
            fg_color=self.COLOR_ACCENT_GOLD, hover_color="#B8952E", text_color="white",
            command=self.ac_ogrenci_ekle_popup
        )
        self.btn_yeni.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        self.scroll_liste = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.scroll_liste.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # --- SAĞ PANEL: ÖĞRENCİ PROFİL DETAYI ---
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Öğrenci detaylarını görmek için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
        self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")

    def verileri_buluttan_cek(self):
        if not self.db: return
        try:
            docs = self.db.collection("ogrenciler").stream()
            self.ogrenci_listesi = []
            for doc in docs:
                veri = doc.to_dict()
                veri["id"] = doc.id
                self.ogrenci_listesi.append(veri)
            self.listeyi_yenile()
        except Exception as e:
            print(f"Veri çekme hatası: {e}")

    def listeyi_yenile(self):
        for widget in self.scroll_liste.winfo_children(): widget.destroy()
        
        sirali_liste = sorted(self.ogrenci_listesi, key=lambda x: x.get("Ad Soyad", "").lower())
        
        for ogr in sirali_liste:
            btn = ctk.CTkButton(
                self.scroll_liste, text=ogr.get("Ad Soyad", "-"), font=ctk.CTkFont(size=14),
                fg_color="transparent", text_color=self.COLOR_TEXT_DARK, hover_color="#F4F7F5",
                anchor="w", height=35, command=lambda o=ogr: self.ogrenci_detay_goster(o)
            )
            btn.pack(fill="x", pady=2)

    def ogrenci_detay_goster(self, ogrenci):
        self.secili_ogrenci = ogrenci
        
        if hasattr(self, 'lbl_info') and self.lbl_info.winfo_exists():
            self.lbl_info.place_forget()
            
        for widget in self.main_content.winfo_children(): 
            widget.destroy()

        # Üst Araç Çubuğu
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(header, text="Öğrenci Profil Kartı", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")

        self.btn_duzenle = ctk.CTkButton(header, text="DÜZENLE", fg_color="#F39C12", hover_color="#D68910", font=ctk.CTkFont(weight="bold"), width=100, command=self.ac_duzenleme_popup)
        self.btn_duzenle.pack(side="right", padx=10)
        
        btn_sil = ctk.CTkButton(header, text="SİL", width=80, fg_color="#D32F2F", hover_color="#B71C1C", font=ctk.CTkFont(weight="bold"), command=self.ogrenci_kalici_sil)
        btn_sil.pack(side="right")

        # --- PROFİL İÇERİĞİ ---
        profil_frame = ctk.CTkFrame(self.main_content, fg_color="#F9F9F9", corner_radius=15, border_width=1, border_color="#E0E0E0")
        profil_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Fotoğraf Alanı
        foto_frame = ctk.CTkFrame(profil_frame, fg_color="transparent", width=160)
        foto_frame.pack(side="left", fill="y", padx=30, pady=30)
        
        foto_yolu = ogrenci.get("foto_yolu", "")
        img_obj = None
        if foto_yolu and os.path.exists(foto_yolu):
            try:
                pil_img = Image.open(foto_yolu)
                img_obj = ctk.CTkImage(light_image=pil_img, size=(140, 180))
            except Exception: pass
            
        if img_obj:
            lbl_foto = ctk.CTkLabel(foto_frame, text="", image=img_obj, corner_radius=10)
        else:
            lbl_foto = ctk.CTkLabel(foto_frame, text="Fotoğraf\nYok", width=140, height=180, fg_color="#E0E0E0", text_color="gray50", corner_radius=10)
        lbl_foto.pack(anchor="n")

        # Bilgi Alanı
        bilgi_frame = ctk.CTkFrame(profil_frame, fg_color="transparent")
        bilgi_frame.pack(side="left", fill="both", expand=True, pady=30)

        def bilgi_satiri(baslik, anahtar, is_bold=False):
            satir = ctk.CTkFrame(bilgi_frame, fg_color="transparent")
            satir.pack(fill="x", pady=6)
            ctk.CTkLabel(satir, text=baslik, width=150, anchor="w", text_color="gray50", font=ctk.CTkFont(size=13)).pack(side="left")
            deger = ogrenci.get(anahtar, "-")
            font_w = "bold" if is_bold else "normal"
            ctk.CTkLabel(satir, text=deger if deger else "-", anchor="w", text_color=self.COLOR_TEXT_DARK, font=ctk.CTkFont(size=14, weight=font_w)).pack(side="left")

        ctk.CTkLabel(bilgi_frame, text=ogrenci.get("Ad Soyad", "İsimsiz"), font=ctk.CTkFont(size=24, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(anchor="w", pady=(0, 15))

        bilgi_satiri("Yaş:", "Yaş")
        bilgi_satiri("Okul:", "Okul")
        bilgi_satiri("Sınıf:", "Sınıf")
        
        ctk.CTkFrame(bilgi_frame, height=1, fg_color="#E0E0E0").pack(fill="x", pady=15)
        
        ctk.CTkLabel(bilgi_frame, text="İletişim Bilgileri", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 10))
        bilgi_satiri("Öğrenci Telefonu:", "Ogrenci Telefonu", is_bold=True)
        bilgi_satiri("Öğrenci E-Posta:", "Ogrenci Mail")
        
        ctk.CTkFrame(bilgi_frame, height=1, fg_color="#E0E0E0").pack(fill="x", pady=15)
        
        ctk.CTkLabel(bilgi_frame, text="Veli Bilgileri", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 10))
        bilgi_satiri("Veli Adı:", "Veli Adı")
        bilgi_satiri("Veli Telefonu:", "Veli Telefonu", is_bold=True)
        bilgi_satiri("Veli E-Posta:", "Veli Mail")

    # ------------------------------------------------------------------
    # FOTOĞRAFLI YENİ ÖĞRENCİ KAYIT POP-UP'I
    # ------------------------------------------------------------------
    def ac_ogrenci_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Yeni Öğrenci Kaydı")
        popup.geometry("600x850")
        popup.configure(fg_color="#F4F1EA")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Kayıt Formu", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(pady=(20, 10))

        form_scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        form_scroll.grid_columnconfigure(1, weight=1)

        girdiler = {}
        secili_foto_yolu = ctk.StringVar(value="")
        satir = 0

        # --- FOTOĞRAF ALANI ---
        foto_container = ctk.CTkFrame(form_scroll, fg_color="transparent")
        foto_container.grid(row=satir, column=0, columnspan=2, pady=(0, 20))
        
        lbl_foto_onizleme = ctk.CTkLabel(foto_container, text="Fotoğraf\nEkleyin", width=100, height=120, fg_color="#E0E0E0", corner_radius=8)
        lbl_foto_onizleme.pack(side="left", padx=15)

        def foto_sec():
            path = filedialog.askopenfilename(filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg")])
            if path:
                secili_foto_yolu.set(path)
                try:
                    img = Image.open(path)
                    ctk_img = ctk.CTkImage(light_image=img, size=(100, 120))
                    lbl_foto_onizleme.configure(image=ctk_img, text="")
                except Exception: pass

        ctk.CTkButton(foto_container, text="Fotoğraf Seç", fg_color="gray50", command=foto_sec).pack(side="left", padx=10)
        satir += 1

        def form_satiri(baslik, anahtar, placeholder=""):
            nonlocal satir
            ctk.CTkLabel(form_scroll, text=baslik, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=satir, column=0, pady=8, sticky="w")
            ent = ctk.CTkEntry(form_scroll, placeholder_text=placeholder, height=35)
            ent.grid(row=satir, column=1, pady=8, padx=(10, 0), sticky="ew")
            girdiler[anahtar] = ent
            satir += 1

        ctk.CTkLabel(form_scroll, text="Öğrenci Bilgileri", font=ctk.CTkFont(size=14, weight="bold", underline=True), text_color=self.COLOR_ACCENT_GOLD).grid(row=satir, column=0, columnspan=2, pady=(10, 5), sticky="w")
        satir += 1
        form_satiri("Ad Soyad:", "Ad Soyad", "Ahmet Yılmaz")
        form_satiri("Yaş", "Yaş", "16 Yaş")
        form_satiri("Öğrenci Telefonu:", "Ogrenci Telefonu", "05xx xxx xx xx")
        form_satiri("Öğrenci E-Posta:", "Ogrenci Mail", "isimsoyisim@email.com")
        form_satiri("Okul:", "Okul", "Atatürk Anadolu Lisesi")
        form_satiri("Sınıf:", "Sınıf", "10. Sınıf")

        ctk.CTkLabel(form_scroll, text="Veli Bilgileri", font=ctk.CTkFont(size=14, weight="bold", underline=True), text_color=self.COLOR_ACCENT_GOLD).grid(row=satir, column=0, columnspan=2, pady=(20, 5), sticky="w")
        satir += 1
        form_satiri("Velisi:", "Veli Adı", "Örn: Ayşe Yılmaz")
        form_satiri("Veli Telefonu:", "Veli Telefonu", "05xx xxx xx xx")
        form_satiri("Veli E-Posta:", "Veli Mail", "ayseveli@email.com")

        ctk.CTkLabel(form_scroll, text="Finansal Bilgiler", font=ctk.CTkFont(size=14, weight="bold", underline=True), text_color=self.COLOR_ACCENT_GOLD).grid(row=satir, column=0, columnspan=2, pady=(20, 5), sticky="w")
        satir += 1
        form_satiri("Ödeme Miktarı:", "Ödeme Miktarı", "Örn: 5000")
        form_satiri("Ödeme Günü:", "Ödeme Günü", "Örn: Her ayın 15'i")

        def kaydet():
            yeni_ogrenci = {k: v.get().strip() for k, v in girdiler.items()}
            ad_soyad = yeni_ogrenci.get("Ad Soyad", "")
            
            if not ad_soyad:
                messagebox.showwarning("Uyarı", "Ad Soyad alanı boş bırakılamaz.")
                return

            kaynak_foto = secili_foto_yolu.get()
            hedef_foto_yolu = ""
            if kaynak_foto and os.path.exists(kaynak_foto):
                try:
                    uzanti = os.path.splitext(kaynak_foto)[1]
                    yeni_isim = f"{ad_soyad.replace(' ', '_')}_{len(self.ogrenci_listesi)}{uzanti}"
                    hedef_foto_yolu = os.path.join(self.PROFIL_FOTO_DIZIN, yeni_isim)
                    shutil.copy2(kaynak_foto, hedef_foto_yolu)
                    yeni_ogrenci["foto_yolu"] = hedef_foto_yolu
                    
                    # --- YENİ: FIREBASE STORAGE YÜKLEMESİ ---
                    bucket = storage.bucket(self.FIREBASE_BUCKET_NAME)
                    blob = bucket.blob(f"ogrenci_profil/{yeni_isim}")
                    blob.upload_from_filename(hedef_foto_yolu)
                    
                    # Web Sitesinin Doğrudan Okuyabileceği URL'yi Oluştur
                    encoded_name = urllib.parse.quote(f"ogrenci_profil/{yeni_isim}", safe='')
                    public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.FIREBASE_BUCKET_NAME}/o/{encoded_name}?alt=media"
                    yeni_ogrenci["fotograf_url"] = public_url
                    
                except Exception as e:
                    print(f"Fotoğraf işleme/yükleme hatası: {e}")
            
            if self.db:
                try:
                    doc_ref = self.db.collection("ogrenciler").document()
                    yeni_ogrenci["id"] = doc_ref.id
                    doc_ref.set(yeni_ogrenci)
                    
                    self.ogrenci_listesi.append(yeni_ogrenci)
                    self.listeyi_yenile()
                    if hasattr(self.master, "guncelle_ana_sayfa"): self.master.guncelle_ana_sayfa()
                    popup.destroy()
                except Exception as e:
                    messagebox.showerror("Kayıt Hatası", f"Veritabanına kaydedilirken hata oluştu:\n{e}")

        ctk.CTkButton(popup, text="ÖĞRENCİ EKLE", font=ctk.CTkFont(size=14, weight="bold"), fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER, height=45, command=kaydet).pack(pady=(10, 20), padx=30, fill="x")

    def ogrenci_kalici_sil(self):
        if not self.secili_ogrenci: return
        
        ogr_adi = self.secili_ogrenci.get("Ad Soyad", "Bu öğrenciyi")
        cevap = messagebox.askyesno("Kalıcı Silme Onayı", f"{ogr_adi} sistemden KALICI OLARAK silinecektir.\nBu işlemin geri dönüşü yoktur. Onaylıyor musunuz?")
        
        if cevap:
            ogr_id = self.secili_ogrenci.get("id")
            
            if self.db and ogr_id:
                try:
                    self.db.collection("ogrenciler").document(ogr_id).delete()
                except Exception as e:
                    messagebox.showerror("Hata", f"Silme işlemi başarısız: {e}")
                    return
            
            foto_yolu = self.secili_ogrenci.get("foto_yolu", "")
            if foto_yolu and os.path.exists(foto_yolu):
                try: os.remove(foto_yolu)
                except: pass

            self.ogrenci_listesi = [o for o in self.ogrenci_listesi if o.get("id") != ogr_id]
            self.secili_ogrenci = None
            
            for widget in self.main_content.winfo_children(): widget.destroy()
            self.lbl_info.place(relx=0.5, rely=0.5, anchor="center")
            
            self.listeyi_yenile()
            if hasattr(self.master, "guncelle_ana_sayfa"): self.master.guncelle_ana_sayfa()

    def ac_duzenleme_popup(self):
        if not self.secili_ogrenci:
            messagebox.showwarning("Uyarı", "Lütfen önce bir öğrenci seçin.")
            return
        
        popup = ctk.CTkToplevel(self)
        popup.title("Öğrenci Bilgilerini Düzenle")
        popup.geometry("600x750")
        popup.attributes("-topmost", True)
        popup.grab_set()

        form_scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        girdiler = {}
        secili_foto_yolu = ctk.StringVar(value="")

        # --- DÜZENLEME EKRANI FOTOĞRAF ALANI ---
        foto_container = ctk.CTkFrame(form_scroll, fg_color="transparent")
        foto_container.pack(fill="x", pady=(0, 20))
        
        lbl_foto_onizleme = ctk.CTkLabel(foto_container, text="Mevcut\nFotoğraf", width=100, height=120, fg_color="#E0E0E0", corner_radius=8)
        lbl_foto_onizleme.pack(side="left", padx=15)
        
        mevcut_foto = self.secili_ogrenci.get("foto_yolu", "")
        if mevcut_foto and os.path.exists(mevcut_foto):
            try:
                img = Image.open(mevcut_foto)
                ctk_img = ctk.CTkImage(light_image=img, size=(100, 120))
                lbl_foto_onizleme.configure(image=ctk_img, text="")
            except: pass

        def foto_sec():
            path = filedialog.askopenfilename(filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg")])
            if path:
                secili_foto_yolu.set(path)
                try:
                    img = Image.open(path)
                    ctk_img = ctk.CTkImage(light_image=img, size=(100, 120))
                    lbl_foto_onizleme.configure(image=ctk_img, text="")
                except Exception: pass

        ctk.CTkButton(foto_container, text="Yeni Fotoğraf Seç", fg_color="gray50", command=foto_sec).pack(side="left", padx=10)

        def form_satiri(baslik, anahtar):
            ctk.CTkLabel(form_scroll, text=baslik, font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 0))
            ent = ctk.CTkEntry(form_scroll, height=35)
            ent.insert(0, self.secili_ogrenci.get(anahtar, ""))
            ent.pack(fill="x", pady=(0, 5))
            girdiler[anahtar] = ent

        ctk.CTkLabel(form_scroll, text="Öğrenci Bilgileri", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_ACCENT_GOLD).pack(anchor="w", pady=10)
        form_satiri("Ad Soyad:", "Ad Soyad")
        form_satiri("Yaş", "Yaş")
        form_satiri("Öğrenci Telefonu:", "Ogrenci Telefonu")
        form_satiri("Öğrenci E-Posta:", "Ogrenci Mail")
        form_satiri("Okul:", "Okul")
        form_satiri("Sınıf:", "Sınıf")
        
        ctk.CTkLabel(form_scroll, text="Veli Bilgileri", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_ACCENT_GOLD).pack(anchor="w", pady=10)
        form_satiri("Velisi:", "Veli Adı")
        form_satiri("Veli Telefonu:", "Veli Telefonu")
        form_satiri("Veli E-Posta:", "Veli Mail")

        def kaydet():
            yeni_veriler = {k: v.get().strip() for k, v in girdiler.items()}
            ad_soyad = yeni_veriler.get("Ad Soyad", "Guncellenen_Ogrenci")
            
            yeni_foto = secili_foto_yolu.get()
            if yeni_foto and os.path.exists(yeni_foto):
                try:
                    uzanti = os.path.splitext(yeni_foto)[1]
                    yeni_isim = f"{ad_soyad.replace(' ', '_')}_guncel_{len(self.ogrenci_listesi)}{uzanti}"
                    hedef_foto_yolu = os.path.join(self.PROFIL_FOTO_DIZIN, yeni_isim)
                    shutil.copy2(yeni_foto, hedef_foto_yolu)
                    yeni_veriler["foto_yolu"] = hedef_foto_yolu
                    
                    # --- YENİ: DÜZENLEMEDE DE BULUTA YÜKLE ---
                    bucket = storage.bucket(self.FIREBASE_BUCKET_NAME)
                    blob = bucket.blob(f"ogrenci_profil/{yeni_isim}")
                    blob.upload_from_filename(hedef_foto_yolu)
                    
                    encoded_name = urllib.parse.quote(f"ogrenci_profil/{yeni_isim}", safe='')
                    public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.FIREBASE_BUCKET_NAME}/o/{encoded_name}?alt=media"
                    yeni_veriler["fotograf_url"] = public_url
                except Exception as e:
                    print(f"Fotoğraf güncelleme hatası: {e}")
            
            self.db.collection("ogrenciler").document(self.secili_ogrenci["id"]).update(yeni_veriler)
            self.secili_ogrenci.update(yeni_veriler)
            
            messagebox.showinfo("Başarılı", "Öğrenci bilgileri güncellendi.")
            popup.destroy()
            
            self.listeyi_yenile()
            self.ogrenci_detay_goster(self.secili_ogrenci)

        ctk.CTkButton(popup, text="KAYDET", font=ctk.CTkFont(weight="bold"), fg_color=self.COLOR_SIDEBAR, height=45, command=kaydet).pack(pady=20, padx=20, fill="x")