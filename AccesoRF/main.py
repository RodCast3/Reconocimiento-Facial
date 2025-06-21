import functions_framework
import requests
from flask import jsonify
from io import BytesIO
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from firebase import get_firebase_db, obtener_vectores_firebase
from distancia import calcularDistancia
from guardaracceso import guardarAcceso
from permisos import verificar_permiso

URL_DETECCION = 'https://deteccionrostros-668387496305.us-central1.run.app/detectar'
URL_EMBEDDING = 'https://extraccionembbeding-668387496305.us-central1.run.app/extraer_embedding'

@functions_framework.http
def procesar_foto(request):
    if request.method != 'POST':
        return 405

    if not request.files or 'foto' not in request.files:
        return jsonify({'error': 'No se recibió ninguna foto'}), 400

    foto = request.files['foto']
    tipo_registro = request.form.get('tipo_registro')

    if not tipo_registro or tipo_registro not in ['entrada', 'salida']:
        return jsonify({'error': 'Debe indicar tipo_registro (entrada o salida)'}), 400

    try:
        # 1: Detección de rostro
        auth_req = Request()

        tokenDeteccion = id_token.fetch_id_token(auth_req, URL_DETECCION)
        headersDeteccion = {
            "Authorization": f"Bearer {tokenDeteccion}"
        }
        
        respuesta_rostro = requests.post(
            URL_DETECCION,
            files={'imagen': (foto.filename, foto.stream, foto.mimetype)},
            headers=headersDeteccion
        )

        if respuesta_rostro.status_code != 200:
            return jsonify({'error': 'Fallo al detectar rostro', 'detalle': respuesta_rostro.text}), 500

        # 2: Obtener embedding
        rostro_bytes = BytesIO(respuesta_rostro.content)
        tokenEmbedding = id_token.fetch_id_token(auth_req, URL_EMBEDDING)
        headersEmbedding = {
            "Authorization": f"Bearer {tokenEmbedding}"
        }

        respuesta_vector = requests.post(
            URL_EMBEDDING,
            files={'imagen': ('rostro.jpg', rostro_bytes, 'image/jpeg')},
            headers=headersEmbedding
        )

        if respuesta_vector.status_code != 200:
            return jsonify({'error': 'Fallo al obtener embedding', 'detalle': respuesta_vector.text}), 500

        embedding = respuesta_vector.json().get('embedding')

        db = get_firebase_db()
        vectores = obtener_vectores_firebase(db)

        menor_distancia = float('inf')
        id_vector_mas_cercano = None

        for doc_id, vector_guardado in vectores:
            if len(vector_guardado) == 512:
                distancia = calcularDistancia(embedding, vector_guardado)
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    id_vector_mas_cercano = doc_id

        if menor_distancia > 0.6 or not id_vector_mas_cercano:
            return jsonify({'distancia': menor_distancia, 'acceso': 'Denegado', 'razon': 'Rostro no encontrado'}), 403

        doc_vector = db.collection("Datos_Biometricos").document(id_vector_mas_cercano).get()
        id_usuario = doc_vector.to_dict().get("id_usuario")

        acceso_valido, razon, nombre_usuario = verificar_permiso(db, id_usuario)
        if not acceso_valido:
            return jsonify({'usuario': nombre_usuario, 'distancia': menor_distancia, 'acceso': 'denegado', 'razon': razon}), 403

        resultado = guardarAcceso(db, id_usuario, tipo_registro)

        if resultado != True:
            return jsonify({'usuario': nombre_usuario, 'acceso': 'denegado', 'razon': resultado}), 403

        return jsonify({
            'acceso': 'concedido',
            'usuario': nombre_usuario,
            'distancia': menor_distancia
        }), 200

    except Exception as e:
        return jsonify({'error': 'Error inesperado', 'detalle': str(e)}), 500
