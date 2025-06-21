import pytz
from datetime import datetime

def obtener_hora_actual():
    zh = pytz.timezone("America/Mexico_City")
    return datetime.now(zh).strftime("%H:%M:%S")

def obtener_fecha_actual():
    zh = pytz.timezone("America/Mexico_City")
    return datetime.now(zh).strftime("%d-%m-%Y")

def crearDia(documento_dia, hora_actual):
    documento_dia.set({
        "entrada": hora_actual,
        "metodo": "RF",
        "salida": "",
        "num_registros": 1,
        "registro_1": hora_actual
    })

def verificarNumeroRegistros(documento_dia, hora_actual):
    datos = documento_dia.get().to_dict()
    num = datos.get("num_registros", 0) + 1
    actualizaciones = {
        f"registro_{num}": hora_actual,
        "num_registros": num
    }
    if num % 2 == 0:
        actualizaciones["salida"] = hora_actual
    documento_dia.update(actualizaciones)

def guardarAcceso(db, user_id, tipo_registro):
    try:
        doc_usuario = db.collection("usuarios").document(user_id).get()
        historial_id = doc_usuario.to_dict().get("historial_accesos")
        if not historial_id:
            print("'historial_accesos' no encontrado")
            return "Historial no encontrado"

        acceso_doc = db.collection("Control_Asistencia").document(historial_id)
        fecha_actual = obtener_fecha_actual()
        hora_actual = obtener_hora_actual()
        documento_dia = acceso_doc.collection("Accesos").document(fecha_actual)

        if not documento_dia.get().exists:
            if tipo_registro == "salida":
                print("No se puede registrar salida sin entrada")
                return "No se puede registrar salida sin entrada"
            else:
                crearDia(documento_dia, hora_actual)
                return True
        else:
            datos = documento_dia.get().to_dict()
            num = datos.get("num_registros", 0)
            ultimo_registro = "salida" if num % 2 == 0 else "entrada"
            if tipo_registro == ultimo_registro:
                print(f"Ya se registró {ultimo_registro}")
                return f"Ya se registró {ultimo_registro}"
            verificarNumeroRegistros(documento_dia, hora_actual)
            return True

    except Exception as e:
        print(f"Error en guardarAcceso(): {e}")
        return f"Error: {e}"
