from flask import Flask, request, jsonify, send_file
import cv2
from mtcnn import MTCNN
import numpy as np
import io

app = Flask(__name__)

detector = MTCNN()

def normalizar(imagen):
    """Normaliza la imagen al rango [0, 1]"""
    return imagen.astype(np.float32) / 255.0

def ajustarImg(imagen, x, y):
    """Redimensiona la imagen a (x, y)"""
    return cv2.resize(imagen, (x, y), interpolation=cv2.INTER_AREA)

def filtro_sobel(imagen):
    """Aplica el filtro Sobel sobre una imagen RGB normalizada"""
    # Convertir a escala de grises
    imagen_gray = cv2.cvtColor((imagen * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    imagen_gray = imagen_gray.astype(np.float32) / 255.0

    # Detectar bordes
    sobelx = cv2.Sobel(imagen_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(imagen_gray, cv2.CV_64F, 0, 1, ksize=3)
    bordes = cv2.magnitude(sobelx, sobely)
    bordes = cv2.normalize(bordes, None, 0, 1, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    bordes = np.clip(bordes * 1.5, 0, 1)

    # Convertir bordes a 3 canales
    bordes_3c = np.repeat(bordes[:, :, np.newaxis], 3, axis=2)

    # Mezclar con la imagen original
    mezcla = cv2.addWeighted(imagen, 0.75, bordes_3c, 0.25, 0)

    return mezcla.astype(np.float32)

def detectar_y_recortar_rostro(imagen):
    """Detecta y recorta el primer rostro usando MTCNN"""
    imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
    resultados = detector.detect_faces(imagen_rgb)

    if not resultados:
        raise ValueError("No se detectó ningún rostro.")

    x, y, w, h = resultados[0]['box']
    x, y = max(x, 0), max(y, 0)
    x2, y2 = min(x + w, imagen.shape[1]), min(y + h, imagen.shape[0])
    return imagen_rgb[y:y2, x:x2]

@app.route('/detectar', methods=['POST'])
def detectar():
    if 'imagen' not in request.files:
        return jsonify({'error': 'No se proporcionó una imagen.'}), 400

    try:
        # Leer imagen del request
        archivo = request.files['imagen']
        imagen = cv2.imdecode(np.frombuffer(archivo.read(), np.uint8), cv2.IMREAD_COLOR)

        # Procesamiento
        rostro = detectar_y_recortar_rostro(imagen)
        rostro = ajustarImg(rostro, 160, 160)
        rostro = normalizar(rostro)
        rostro = filtro_sobel(rostro)

        # Convertir a formato compatible con JPG
        rostro = (rostro * 255).astype(np.uint8)
        rostro = cv2.cvtColor(rostro, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', rostro)

        return send_file(
            io.BytesIO(buffer.tobytes()),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='rostro_recortado.jpg'
        ), 200

    except Exception as e:
        return jsonify({'error': 'Error al procesar la imagen', 'detalle': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
