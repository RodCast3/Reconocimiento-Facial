import numpy as np

def calcularDistancia(vector1, vector2):
    vector1 = np.array(vector1)
    vector2 = np.array(vector2)
    if vector1.shape != vector2.shape:
        raise ValueError("Error en las dimensiones de los vectores")
    return np.linalg.norm(vector1 - vector2)
