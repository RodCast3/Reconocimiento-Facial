from io import BytesIO
from flask import request, jsonify
import requests
import numpy as np
import functions_framework
from google.auth.transport.requests import Request
from google.oauth2 import id_token

# Si usas Firebase
from google.cloud import firestore
db = firestore.Client()

URL_DETECCION = 'https://deteccionrostros-668387496305.us-central1.run.app/detectar'
URL_EMBEDDING = 'https://extraccionembbeding-668387496305.us-central1.run.app/extraer_embedding'



def obtener_token(url):
    auth_req = Request()
    return id_token.fetch_id_token(auth_req, url)


def insertarVector(id_usuario: str, vector_facial: list):
    if not isinstance(vector_facial, list) or len(vector_facial) != 512:
        raise ValueError("El vector facial debe ser una lista de 512 dimensiones.")

    datos_faciales_ref = db.collection('Datos_Biometricos').document()
    id_datos_faciales = datos_faciales_ref.id

    datos_faciales_ref.set({
        'fecha_creacion': firestore.SERVER_TIMESTAMP, 
        'id_usuario': id_usuario,
        'vector': vector_facial
    })

    usuarios_ref = db.collection('usuarios').document(id_usuario)
    usuario_doc = usuarios_ref.get()

    if usuario_doc.exists:
        usuarios_ref.update({'id_datos_biometricos': id_datos_faciales})
        print(f"Vector facial insertado y usuario {id_usuario} actualizado.")
    else:
        print(f"El usuario {id_usuario} no existe.")

@functions_framework.http
def procesar_foto(request):
    if request.method != 'POST':
        return jsonify({'error': 'Método no permitido'}), 405

    if not request.files:
        return jsonify({'error': 'No se recibieron archivos'}), 400

    id_usuario = request.form.get('id_usuario')
    if not id_usuario:
        return jsonify({'error': 'No se proporcionó id_usuario'}), 400
    
    fotos = request.files.getlist('fotos')
    if len(fotos) != 9:
        return jsonify({'error': 'Se requieren exactamente 9 fotos'}), 400

    embeddings = []

    for i, foto in enumerate(fotos):
        token_deteccion = obtener_token(URL_DETECCION)
        headers_deteccion = {"Authorization": f"Bearer {token_deteccion}"}
        
        token_embedding = obtener_token(URL_EMBEDDING)
        headers_embedding = {"Authorization": f"Bearer {token_embedding}"}



        try:
            # Paso 1: Detección de rostro
            respuesta_rostro = requests.post(
                URL_DETECCION,
                files={'imagen': (foto.filename, foto.stream, foto.mimetype)},
                headers=headers_deteccion
            )
            if respuesta_rostro.status_code != 200:
                return jsonify({'error': f'Fallo al detectar rostro en foto {i+1}', 'detalle': respuesta_rostro.text}), 500

            # Paso 2: Obtener embedding
            rostro_bytes = BytesIO(respuesta_rostro.content)
            respuesta_vector = requests.post(
                URL_EMBEDDING,
                files={'imagen': ('rostro.jpg', rostro_bytes, 'image/jpeg')},
                headers=headers_embedding
            )
            if respuesta_vector.status_code != 200:
                return jsonify({'error': f'Fallo al obtener embedding de foto {i+1}', 'detalle': respuesta_vector.text}), 500

            embedding = respuesta_vector.json().get('embedding')
            if not embedding:
                return jsonify({'error': f'Embedding inválido en foto {i+1}'}), 500

            embeddings.append(embedding)

        except Exception as e:
            return jsonify({'error': f'Error procesando foto {i+1}', 'detalle': str(e)}), 500

    avg_vector = np.mean(np.array(embeddings), axis=0).tolist()
    
    try:
        insertarVector(id_usuario, avg_vector)
    except Exception as e:
        return jsonify({'error': 'Error al guardar vector en Firebase', 'detalle': str(e)}), 500

    return jsonify({'message': 'Vector promedio calculado y guardado correctamente'}), 200
