import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import get_db
from datetime import datetime

class KonuTakipView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        
        self.db = get_db()
        self.konu_listesi = []
        self.secili_ogrenci = None
        
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
        
        # Sağ Taraf: Müfredat Takibi
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Müfredat ilerlemesini yönetmek için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
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
            docs = self.db.collection("konu_takip").stream()
            self.konu_listesi = [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e: print(f"Konu çekme hatası: {e}")

    def ogrenci_sec(self, ogrenci):
        self.secili_ogrenci = ogrenci
        self.lbl_info.place_forget()
        for widget in self.main_content.winfo_children(): widget.destroy()
        
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text=f"{ogrenci['Ad Soyad']} - Müfredat Durumu", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")
        ctk.CTkButton(header, text="+ Yeni Konu Ekle", fg_color=self.COLOR_SIDEBAR, command=self.ac_konu_ekle_popup).pack(side="right")

        self.stats_frame = ctk.CTkFrame(self.main_content, fg_color="#F9F9F9", corner_radius=10)
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        self.ilerleme_guncelle()

        self.list_frame = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.konulari_listele()

    def ilerleme_guncelle(self):
        for widget in self.stats_frame.winfo_children(): widget.destroy()
        
        ogr_konular = [k for k in self.konu_listesi if k.get("ogrenci_id") == self.secili_ogrenci["id"]]
        toplam = len(ogr_konular)
        biten = len([k for k in ogr_konular if k.get("durum") == "Bitti"])
        yuzde = (biten / toplam * 100) if toplam > 0 else 0

        ctk.CTkLabel(self.stats_frame, text=f"Genel İlerleme: %{int(yuzde)}", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20, pady=10)
        
        p_bar = ctk.CTkProgressBar(self.stats_frame, fg_color="#E0E0E0", progress_color=self.COLOR_SIDEBAR)
        p_bar.pack(side="left", fill="x", expand=True, padx=20)
        p_bar.set(yuzde / 100)
        
        ctk.CTkLabel(self.stats_frame, text=f"{biten}/{toplam} Konu Tamamlandı", font=ctk.CTkFont(size=12)).pack(side="right", padx=20)

    def konulari_listele(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        
        ogr_konular = [k for k in self.konu_listesi if k.get("ogrenci_id") == self.secili_ogrenci["id"]]
        if not ogr_konular:
            ctk.CTkLabel(self.list_frame, text="Henüz müfredat planı oluşturulmadı.", font=ctk.CTkFont(slant="italic")).pack(pady=50)
            return

        kategoriler = sorted(list(set([k.get("kategori", "Genel") for k in ogr_konular])))
        
        for kat in kategoriler:
            kat_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            kat_frame.pack(fill="x", pady=(15, 5))
            ctk.CTkLabel(kat_frame, text=kat, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_ACCENT_GOLD).pack(side="left", padx=5)
            ctk.CTkFrame(kat_frame, height=2, fg_color="#EEEEEE").pack(side="left", fill="x", expand=True, padx=10)

            kat_konulari = [k for k in ogr_konular if k.get("kategori") == kat]
            for k in kat_konulari:
                card = ctk.CTkFrame(self.list_frame, fg_color="#FDFDFB", corner_radius=8, border_width=1, border_color="#EEEEEE")
                card.pack(fill="x", pady=2, padx=10)
                
                ctk.CTkLabel(card, text=k.get("baslik", "-"), font=ctk.CTkFont(size=13)).pack(side="left", padx=15, pady=10)
                
                def durum_degistir(secim, kid=k["id"]):
                    if self.db:
                        self.db.collection("konu_takip").document(kid).update({"durum": secim})
                    for item in self.konu_listesi:
                        if item["id"] == kid: item["durum"] = secim
                    self.ilerleme_guncelle()
                    self.konulari_listele()

                durum = k.get("durum", "Başlanmadı")
                d_color = "gray60"
                if durum == "Devam Ediyor": d_color = self.COLOR_ACCENT_GOLD
                elif durum == "Bitti": d_color = self.COLOR_SIDEBAR
                
                cmb = ctk.CTkOptionMenu(
                    card, values=["Başlanmadı", "Devam Ediyor", "Bitti"], 
                    width=130, height=28, fg_color=d_color, button_color=d_color,
                    command=lambda s, kid=k["id"]: durum_degistir(s, kid)
                )
                cmb.set(durum)
                cmb.pack(side="right", padx=10)

                def sil(kid=k["id"]):
                    if messagebox.askyesno("Onay", "Bu konuyu müfredattan silmek istiyor musunuz?"):
                        if self.db: self.db.collection("konu_takip").document(kid).delete()
                        self.konu_listesi = [x for x in self.konu_listesi if x["id"] != kid]
                        self.ilerleme_guncelle()
                        self.konulari_listele()

                ctk.CTkButton(card, text="Sil", width=40, height=25, fg_color="transparent", text_color="#D32F2F", command=sil).pack(side="right", padx=5)

    def ac_konu_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Müfredata Konu Ekle")
        popup.geometry("400x400")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Konu Bilgileri", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        ent_kat = ctk.CTkEntry(popup, placeholder_text="Kategori (Örn: TYT Matematik)", width=300)
        ent_kat.pack(pady=10)
        ent_baslik = ctk.CTkEntry(popup, placeholder_text="Konu Adı (Örn: Üslü Sayılar)", width=300)
        ent_baslik.pack(pady=10)

        def kaydet():
            if not ent_baslik.get(): return
            yeni = {"ogrenci_id": self.secili_ogrenci["id"], "kategori": ent_kat.get() or "Genel", "baslik": ent_baslik.get(), "durum": "Başlanmadı"}
            if self.db:
                doc_ref = self.db.collection("konu_takip").document()
                yeni["id"] = doc_ref.id
                doc_ref.set(yeni)
            self.konu_listesi.append(yeni)
            self.ilerleme_guncelle()
            self.konulari_listele()
            popup.destroy()

        ctk.CTkButton(popup, text="Müfredata Ekle", fg_color=self.COLOR_SIDEBAR, command=kaydet, height=40).pack(pady=30)