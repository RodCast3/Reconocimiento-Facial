from flask import Flask, request, jsonify
import numpy as np
import cv2
from keras_facenet import FaceNet

app = Flask(__name__)

# Cargar modelo FaceNet
model = FaceNet().model
model.load_weights('facenet.weights.h5')

@app.route('/extraer_embedding', methods=['POST'])
def extraer_embedding():
    if 'imagen' not in request.files:
        return jsonify({'error': 'No se proporcionó imagen'}), 400

    try:
        # Leer la imagen (esperamos .jpg ya en RGB, 160x160, normalizada)
        file = request.files['imagen'].read()
        np_arr = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Formato de imagen no válido'}), 400

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255
        # Agregar dimensión batch
        img = np.expand_dims(img, axis=0)  # (1, 160, 160, 3)
        embedding = model.predict(img)[0]
        embedding = embedding / np.linalg.norm(embedding)

        return jsonify({'embedding': embedding.tolist()}), 200

    except Exception as e:
        return jsonify({'error': 'Error al procesar la imagen', 'detalle': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
