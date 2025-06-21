import firebase_admin
from firebase_admin import credentials, firestore

def get_firebase_db():
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    return firestore.client()

def obtener_vectores_firebase(db):
    datos = []
    docs = db.collection('Datos_Biometricos').stream()
    for doc in docs:
        data = doc.to_dict()
        vector = data.get('vector')
        if vector:
            datos.append((doc.id, vector))
    return datos
