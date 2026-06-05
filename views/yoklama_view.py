import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import get_db
from datetime import datetime

class YoklamaView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_SIDEBAR_HOVER = "#066838"
        self.COLOR_ACCENT_GOLD = "#D4AF37"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_TEXT_LIGHT = "#FDFDFB"
        
        self.db = get_db()
        self.yoklama_listesi = []
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
        
        # Sağ Taraf: Yoklama Geçmişi
        self.main_content = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.main_content.grid(row=0, column=1, padx=(10, 40), pady=40, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(self.main_content, text="Katılım durumunu görmek için\nsol taraftan bir öğrenci seçin.", font=ctk.CTkFont(size=16, slant="italic"), text_color="gray50")
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
            docs = self.db.collection("yoklama").stream()
            self.yoklama_listesi = [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e: print(f"Yoklama çekme hatası: {e}")

    def ogrenci_sec(self, ogrenci):
        self.secili_ogrenci = ogrenci
        self.lbl_info.place_forget()
        for widget in self.main_content.winfo_children(): widget.destroy()
        
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text=f"{ogrenci['Ad Soyad']} - Yoklama Takibi", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left")
        ctk.CTkButton(header, text="+ Yeni Kayıt Ekle", fg_color=self.COLOR_SIDEBAR, command=self.ac_yoklama_ekle_popup).pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.yoklamalari_listele()

    def yoklamalari_listele(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        ogr_yoklama = [y for y in self.yoklama_listesi if y.get("ogrenci_id") == self.secili_ogrenci["id"]]
        
        if not ogr_yoklama:
            ctk.CTkLabel(self.list_frame, text="Henüz bir yoklama kaydı bulunmuyor.", font=ctk.CTkFont(slant="italic")).pack(pady=50)
            return

        for y in reversed(ogr_yoklama):
            card = ctk.CTkFrame(self.list_frame, fg_color="#F9F9F9", corner_radius=10, border_width=1, border_color="#EEEEEE")
            card.pack(fill="x", pady=5)
            
            durum = y.get("durum", "Geldi")
            colors = {"Geldi": "#388E3C", "Gelmedi": "#D32F2F", "Geç Geldi": "#FBC02D", "İptal": "gray50"}
            
            ctk.CTkLabel(card, text=y.get("tarih", "-"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(card, text=y.get("ders", "Genel Ders"), font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
            
            lbl_durum = ctk.CTkLabel(card, text=durum, font=ctk.CTkFont(size=12, weight="bold"), text_color="white", fg_color=colors.get(durum, "black"), corner_radius=5, width=80)
            lbl_durum.pack(side="right", padx=20)
            
            def sil(yid=y["id"]):
                if messagebox.askyesno("Onay", "Bu yoklama kaydını silmek istiyor musunuz?"):
                    if self.db: self.db.collection("yoklama").document(yid).delete()
                    self.yoklama_listesi = [x for x in self.yoklama_listesi if x["id"] != yid]
                    self.yoklamalari_listele()
            
            ctk.CTkButton(card, text="Sil", width=50, height=25, fg_color="transparent", text_color="#D32F2F", command=sil).pack(side="right", padx=5)

    def ac_yoklama_ekle_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Yoklama Kaydı")
        popup.geometry("400x400")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Ders Katılım Bilgisi", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        ent_tarih = ctk.CTkEntry(popup, placeholder_text="Tarih (Örn: 15.05.2026)", width=300)
        ent_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        ent_tarih.pack(pady=10)
        
        ent_ders = ctk.CTkEntry(popup, placeholder_text="Ders/Konu Adı", width=300)
        ent_ders.pack(pady=10)
        
        cmb_durum = ctk.CTkOptionMenu(popup, values=["Geldi", "Gelmedi", "Geç Geldi", "İptal"], width=300)
        cmb_durum.pack(pady=10)

        def kaydet():
            yeni = {
                "ogrenci_id": self.secili_ogrenci["id"],
                "tarih": ent_tarih.get(),
                "ders": ent_ders.get() or "Matematik Dersi",
                "durum": cmb_durum.get(),
                "kayit_tarihi": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            if self.db:
                doc_ref = self.db.collection("yoklama").document()
                yeni["id"] = doc_ref.id
                doc_ref.set(yeni)
            self.yoklama_listesi.append(yeni)
            self.yoklamalari_listele()
            popup.destroy()

        ctk.CTkButton(popup, text="Kaydı Tamamla", fg_color=self.COLOR_SIDEBAR, command=kaydet, height=40).pack(pady=20)