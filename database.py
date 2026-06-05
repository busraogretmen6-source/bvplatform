import firebase_admin
from firebase_admin import credentials, firestore
import os

def get_db():
    # Firebase'in birden fazla kez başlatılmasını (hata vermesini) engelliyoruz
    if not firebase_admin._apps:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(current_dir, "firebase_key.json")
        
        try:
            cred = credentials.Certificate(cred_path)
            
            # YENİ: Fotoğraf yüklemeleri için Storage Bucket eklendi
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'busra-hoca-platform.firebasestorage.app'
            })
            
            print("Bulut Veritabanı ve Depolama (Firebase) Bağlantısı Başarılı!")
        except Exception as e:
            print(f"Firebase bağlantı hatası: {e}")
            print("Lütfen firebase_key.json dosyasının doğru yerde olduğundan emin olun.")
            return None
            
    return firestore.client()