import customtkinter as ctk
from database import get_db

class AjandaView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db = get_db()
        self.gorevler = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.arayuz_olustur()
        self.verileri_buluttan_cek()

    def arayuz_olustur(self):
        self.header = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.header.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(self.header, text="📝 Kişisel Ajanda (To-Do List)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#044D29").pack(side="left", padx=20, pady=20)
        
        self.ent_gorev = ctk.CTkEntry(self.header, placeholder_text="Yeni bir görev veya not ekleyin...", width=400)
        self.ent_gorev.pack(side="left", padx=20)
        
        ctk.CTkButton(self.header, text="Görev Ekle", fg_color="#D4AF37", command=self.gorev_ekle).pack(side="left")

        self.liste_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.liste_frame.grid(row=1, column=0, padx=40, pady=(0, 40), sticky="nsew")

    def verileri_buluttan_cek(self):
        if self.db:
            try:
                docs = self.db.collection("ajanda").stream()
                self.gorevler = [doc.to_dict() | {"id": doc.id} for doc in docs]
                self.listeyi_yenile()
            except: pass

    def gorev_ekle(self):
        metin = self.ent_gorev.get()
        if not metin: return
        yeni = {"metin": metin, "durum": 0}
        if self.db:
            ref = self.db.collection("ajanda").document()
            yeni["id"] = ref.id
            ref.set(yeni)
        self.gorevler.append(yeni)
        self.ent_gorev.delete(0, 'end')
        self.listeyi_yenile()

    def listeyi_yenile(self):
        for widget in self.liste_frame.winfo_children(): widget.destroy()
        
        for g in self.gorevler:
            satir = ctk.CTkFrame(self.liste_frame, fg_color="#F9F9F9")
            satir.pack(fill="x", pady=2, padx=10)
            
            var = ctk.IntVar(value=g.get("durum", 0))
            def durum_degis(gid=g["id"], v=var):
                if self.db: self.db.collection("ajanda").document(gid).update({"durum": v.get()})
            
            ctk.CTkCheckBox(satir, text=g["metin"], variable=var, command=durum_degis, font=ctk.CTkFont(size=14)).pack(side="left", padx=15, pady=10)
            
            def sil(gid=g["id"]):
                if self.db: self.db.collection("ajanda").document(gid).delete()
                self.gorevler = [x for x in self.gorevler if x["id"] != gid]
                self.listeyi_yenile()
                
            ctk.CTkButton(satir, text="Sil", width=50, fg_color="transparent", text_color="red", command=sil).pack(side="right", padx=10)