import customtkinter as ctk
import tkinter.messagebox as messagebox
import os
from datetime import datetime  # Yerel tarih formatı için eklendi
try:
    from firebase_admin import firestore, storage
except ImportError:
    firestore = None
    storage = None

class RozetlerView(ctk.CTkFrame):
    def __init__(self, master, db=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.COLOR_SIDEBAR = "#044D29"
        self.grid_columnconfigure(0, weight=1)
        
        # --- VERİTABANI BAĞLANTISI ---
        if db:
            self.db = db
        else:
            try:
                self.db = firestore.client() if firestore else None
            except Exception:
                self.db = self._ust_katmandan_bul("db")
        
        # --- BULUT DEPOSU BAĞLANTISI ---
        self.bucket = self._ust_katmandan_bul("bucket")
        if not self.bucket and storage:
            try:
                self.bucket = storage.bucket()
            except Exception: pass
            
        # --- ROZET GÖRSELLERİNİN YEREL YOLLARI ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.badges_dir = os.path.join(current_dir, "rozetler")
        
        self.ogrenci_dokumanlari = {} 
        
        self.arayuz_olustur()
        self.ogrencileri_yukle()

    def _ust_katmandan_bul(self, nitelik_adi):
        mevcut = self.master
        while mevcut:
            if hasattr(mevcut, nitelik_adi):
                return getattr(mevcut, nitelik_adi)
            if hasattr(mevcut, "master"):
                mevcut = mevcut.master
            else:
                break
        return None

    def arayuz_olustur(self):
        ctk.CTkLabel(self, text="Haftanın Şampiyonları Merkezi", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 5))
        ctk.CTkLabel(self, text="Bu hafta dereceye giren öğrencileri seçin ve portallarına rozetlerini ekleyin.", text_color="gray").pack(pady=(0, 30))
        
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(pady=10)
        
        ctk.CTkLabel(control_frame, text="Öğrenci Seçin:", font=ctk.CTkFont(weight="bold")).pack(pady=(0,5))
        self.cmb_ogrenci = ctk.CTkOptionMenu(
            control_frame, 
            values=["(Öğrenciler Yükleniyor...)"], 
            width=350,
            fg_color="#F4F1EA",
            text_color="black",
            button_color=self.COLOR_SIDEBAR
        )
        self.cmb_ogrenci.pack(pady=(0,20))
        
        badged_frame = ctk.CTkFrame(control_frame, fg_color="#F9F9F9", corner_radius=10, border_width=1, border_color="#E0E0E0")
        badged_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(badged_frame, text="Öğrencinin Derecesini ve Rozetini Seçin", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 10))
        
        # --- KRİTİK DÜZELTME: Değişkeni kesin olarak sınıfa bağlıyoruz ---
        self.rozet_var = ctk.StringVar(value="sampiyon")
        
        # Butonları doğrudan self.rozet_var değişkenine açıkça bağlıyoruz
        self.rb_1 = ctk.CTkRadioButton(
            badged_frame, text="🏆 HAFTANIN ŞAMPİYONU (Altın Rozet)", 
            value="sampiyon", variable=self.rozet_var,
            fg_color="#D4AF37", border_color="#D4AF37", text_color="black", font=ctk.CTkFont(size=13)
        )
        self.rb_1.pack(pady=8, anchor="w", padx=30)
        
        self.rb_2 = ctk.CTkRadioButton(
            badged_frame, text="🥈 HAFTANIN İKİNCİSİ (Gümüş Rozet)", 
            value="ikinci", variable=self.rozet_var,
            fg_color="#C0C0C0", border_color="#C0C0C0", text_color="black", font=ctk.CTkFont(size=13)
        )
        self.rb_2.pack(pady=8, anchor="w", padx=30)
        
        self.rb_3 = ctk.CTkRadioButton(
            badged_frame, text="🥉 HAFTANIN ÜÇÜNCÜSÜ (Bronz Rozet)", 
            value="ucuncu", variable=self.rozet_var,
            fg_color="#CD7F32", border_color="#CD7F32", text_color="black", font=ctk.CTkFont(size=13)
        )
        self.rb_3.pack(pady=8, anchor="w", padx=30)

        self.btn_gonder = ctk.CTkButton(
            control_frame, 
            text="Seçili Rozeti Öğrenci Portalına Yükle", 
            fg_color=self.COLOR_SIDEBAR, 
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            command=self.rozet_isle
        )
        self.btn_gonder.pack(pady=40, fill="x", padx=10)

    def ogrencileri_yukle(self):
        if not self.db:
            self.db = self._ust_katmandan_bul("db")
            
        if not self.db:
            self.cmb_ogrenci.configure(values=["(Veritabanı Bağlantısı Yok)"])
            return
            
        try:
            docs = self.db.collection("ogrenciler").stream()
            isimler = ["(Öğrenci Seçin)"]
            self.ogrenci_dokumanlari = {} 
            
            for doc in docs:
                data = doc.to_dict()
                isim = data.get("Ad Soyad")
                if isim:
                    isimler.append(isim)
                    self.ogrenci_dokumanlari[isim] = doc.id 
            
            if len(isimler) > 1:
                self.cmb_ogrenci.configure(values=isimler)
                self.cmb_ogrenci.set("(Öğrenci Seçin)")
            else:
                self.cmb_ogrenci.configure(values=["(Kayıtlı Öğrenci Bulunamadı)"])
                self.cmb_ogrenci.set("(Kayıtlı Öğrenci Bulunamadı)")
            
        except Exception as e:
            self.cmb_ogrenci.configure(values=["(Hata Oluştu)"])

    def rozet_isle(self):
        secilen_isim = self.cmb_ogrenci.get()
        if secilen_isim == "(Öğrenci Seçin)" or secilen_isim not in self.ogrenci_dokumanlari:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir öğrenci seçin.")
            return

        selected_badge_type = self.rozet_var.get()
        
        if not self.bucket:
            self.bucket = self._ust_katmandan_bul("bucket")
            
        if not self.bucket:
            messagebox.showerror("Hata", "Firebase Storage (Depolama) bağlantısı kurulamadı!")
            return
            
        filename = f"rozet_{selected_badge_type}.png"
        
        # --- DÜZELTME: TÜM YOLLAR ARTIK EL YAZISI SABİT DEĞİL, DİNAMİK f"{filename}" KULLANIYOR ---
        path_option1 = os.path.join(self.badges_dir, filename)
        path_option2 = os.path.join(os.getcwd(), "rozetler", filename)
        path_option3 = os.path.join(os.path.dirname(self.badges_dir), "rozetler", filename)
        
        if os.path.exists(path_option1):
            local_badge_path = path_option1
        elif os.path.exists(path_option2):
            local_badge_path = path_option2
        elif os.path.exists(path_option3):
            local_badge_path = path_option3
        else:
            messagebox.showerror("Hata", f"'{filename}' dosyası 'rozetler' klasöründe bulunamadı!")
            return

        doc_id = self.ogrenci_dokumanlari[secilen_isim]
        
        self.btn_gonder.configure(text="Yükleniyor, Lütfen Bekleyin...", state="disabled")
        self.update_idletasks()

        try:
            # --- A. GÖRSELİ BULUTA YÜKLEME ---
            blob_path = f"ogrenciler/{doc_id}/rozetler/{filename}"
            blob = self.bucket.blob(blob_path)
            blob.upload_from_filename(local_badge_path, content_type="image/png")
            blob.make_public()
            rozet_url = blob.public_url
            
            # --- B. VERİTABANI GÜNCELLEME ---
            doc_ref = self.db.collection("ogrenciler").document(doc_id)
            doc_data = doc_ref.get().to_dict()
            
            badge_list = doc_data.get("kazanilan_rozetler_listesi", [])
            
            badge_title_map = {
                "sampiyon": "Haftanın Şampiyonu",
                "ikinci": "Haftanın İkincisi",
                "ucuncu": "Haftanın Üçüncüsü"
            }
            
            new_badge_entry = {
                "type": selected_badge_type,
                "title": badge_title_map.get(selected_badge_type, "Başarı Rozeti"),
                "url": rozet_url,
                "tarih_str": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            
            badge_list.append(new_badge_entry)
            mevcut_rozet_sayisi = doc_data.get("basari_rozetleri", 0)
            
            doc_ref.update({
                "kazanilan_rozetler_listesi": badge_list,
                "basari_rozetleri": mevcut_rozet_sayisi + 1,
                "son_rozet_tarihi": firestore.SERVER_TIMESTAMP
            })
            
            derece_text = badge_title_map.get(selected_badge_type).split("Haftanın ")[1]
            messagebox.showinfo("Başarılı", f"Muazzam! {secilen_isim} bu haftanın {derece_text} rozetini kazandı!\nGörsel veli portalına anında yüklendi.")
            
        except Exception as e:
            messagebox.showerror("Hata Oluştu", f"Rozet kaydedilirken hata oluştu:\n{e}")
            
        finally:
            self.btn_gonder.configure(text="Seçili Rozeti Öğrenci Portalına Yükle", state="normal")