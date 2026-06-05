import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import get_db
from datetime import datetime

class OdevlerView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        
        self.db = get_db()
        self.odev_listesi = []
        self.secili_ogrenci = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        # Sol Taraf: Öğrenci Listesi
        self.sidebar_liste = ctk.CTkFrame(self, width=200, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.sidebar_liste.grid(row=0, column=0, padx=(40, 10), pady=40, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_liste, text="Öğrenci Seçin", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        self.scroll_liste = ctk.CTkScrollableFrame(self.sidebar_liste, fg_color="transparent")
        self.scroll_liste.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sağ Taraf: Ödev Yönetimi
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Ödevleri yönetmek için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
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
            docs = self.db.collection("odevler").stream()
            self.odev_listesi = [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e: print(f"Ödev çekme hatası: {e}")

    def ogrenci_sec(self, ogrenci):
        self.secili_ogrenci = ogrenci
        self.lbl_info.place_forget()
        for widget in self.main_content.winfo_children(): widget.destroy()
        
        # Üst Başlık
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text=f"{ogrenci['Ad Soyad']} - Ödev Takibi", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")
        ctk.CTkButton(header, text="+ Yeni Ödev Ver", fg_color=self.COLOR_SIDEBAR, command=self.ac_odev_ekle_popup).pack(side="right")

        # Ödev Listesi
        self.list_frame = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.odevleri_listele()

    def odevleri_listele(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        
        ogr_odevler = [o for o in self.odev_listesi if o.get("ogrenci_id") == self.secili_ogrenci["id"]]
        if not ogr_odevler:
            ctk.CTkLabel(self.list_frame, text="Henüz verilmiş bir ödev yok.", font=ctk.CTkFont(slant="italic")).pack(pady=50)
            return

        for o in reversed(ogr_odevler):
            # Tıklanabilir Kart
            card = ctk.CTkFrame(self.list_frame, fg_color="#F9F9F9", corner_radius=10, border_width=1, border_color="#EEEEEE", cursor="hand2")
            card.pack(fill="x", pady=5)
            
            durum = o.get("durum", "Bekliyor")
            durum_color = "#D32F2F" if durum == "Bekliyor" else "#388E3C"
            
            # Kart içindeki metinler de tıklanabilir olmalı
            lbl_baslik = ctk.CTkLabel(card, text=o.get("baslik", "Ödev"), font=ctk.CTkFont(size=14, weight="bold"), cursor="hand2")
            lbl_baslik.pack(side="left", padx=20, pady=15)
            
            lbl_tarih = ctk.CTkLabel(card, text=f"Teslim: {o.get('teslim_tarihi', '-')}", font=ctk.CTkFont(size=12), text_color="gray", cursor="hand2")
            lbl_tarih.pack(side="left", padx=10)
            
            # Tıklama olaylarını bağla (Detay popup'ını açar)
            def detay_goster(event, odev_data=o):
                self.ac_odev_detay_popup(odev_data)

            card.bind("<Button-1>", detay_goster)
            lbl_baslik.bind("<Button-1>", detay_goster)
            lbl_tarih.bind("<Button-1>", detay_goster)
            
            def durum_degistir(oid=o["id"], mevcut=durum):
                yeni = "Yapıldı" if mevcut == "Bekliyor" else "Bekliyor"
                if self.db:
                    self.db.collection("odevler").document(oid).update({"durum": yeni})
                for od in self.odev_listesi:
                    if od["id"] == oid: od["durum"] = yeni
                self.odevleri_listele()

            btn_durum = ctk.CTkButton(card, text=durum, width=100, height=30, fg_color=durum_color, command=lambda oid=o["id"], m=durum: durum_degistir(oid, m))
            btn_durum.pack(side="right", padx=10)
            
            def sil(oid=o["id"]):
                if messagebox.askyesno("Onay", "Bu ödevi silmek istiyor musunuz?"):
                    if self.db: self.db.collection("odevler").document(oid).delete()
                    self.odev_listesi = [x for x in self.odev_listesi if x["id"] != oid]
                    self.odevleri_listele()
            
            ctk.CTkButton(card, text="Sil", width=50, height=25, fg_color="transparent", text_color="#D32F2F", command=sil).pack(side="right", padx=10)

    # YENİ EKLENEN: Ödev Detaylarını Gösteren Pop-up
    def ac_odev_detay_popup(self, odev):
        popup = ctk.CTkToplevel(self)
        popup.title("Ödev Detayı")
        popup.geometry("450x400")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text=odev.get("baslik", "Ödev Başlığı"), font=ctk.CTkFont(size=20, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(pady=(20, 5), padx=20)
        ctk.CTkLabel(popup, text=f"Teslim Tarihi: {odev.get('teslim_tarihi', '-')}", font=ctk.CTkFont(size=13, slant="italic"), text_color="gray").pack(pady=(0, 20))

        # Detay Metni Alanı (Sadece Okunabilir)
        txt_detay = ctk.CTkTextbox(popup, width=400, height=220, border_width=1, fg_color="#F9F9F9", border_color="#E0E0E0")
        txt_detay.pack(padx=20, pady=5)
        txt_detay.insert("0.0", odev.get("detay", "Ödev detayı girilmemiş."))
        txt_detay.configure(state="disabled") # Yazı değiştirilmesini engelle

        ctk.CTkButton(popup, text="Kapat", fg_color=self.COLOR_SIDEBAR, command=popup.destroy).pack(pady=15)

    def ac_odev_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Yeni Ödev Ver")
        popup.geometry("400x450")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Ödev Bilgileri", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        ent_baslik = ctk.CTkEntry(popup, placeholder_text="Ödev Başlığı (Örn: Polinomlar Test 1-2)", width=300)
        ent_baslik.pack(pady=10)
        
        ent_tarih = ctk.CTkEntry(popup, placeholder_text="Teslim Tarihi (Örn: 25.05.2026)", width=300)
        ent_tarih.pack(pady=10)
        
        txt_detay = ctk.CTkTextbox(popup, height=100, width=300, border_width=1)
        txt_detay.pack(pady=10)
        txt_detay.insert("0.0", "Ödev detaylarını buraya yazın...")

        def kaydet():
            if not ent_baslik.get():
                messagebox.showwarning("Uyarı", "Ödev başlığı zorunludur.")
                return

            yeni = {
                "ogrenci_id": self.secili_ogrenci["id"],
                "baslik": ent_baslik.get(),
                "teslim_tarihi": ent_tarih.get(),
                "detay": txt_detay.get("0.0", "end-1c"),
                "durum": "Bekliyor",
                "kayit_tarihi": datetime.now().strftime("%d.%m.%Y")
            }
            
            if self.db:
                doc_ref = self.db.collection("odevler").document()
                yeni["id"] = doc_ref.id
                doc_ref.set(yeni)
            
            self.odev_listesi.append(yeni)
            self.odevleri_listele()
            popup.destroy()

        ctk.CTkButton(popup, text="Ödevi Kaydet", fg_color=self.COLOR_SIDEBAR, command=kaydet, height=40).pack(pady=20)