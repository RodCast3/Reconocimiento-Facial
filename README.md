# Microservicios – Reconocimiento facial con embeddings en la nube

Repositorio que contiene los microservicios responsables del procesamiento facial biométrico mediante embeddings faciales, desarrollados como parte del "sistema de control de acceso a áreas restringidas mediante reconocimiento facial y generación de códigos OTP".

---

## 📄 Descripción general

Los servicios están organizados de acuerdo con su propósito y nivel de acceso, y se comunican entre sí mediante el protocolo HTTPS.
Todos están desplegados en **Google Cloud Platform**, usando contenedores en **Cloud Run** o funciones en **Cloud Functions**, según su naturaleza.

---

## 🔧 Microservicios incluidos

### 🟦 `deteccionRostros` (Cloud Run, IAM)

- Recibe una imagen capturada desde el cliente.
- Detecta el rostro mediante una red MTCNN.
- Acondiciona la imagen aplicando filtros, normalización y recorte.
- Devuelve una imagen centrada en el rostro.

### 🟦 `extraccionEmbedding` (Cloud Run, IAM)

- Recibe la imagen procesada.
- Aplica el modelo FaceNet para extraer un vector facial de 512 dimensiones.
- Devuelve el embedding como JSON.

### 🟩 `almacenarEmbedding` (Cloud Run)

- Recibe 9 imágenes de un nuevo usuario.
- Llama a `deteccionRostros` y `extraccionEmbedding` internamente.
- Calcula un vector promedio y lo guarda en Firebase Firestore.

### 🟨 `accesoRF` (Cloud Function)

- Recibe una imagen para autenticar un usuario regular.
- Llama a los servicios de detección y extracción para generar el embedding.
- Compara el vector resultante contra los almacenados y retorna si hay coincidencia.

---

## 🧠 Tecnologías utilizadas

- Python 3.x  
- Flask / Gunicorn (para contenedores)  
- TensorFlow / FaceNet  
- OpenCV  
- Google Cloud Run + IAM  
- Firebase Admin SDK  
- MTCNN (detección de rostros)

---

## 🔐 Seguridad

- Los servicios `deteccionRostros` y `extraccionEmbedding` están protegidos mediante **IAM**, y solo pueden ser llamados desde `almacenarEmbedding` y `accesoRF`.
- Todas las comunicaciones entre microservicios se realizan mediante **HTTPS** con autenticación de servicio.
- No se exponen endpoints públicos para el procesamiento de fotos.
