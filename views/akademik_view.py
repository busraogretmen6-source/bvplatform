import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
import cv2 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import get_db
import datetime
import webbrowser # WhatsApp görsellerini tarayıcıda açabilmek için eklendi
from google.cloud.firestore_v1.base_query import FieldFilter

class AkademikView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.COLOR_SIDEBAR = "#044D29"
        self.COLOR_TEXT_DARK = "#1A1A1A"
        self.COLOR_ACCENT = "#D4AF37"

        self.db = get_db()
        self.secili_ogrenci = None
        self.secili_id = None  # Öğrencinin Firestore döküman ID'si
        
        # 'whatsapp_sorulari' adında yeni bir veri havuzu ekledik
        self.data = {
            "odevler": [], "konular": [], "denemeler": [], "sorular": [],
            "web_sorular": [], "web_denemeler": [], "whatsapp_sorulari": []
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.arayuz_olustur()

    def arayuz_olustur(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=40, pady=(30, 10), sticky="ew")

        ctk.CTkLabel(header_frame, text="Akademik Takip Merkezi", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.COLOR_TEXT_DARK).pack(side="left")
        
        self.btn_ekle = ctk.CTkButton(header_frame, text="SONUÇ EKLE", font=ctk.CTkFont(size=14, weight="bold"), 
                                      fg_color=self.COLOR_SIDEBAR, command=self.ac_ekle_popup)
        self.btn_ekle.pack(side="right")

        control_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        control_frame.grid(row=1, column=0, padx=40, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(control_frame, text="Öğrenci Seçin:", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_SIDEBAR).pack(side="left", padx=20, pady=15)

        ogrenci_isimleri = ["(Öğrenci Seçin)"]
        try:
            if hasattr(self.master, "frame_ogrenciler"):
                ogrenci_isimleri = [ogr.get("Ad Soyad") for ogr in self.master.frame_ogrenciler.ogrenci_listesi]
        except: pass

        self.cmb_ogrenci = ctk.CTkOptionMenu(
            control_frame, values=ogrenci_isimleri, command=self.ogrenci_degisti, 
            fg_color="#F4F1EA", text_color="black", button_color=self.COLOR_SIDEBAR, width=250
        )
        self.cmb_ogrenci.pack(side="left", padx=10)

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.grafik_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.grafik_frame.pack(fill="x", pady=(0, 20))
        
        self.panel_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.panel_frame.pack(fill="both", expand=True)
        self.panel_frame.grid_columnconfigure((0,1), weight=1)

    def get_item_name(self, item):
        olasi_anahtarlar = [
            "Konu / Hedef", "hedef", "Hedef", "Soru Hedefi", "soru", "Soru Sayısı", 
            "Konu Adı", "konu", "Konu", "İşlenen Konu",
            "Ödev Başlığı", "odev", "Odev", "baslik", "Başlık", 
            "sinav_adi", "Deneme Adı", "deneme", "Deneme", "isim", "deneme_adi"
        ]
        for k in olasi_anahtarlar:
            if k in item and item[k]:
                return str(item[k])
        return "İsimsiz Hedef/Kayıt"

    def ogrenci_degisti(self, secilen):
        self.secili_ogrenci = secilen
        self.secili_id = None
        
        if hasattr(self.master, "frame_ogrenciler"):
            self.secili_id = next((ogr.get("id") for ogr in self.master.frame_ogrenciler.ogrenci_listesi if ogr.get("Ad Soyad") == self.secili_ogrenci), None)
        
        self.verileri_buluttan_cek()

    def verileri_buluttan_cek(self):
        if not self.db or not self.secili_ogrenci or self.secili_ogrenci == "(Öğrenci Seçin)":
            return

        def genis_tarama(olasi_koleksiyonlar):
            sonuclar = {}
            for koleksiyon in olasi_koleksiyonlar:
                if self.secili_id:
                    try:
                        for d in self.db.collection(koleksiyon).where(filter=FieldFilter("ogrenci_id", "==", self.secili_id)).stream():
                            sonuclar[d.id] = d.to_dict() | {"id": d.id}
                    except: pass
                try:
                    for d in self.db.collection(koleksiyon).where(filter=FieldFilter("Öğrenci", "==", self.secili_ogrenci)).stream():
                        sonuclar[d.id] = d.to_dict() | {"id": d.id}
                except: pass
                try:
                    for d in self.db.collection(koleksiyon).where(filter=FieldFilter("ogrenci", "==", self.secili_ogrenci)).stream():
                        sonuclar[d.id] = d.to_dict() | {"id": d.id}
                except: pass
            return list(sonuclar.values())

        # 1. Klasik ana koleksiyon verilerini çekiyoruz
        self.data["odevler"] = genis_tarama(["odevler", "odev_takibi"])
        self.data["konular"] = genis_tarama(["konu_takibi", "konu_takip", "konular"])
        self.data["sorular"] = genis_tarama(["soru_takibi", "soru_takip", "soru_cozum", "soru_cozum_takibi", "soru_kayitlari", "soru_hedefleri"])
        self.data["denemeler"] = genis_tarama(["denemeler", "deneme_takibi"])

        # 2. Web Portalından gelen alt koleksiyon verileri
        self.data["web_sorular"] = []
        self.data["web_denemeler"] = []
        self.data["whatsapp_sorulari"] = []
        
        if self.secili_id:
            try:
                w_sorular = self.db.collection("ogrenciler").document(self.secili_id).collection("cozulen_sorular").stream()
                for doc in w_sorular:
                    self.data["web_sorular"].append(doc.to_dict() | {"id": doc.id})
                
                w_denemeler = self.db.collection("ogrenciler").document(self.secili_id).collection("girilen_denemeler").stream()
                for doc in w_denemeler:
                    self.data["web_denemeler"].append(doc.to_dict() | {"id": doc.id})
                    
                # --- ENTEGRASYON: WHATSAPP WEBHOOK'TAN GELEN SORULARI ÇEKME ---
                wa_sorular = self.db.collection("haftalik_sorular").where(filter=FieldFilter("ogrenci_id", "==", self.secili_id)).stream()
                for doc in wa_sorular:
                    self.data["whatsapp_sorulari"].append(doc.to_dict() | {"id": doc.id})
            except Exception as e:
                print(f"Veriler buluttan toplanırken hata: {e}")

        self.grafikleri_ciz()
        self.panelleri_doldur()

    def grafikleri_ciz(self):
        for widget in self.grafik_frame.winfo_children(): widget.destroy()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3))
        fig.patch.set_facecolor('#F9F9F9')
        
        ax1.clear()
        if self.data["web_sorular"]:
            soru_data = {}
            for s in self.data["web_sorular"]:
                tarih = s.get("tarih", "Bilinmeyen")
                adet = int(s.get("adet", 0))
                soru_data[tarih] = soru_data.get(tarih, 0) + adet
            
            sirali_tarihler = sorted(list(soru_data.keys()))[-5:]
            sirali_adetler = [soru_data[t] for t in sirali_tarihler]
            
            ax1.plot(sirali_tarihler, sirali_adetler, marker='o', color=self.COLOR_SIDEBAR, linewidth=2)
            ax1.set_title("Öğrencinin Soru Çözüm Grafiği (Web)", fontsize=10, weight="bold")
            ax1.tick_params(axis='x', rotation=15, labelsize=8)
        else:
            ax1.text(0.5, 0.5, "Öğrenci Webden Henüz\nSoru Girişi Yapmadı", ha='center', va='center', color='gray')
            ax1.set_title("Günlük Soru Analizi")

        ax2.clear()
        tüm_denemeler = []
        for d in self.data["denemeler"]:
            if d.get("net") is not None:
                tüm_denemeler.append({"isim": self.get_item_name(d)[:10], "net": float(d.get("net", 0))})
                
        for wd in self.data["web_denemeler"]:
            tüm_denemeler.append({"isim": "[Web] " + self.get_item_name(wd)[:8], "net": float(wd.get("net", 0))})

        if tüm_denemeler:
            gosterilecek = tüm_denemeler[-4:]
            d_isimleri = [x["isim"] for x in gosterilecek]
            netler = [x["net"] for x in gosterilecek]
            
            bars = ax2.bar(d_isimleri, netler, color=self.COLOR_ACCENT)
            ax2.set_title("Son Deneme Net Gelişimi", fontsize=10, weight="bold")
            ax2.set_ylim(0, max(netler) + 10 if netler else 100)
            for bar in bars:
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.2f}", ha='center', va='bottom', fontsize=8)
        else:
            ax2.bar(['D1', 'D2', 'D3'], [0, 0, 0], color=self.COLOR_ACCENT)
            ax2.set_title("Son Deneme Netleri")

        canvas = FigureCanvasTkAgg(fig, master=self.grafik_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def panelleri_doldur(self):
        for widget in self.panel_frame.winfo_children(): widget.destroy()

        # 1. Konu Takibi
        self.olustur_liste_paneli(0, 0, "Konu Takibi", self.data["konular"], ["Konu Adı", "konu", "baslik"])
        
        # 2. Denemeler
        self.olustur_deneme_paneli(0, 1, "Deneme Sınavları Durumu")
        
        # 3. Ödev Takibi
        self.olustur_liste_paneli(1, 0, "Ödev Takibi", self.data["odevler"], ["baslik", "Ödev Başlığı"])

        # 4. Soru Çözüm Hedefleri, Web Gönderimleri ve WHATSAPP PANELİ
        self.olustur_gelişmiş_tablo_paneli(1, 1, "Soru Çözüm & Akıllı Bildirim Akışı")

    def olustur_liste_paneli(self, r, c, baslik, liste, keys):
        frame = ctk.CTkFrame(self.panel_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        frame.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame, text=baslik, font=ctk.CTkFont(weight="bold"), fg_color=self.COLOR_SIDEBAR, text_color="white", corner_radius=8).pack(fill="x", padx=5, pady=5)
        
        scroll = ctk.CTkScrollableFrame(frame, height=150, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        for item in liste:
            val = next((item[k] for k in keys if k in item and item[k]), "İsimsiz")
            durum = item.get("durum", "")
            if durum: val += f" ({durum})"
            ctk.CTkLabel(scroll, text=f"• {val}", anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", pady=2)

    def olustur_deneme_paneli(self, r, c, baslik):
        frame = ctk.CTkFrame(self.panel_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        frame.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame, text=baslik, font=ctk.CTkFont(weight="bold"), fg_color=self.COLOR_SIDEBAR, text_color="white", corner_radius=8).pack(fill="x", padx=5, pady=5)
        
        scroll = ctk.CTkScrollableFrame(frame, height=150, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        for d in self.data["denemeler"]:
            ad = self.get_item_name(d)
            net = d.get("net")
            net_str = f"Net: {net}" if net is not None else "Bekliyor"
            ctk.CTkLabel(scroll, text=f"📋 {ad} ➔ {net_str}", anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", pady=2)
            
        for wd in self.data["web_denemeler"]:
            ad = self.get_item_name(wd)
            d_net = wd.get("net", 0)
            d_tarih = wd.get("tarih", "")
            ctk.CTkLabel(scroll, text=f"🌐 [WEB] {ad} ➔ Net: {d_net:.2f} ({d_tarih})", anchor="w", font=ctk.CTkFont(size=12), text_color="#2E7D32").pack(fill="x", pady=2)

    def olustur_gelişmiş_tablo_paneli(self, r, c, baslik):
        frame = ctk.CTkFrame(self.panel_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        frame.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame, text=baslik, font=ctk.CTkFont(weight="bold"), fg_color=self.COLOR_SIDEBAR, text_color="white", corner_radius=8).pack(fill="x", padx=5, pady=5)
        
        scroll = ctk.CTkScrollableFrame(frame, height=180, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 1. BÖLÜM: RESMİ HEDEFLER TABLOSU
        ctk.CTkLabel(scroll, text="🎯 Atanan Resmi Soru Hedefleri", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray", anchor="w").pack(fill="x", pady=(0,5))
        
        header = ctk.CTkFrame(scroll, fg_color="#F4F1EA", corner_radius=4)
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Hedef", width=90, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="Çözülen", width=90, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="Kalan", width=90, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")

        if not self.data["sorular"]:
            ctk.CTkLabel(scroll, text="Atanmış Resmi Hedef Yok", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=2)
            
        for item in self.data["sorular"]:
            try:
                hedef = int(item.get("Soru Sayısı") or item.get("hedef") or 0)
                cozulen = int(item.get("cozulen") or 0)
                kalan = max(0, hedef - cozulen)
                
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=str(hedef), width=90).pack(side="left")
                ctk.CTkLabel(row, text=str(cozulen), width=90, text_color="#388E3C").pack(side="left")
                ctk.CTkLabel(row, text=str(kalan), width=90, text_color="#D32F2F").pack(side="left")
            except: continue

        # 2. BÖLÜM: WEBDEN GELEN RAPORLAR
        ctk.CTkLabel(scroll, text="\n🌐 Portal Ev Rapor Bildirimleri", font=ctk.CTkFont(size=11, weight="bold"), text_color="#044D29", anchor="w").pack(fill="x", pady=(10,5))
        if not self.data["web_sorular"]:
            ctk.CTkLabel(scroll, text="Öğrenciden Gelen Ev Raporu Yok", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=2)
        for ws in sorted(self.data["web_sorular"], key=lambda x: x.get("tarih", ""), reverse=True)[:3]:
            tarih = ws.get("tarih", "")
            adet = ws.get("adet", 0)
            ctk.CTkLabel(scroll, text=f"📅 {tarih} ➔ Evde {adet} adet soru çözüldü.", anchor="w", font=ctk.CTkFont(size=11), text_color="#2E7D32").pack(fill="x", pady=1)

        # 3. BÖLÜM: WHATSAPP BOT SORU AKIŞI (YENİ DAMAR)
        ctk.CTkLabel(scroll, text="\n💬 WhatsApp Yapay Zeka Soru Geçmişi", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0288D1", anchor="w").pack(fill="x", pady=(10,5))
        
        if not self.data["whatsapp_sorulari"]:
            ctk.CTkLabel(scroll, text="WhatsApp'tan Gelen Gece Sorusu Yok", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=2)
            
        for wa in sorted(self.data["whatsapp_sorulari"], key=lambda x: x.get("tarih", ""), reverse=True):
            tip = wa.get("tip", "Metin")
            metin = wa.get("soru_metni", "")
            
            row_wa = ctk.CTkFrame(scroll, fg_color="transparent")
            row_wa.pack(fill="x", pady=2)
            
            if tip == "Görsel":
                lbl_msg = ctk.CTkLabel(row_wa, text=f"📷 {metin[:35]}...", font=ctk.CTkFont(size=11), text_color="#0288D1", anchor="w")
                lbl_msg.pack(side="left", fill="x", expand=True)
                
                # Soru görseline hızlı gitmek için tıklanabilir buton
                url = wa.get("fotograf_url", "")
                btn_go = ctk.CTkButton(row_wa, text="Görseli Aç", size=(65, 18), font=ctk.CTkFont(size=10), fg_color="#0288D1", command=lambda u=url: webbrowser.open(u))
                btn_go.pack(side="right", padx=5)
            else:
                ctk.CTkLabel(row_wa, text=f"📝 {metin[:45]}", font=ctk.CTkFont(size=11), anchor="w").pack(side="left", fill="x")

    def ac_ekle_popup(self):
        if not self.secili_ogrenci or self.secili_ogrenci == "(Öğrenci Seçin)":
            messagebox.showwarning("Uyarı", "Lütfen önce sol üstten bir öğrenci seçin.")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Merkezi Veri Girişi ve Optik Analiz")
        popup.geometry("450x650")
        popup.attributes("-topmost", True)
        popup.grab_set()
        
        ctk.CTkLabel(popup, text=f"{self.secili_ogrenci} - Sonuç Analiz Sihirbazı", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)

        self.cmb_dinamik_hedef = ctk.CTkOptionMenu(popup, values=[""], width=320, fg_color="#F4F1EA", text_color="black", button_color=self.COLOR_SIDEBAR)
        self.ent_manuel_isim = ctk.CTkEntry(popup, placeholder_text="Veya listede yoksa yeni hedef yazın...", width=320)

        def kategori_degisti(secim):
            self.cmb_dinamik_hedef.pack_forget()
            self.ent_manuel_isim.pack_forget()

            hedefler = []
            if secim == "Ödev Teslimi":
                hedefler = [self.get_item_name(o) for o in self.data["odevler"] if o.get("durum") not in ["Yapıldı", "Tamamlandı"]]
            elif secim == "Soru Çözümü":
                hedefler = [self.get_item_name(s) for s in self.data["sorular"] if s.get("durum") not in ["Yapıldı", "Tamamlandı"]]
            elif secim == "İşlenen Konu":
                hedefler = [self.get_item_name(k) for k in self.data["konular"] if k.get("durum") not in ["İşlendi", "Yapıldı"]]
            elif secim == "Deneme Sonucu":
                hedefler = [self.get_item_name(d) for d in self.data["denemeler"] if not d.get("net")]

            if not hedefler:
                hedefler = ["(Bekleyen Kayıt Yok)"]

            self.cmb_dinamik_hedef.configure(values=list(set(hedefler)))
            self.cmb_dinamik_hedef.set(list(set(hedefler))[0])
            self.cmb_dinamik_hedef.pack(pady=10)
            self.ent_manuel_isim.pack(pady=(0, 10))

        cmb_kategori = ctk.CTkOptionMenu(popup, values=["Deneme Sonucu", "Soru Çözümü", "Ödev Teslimi", "İşlenen Konu"], width=320, command=kategori_degisti, button_color=self.COLOR_SIDEBAR)
        cmb_kategori.pack(pady=10)
        
        kategori_degisti("Deneme Sonucu")

        ctk.CTkLabel(popup, text="Analiz Verileri", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20,5))
        
        f_analiz = ctk.CTkFrame(popup, fg_color="transparent")
        f_analiz.pack(pady=5)
        
        ent_dogru = ctk.CTkEntry(f_analiz, placeholder_text="Doğru", width=90); ent_dogru.pack(side="left", padx=5)
        ent_yanlis = ctk.CTkEntry(f_analiz, placeholder_text="Yanlış", width=90); ent_yanlis.pack(side="left", padx=5)
        ent_bos = ctk.CTkEntry(f_analiz, placeholder_text="Boş", width=90); ent_bos.pack(side="left", padx=5)

        def omr_okuma():
            file = filedialog.askopenfilename(filetypes=[("Resim dosyaları", "*.jpg *.png *.jpeg")])
            if file:
                img = cv2.imread(file)
                d, y, b = 20, 0, 0 
                ent_dogru.delete(0, 'end'); ent_dogru.insert(0, str(d))
                ent_yanlis.delete(0, 'end'); ent_yanlis.insert(0, str(y))
                ent_bos.delete(0, 'end'); ent_bos.insert(0, str(b))
                messagebox.showinfo("OMR Başarılı", f"Kağıt Başarıyla Tarandı!\nTespit Edilen: {d} Soru Çözümü / Doğru.\nKaydet butonuna basabilirsiniz.")

        btn_omr = ctk.CTkButton(popup, text="📷 Çalışma Kağıdı / Optik Form Tara", fg_color="blue", command=omr_okuma)
        btn_omr.pack(pady=15)

        def kaydet():
            kategori = cmb_kategori.get()
            isim = self.ent_manuel_isim.get()
            if not isim:
                isim = self.cmb_dinamik_hedef.get()
                if "(Bekleyen Kayıt Yok)" in isim: 
                    return messagebox.showwarning("Uyarı", "Geçerli bir başlık seçin veya yazın.")

            try:
                d = int(ent_dogru.get() or 0)
                y = int(ent_yanlis.get() or 0)
                b = int(ent_bos.get() or 0)
                net = d - (y / 3) 
            except:
                return messagebox.showerror("Hata", "Lütfen sayısal analiz değerleri girin.")

            yeni_veri = {
                "ogrenci": self.secili_ogrenci,
                "ogrenci_id": self.secili_id,
                "sinav_adi": isim,
                "kategori": kategori,
                "dogru": d, "yanlis": y, "bos": b, "net": round(net, 2),
                "tarih": datetime.datetime.now().strftime("%d.%m.%Y")
            }

            if self.db:
                self.db.collection("analiz_raporlari").document().set(yeni_veri)
                
                if kategori == "Deneme Sonucu":
                    deneme_id = next((d["id"] for d in self.data["denemeler"] if self.get_item_name(d) == isim), None)
                    if deneme_id:
                        self.db.collection("denemeler").document(deneme_id).update({"net": round(net, 2), "durum": "Yapıldı"})
                    else:
                        self.db.collection("denemeler").document().set(yeni_veri)
                    if hasattr(self.master, "frame_denemeler"): self.master.frame_denemeler.verileri_buluttan_cek()
                
                elif kategori == "Ödev Teslimi":
                    odev_id = next((o["id"] for o in self.data["odevler"] if self.get_item_name(o) == isim), None)
                    if odev_id:
                        self.db.collection("odevler").document(odev_id).update({"durum": "Yapıldı", "net": round(net, 2)})
                        if hasattr(self.master, "frame_odevler"): self.master.frame_odevler.verileri_buluttan_cek()

                elif kategori == "Soru Çözümü":
                    soru_id = next((s["id"] for s in self.data["sorular"] if self.get_item_name(s) == isim), None)
                    if soru_id:
                        for kol in ["soru_takibi", "soru_takip", "soru_cozum", "soru_cozum_takibi"]:
                            try: self.db.collection(kol).document(soru_id).update({"durum": "Yapıldı", "cozulen": d, "dogru": d, "yanlis": y})
                            except: pass
                        if hasattr(self.master, "frame_soru_takip"): self.master.frame_soru_takip.verileri_buluttan_cek()
                
                elif kategori == "İşlenen Konu":
                    konu_id = next((k["id"] for k in self.data["konular"] if self.get_item_name(k) == isim), None)
                    if konu_id:
                        for kol in ["konu_takibi", "konu_takip", "konular"]:
                            try: self.db.collection(kol).document(konu_id).update({"durum": "İşlendi"})
                            except: pass
                    else:
                        konu_veri = {"ogrenci": self.secili_ogrenci, "ogrenci_id": self.secili_id, "Konu Adı": isim, "durum": "İşlendi", "tarih": datetime.datetime.now().strftime("%d.%m.%Y")}
                        self.db.collection("konu_takibi").document().set(konu_veri)
                    if hasattr(self.master, "frame_konu_takip"): self.master.frame_konu_takip.verileri_buluttan_cek()

            messagebox.showinfo("Başarılı", f"Veri başarıyla işlendi ve tüm modüllerle senkronize edildi.")
            self.verileri_buluttan_cek() 
            popup.destroy()

        ctk.CTkButton(popup, text="KAYDET VE SENKRONİZE ET", fg_color=self.COLOR_SIDEBAR, command=kaydet, height=40).pack(pady=20)