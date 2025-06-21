import pytz
from datetime import datetime

def verificar_permiso(db, id_usuario):
    try:
        doc_usuario = db.collection("usuarios").document(id_usuario).get()
        datos_usuario = doc_usuario.to_dict()

        if not datos_usuario:
            return False, "Usuario no encontrado", None

        nombre_permiso = datos_usuario.get("permisos")
        if not nombre_permiso:
            return False, "Permiso no asignado", None

        doc_permiso = db.collection("Permisos").document(nombre_permiso).get()
        if not doc_permiso.exists:
            return False, "Documento de permiso no existe", None

        datos_permiso = doc_permiso.to_dict()

        # Obtener día actual en español
        dias_semana = {
            'monday': 'lunes',
            'tuesday': 'martes',
            'wednesday': 'miércoles',
            'thursday': 'jueves',
            'friday': 'viernes',
            'saturday': 'sábado',
            'sunday': 'domingo'
        }

        tz = pytz.timezone("America/Mexico_City")
        ahora = datetime.now(tz)
        dia_en = ahora.strftime("%A").lower()
        dia = dias_semana.get(dia_en)

        if not dia:
            return False, "Error obteniendo el día actual", None

        horarios = datos_permiso.get(dia)
        if not horarios:
            return False, f"Sin horarios asignados para hoy ({dia})", None

        hora_actual = ahora.strftime("%H:%M")

        for i in range(0, len(horarios), 2):
            hora_inicio = horarios[i]
            hora_fin = horarios[i + 1] if i + 1 < len(horarios) else None
            if hora_fin and hora_inicio <= hora_actual <= hora_fin:
                return True, "Permiso válido", datos_usuario.get("nombre")

        return False, "Hora fuera de rango", None

    except Exception as e:
        return False, f"Error verificando permisos: {str(e)}", None
