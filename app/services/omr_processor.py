import cv2
import numpy as np
from pyzbar.pyzbar import decode
from fastapi import HTTPException

def ordenar_puntos(pts):
    """Ordena 4 puntos en orden: Arriba-Izquierda, Arriba-Derecha, Abajo-Derecha, Abajo-Izquierda"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def alinear_hoja(image):
    """Detecta el contorno más grande (la hoja de papel) y aplica transformación de perspectiva"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    contornos, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:5]

    contorno_hoja = None
    for c in contornos:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            contorno_hoja = approx
            break

    if contorno_hoja is None:
        return cv2.resize(image, (612, 792))

    rect = ordenar_puntos(contorno_hoja.reshape(4, 2))
    dst = np.array([
        [0, 0],
        [611, 0],
        [611, 791],
        [0, 791]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (612, 792))

# ==========================================
# NUEVAS FUNCIONES DIVIDIDAS
# ==========================================

def alinear_hoja_y_leer_qr(image_bytes: bytes):
    """Paso 1: Recibe la imagen, la endereza y extrae el UUID del QR."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Imagen no válida o corrupta.")

    warped = alinear_hoja(img)

    qrs = decode(warped)
    if not qrs:
        raise HTTPException(status_code=400, detail="No se detectó el código QR en la hoja.")
    
    asignacion_id = qrs[0].data.decode("utf-8")
    return warped, asignacion_id

def procesar_burbujas(warped_img, num_criterios: int) -> list:
    """Paso 2: Lee las burbujas basándose en la cantidad exacta de criterios."""
    gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV) 

    resultados_crudos = []
    y_actual_reportlab = 792 - 220 
    
    for idx in range(num_criterios):
        y_cv = 792 - y_actual_reportlab 
        pixeles_por_burbuja = []
        
        for i in range(1, 6): 
            x_cv = 350 + (i * 40) 
            roi = thresh[int(y_cv)-10 : int(y_cv)+10, int(x_cv)-10 : int(x_cv)+10]
            
            tinta = cv2.countNonZero(roi)
            pixeles_por_burbuja.append(tinta)
            
        max_tinta = max(pixeles_por_burbuja)
        
        if max_tinta > 50:
            calificacion_elegida = pixeles_por_burbuja.index(max_tinta) + 1 
        else:
            calificacion_elegida = 0 
            
        resultados_crudos.append({
            "criterio_indice": idx,
            "calificacion": calificacion_elegida,
            "pixeles_detectados": pixeles_por_burbuja
        })
        
        y_actual_reportlab -= 60 

    return resultados_crudos