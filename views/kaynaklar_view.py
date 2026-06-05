import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
from database import get_db
import os
import shutil  # Dosyaları yerel diske kopyalamak için
import webbrowser

class KaynaklarView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        
        self.db = get_db()
        self.kaynak_listesi = []
        
        # ------------------------------------------------------------------
        # GOOGLE DRIVE MASAÜSTÜ KAYNAK KÜTÜPHANESİ KALICI YOLU
        # ------------------------------------------------------------------
        self.KAYNAK_ANA_DIZIN = r"G:\Drive'ım\Kaynak Kütüphanesi"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Arama çubuğu eklendiği için liste row 2'ye alındı
        
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        # ROW 0: Üst Başlık ve Yeni Ekle Butonu
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=40, pady=(40, 15), sticky="ew")
        
        self.lbl_baslik = ctk.CTkLabel(self.header_frame, text="Dijital Kaynak Kütüphanesi", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.COLOR_TEXT_DARK)
        self.lbl_baslik.pack(side="left")

        self.btn_yeni = ctk.CTkButton(
            self.header_frame, text="+ Yeni Kaynak Ekle", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER,
            text_color=self.COLOR_TEXT_LIGHT, corner_radius=8, height=40,
            command=self.ac_kaynak_ekle_popup
        )
        self.btn_yeni.pack(side="right")

        # ROW 1: CANLI ARAMA ÇUBUĞU
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.grid(row=1, column=0, padx=40, pady=(0, 15), sticky="ew")
        
        self.ent_arama = ctk.CTkEntry(self.search_frame, placeholder_text="🔍 Kaynak adı veya kategoriye göre canlı ara...", height=38, font=ctk.CTkFont(size=14))
        self.ent_arama.pack(fill="x", expand=True)
        # Klavyeden her el çekildiğinde filtrelemeyi tetikler
        self.ent_arama.bind("<KeyRelease>", self.canli_arama_yap)

        # ROW 2: Kaydırılabilir Kaynak Listesi
        self.liste_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.liste_frame.grid(row=2, column=0, padx=40, pady=(0, 40), sticky="nsew")

    def verileri_buluttan_cek(self):
        if not self.db: return
        try:
            docs = self.db.collection("kaynaklar").stream()
            self.kaynak_listesi = []
            for doc in docs:
                veri = doc.to_dict()
                veri["id"] = doc.id
                self.kaynak_listesi.append(veri)
            self.listeyi_yenile()
        except Exception as e: 
            print(f"Kaynakları çekme hatası: {e}")

    # ------------------------------------------------------------------
    # YEREL DİSKE / BULUT KILASÖRÜNE DIREKT KOPYALAMA MOTORU
    # ------------------------------------------------------------------
    def local_drive_kopyala(self, kaynak_dosya, kategori):
        try:
            # 1. Ana dizin altında kategori adında alt klasör kontrolü / oluşturulması
            kategori_yolu = os.path.join(self.KAYNAK_ANA_DIZIN, kategori.strip())
            os.makedirs(kategori_yolu, exist_ok=True)
            
            # 2. Dosya ismini ayıkla ve hedef tam yolu belirle
            dosya_adi = os.path.basename(kaynak_dosya)
            hedef_tam_yol = os.path.join(kategori_yolu, dosya_adi)
            
            # 3. Dosyayı hızlıca kopyala
            shutil.copy2(kaynak_dosya, hedef_tam_yol)
            return hedef_tam_yol
        except Exception as e:
            print(f"Dosya kopyalama hatası: {e}")
            return None

    def canli_arama_yap(self, event=None):
        aranan_kelime = self.ent_arama.get().strip().lower()
        self.listeyi_yenile(arama_filtresi=aranan_kelime)

    def ac_kaynak_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Sisteme Kaynak Ekle")
        popup.geometry("500x650")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Kaynak Bilgileri", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(pady=20)
        
        ent_baslik = ctk.CTkEntry(popup, placeholder_text="Kaynak Adı (Örn: Polinomlar Deneme)", width=350)
        ent_baslik.pack(pady=10)
        
        ent_kategori = ctk.CTkEntry(popup, placeholder_text="Kategori (Örn: TYT Matematik)", width=350)
        ent_kategori.pack(pady=10)
        
        selected_file_path = tk.StringVar(value="")
        
        def dosya_sec():
            path = filedialog.askopenfilename()
            if path:
                selected_file_path.set(path)
                lbl_dosya.configure(text=f"Seçili: {os.path.basename(path)}", text_color="green")

        btn_dosya = ctk.CTkButton(popup, text="Bilgisayardan Dosya Seç", fg_color="gray30", command=dosya_sec)
        btn_dosya.pack(pady=10)
        
        lbl_dosya = ctk.CTkLabel(popup, text="Henüz dosya seçilmedi", font=ctk.CTkFont(size=11), text_color="gray")
        lbl_dosya.pack()

        ctk.CTkLabel(popup, text="VEYA Manuel İnternet Linki Girin:", font=ctk.CTkFont(size=11)).pack(pady=(15,0))
        ent_link = ctk.CTkEntry(popup, placeholder_text="http://...", width=350)
        ent_link.pack(pady=5)
        
        txt_aciklama = ctk.CTkTextbox(popup, height=80, width=350, border_width=1)
        txt_aciklama.pack(pady=10)
        txt_aciklama.insert("0.0", "Kısa bir açıklama...")

        def kaydet():
            baslik = ent_baslik.get().strip()
            kategori = ent_kategori.get().strip()
            file_path = selected_file_path.get()
            manual_link = ent_link.get().strip()
            
            if not baslik or not kategori:
                messagebox.showwarning("Uyarı", "Başlık ve Kategori alanları zorunludur.")
                return

            final_link = manual_link
            
            # Eğer bilgisayardan dosya seçilmişse lokal Drive klasörüne kopyalama tetiklenir
            if file_path:
                btn_kaydet.configure(state="disabled", text="Drive Klasörüne Atılıyor...")
                popup.update()
                
                # API gerektirmeden kopyalama fonksiyonu çağrılıyor
                final_link = self.local_drive_kopyala(file_path, kategori)
                
                if not final_link:
                    messagebox.showerror("Hata", "Dosya kopyalanamadı! G:\\ sürücüsünü kontrol edin.")
                    btn_kaydet.configure(state="normal", text="Kaydet")
                    return

            if not final_link:
                messagebox.showwarning("Uyarı", "Lütfen bir dosya seçin veya link girin.")
                return

            yeni = {
                "baslik": baslik,
                "kategori": kategori,
                "link": final_link,
                "aciklama": txt_aciklama.get("0.0", "end-1c").strip()
            }
            
            if self.db:
                try:
                    doc_ref = self.db.collection("kaynaklar").document()
                    yeni["id"] = doc_ref.id
                    doc_ref.set(yeni)
                except Exception as db_err:
                    print(f"Firestore kayıt hatası: {db_err}")
            
            self.kaynak_listesi.append(yeni)
            self.listeyi_yenile()
            popup.destroy()

        btn_kaydet = ctk.CTkButton(popup, text="Kaydet", fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER, font=ctk.CTkFont(weight="bold"), command=kaydet, height=40)
        btn_kaydet.pack(pady=20)

    def listeyi_yenile(self, arama_filtresi=""):
        for widget in self.liste_frame.winfo_children(): widget.destroy()
        
        if not self.kaynak_listesi:
            ctk.CTkLabel(self.liste_frame, text="Henüz bir kaynak eklenmedi.", font=ctk.CTkFont(slant="italic")).pack(pady=50)
            return

        # Canlı filtreleme algoritması
        gorunur_liste = self.kaynak_listesi
        if arama_filtresi:
            gorunur_liste = [
                k for k in self.kaynak_listesi 
                if arama_filtresi in k.get("baslik", "").lower() or arama_filtresi in k.get("kategori", "").lower()
            ]

        if not gorunur_liste:
            ctk.CTkLabel(self.liste_frame, text="Aramanızla eşleşen kaynak bulunamadı.", font=ctk.CTkFont(slant="italic"), text_color="gray50").pack(pady=40)
            return

        for k in gorunur_liste:
            card = ctk.CTkFrame(self.liste_frame, fg_color="#F9F9F9", corner_radius=10, border_width=1, border_color="#EEEEEE")
            card.pack(fill="x", pady=5, padx=10)
            
            ctk.CTkLabel(card, text=f"[{k['kategori']}]", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left", padx=(20, 5))
            ctk.CTkLabel(card, text=k["baslik"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5, pady=15)
            
            def sil(kid=k["id"]):
                if messagebox.askyesno("Onay", "Bu kaynağı silmek istiyor musunuz?"):
                    if self.db: self.db.collection("kaynaklar").document(kid).delete()
                    self.kaynak_listesi = [x for x in self.kaynak_listesi if x["id"] != kid]
                    # Güncel arama girdisini koruyarak listeyi tazele
                    self.canli_arama_yap()

            def kopyala(link=k["link"]):
                self.clipboard_clear()
                self.clipboard_append(link)
                messagebox.showinfo("Başarılı", "Kaynak yolu kopyalandı!")

            def ac(link=k["link"]):
                # Eğer link yerel bir dosya yolu ise (G:\...) işletim sisteminin varsayılan uygulamasıyla açar
                if os.path.exists(link) or link.startswith("G:"):
                    os.startfile(link)
                else:
                    webbrowser.open(link)

            ctk.CTkButton(card, text="Sil", width=60, height=28, fg_color="transparent", text_color="#D32F2F", hover_color="#FEEEEE", command=sil).pack(side="right", padx=10)
            ctk.CTkButton(card, text="Yolu Kopyala", width=100, height=28, fg_color="gray60", command=kopyala).pack(side="right", padx=5)
            ctk.CTkButton(card, text="Kaynağı Aç", width=100, height=28, fg_color=self.COLOR_SIDEBAR, hover_color=self.COLOR_SIDEBAR_HOVER, text_color=self.COLOR_TEXT_LIGHT, command=ac).pack(side="right", padx=5)