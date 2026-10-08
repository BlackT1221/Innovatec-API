import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

def generar_hoja_evaluacion_pdf(
    asignacion_id: str, 
    nombre_evaluador: str, 
    nombre_proyecto: str, 
    criterios: list
) -> io.BytesIO:
    """
    Genera un PDF en memoria con marcadores fiduciarios, QR y burbujas OMR.
    """
    buffer = io.BytesIO()
    
    # Usamos tamaño carta (letter). width=612.0, height=792.0 puntos
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- 1. DIBUJAR MARCADORES FIDUCIARIOS ---
    # Cuadrados negros de 30x30 puntos en las 4 esquinas. 
    # Margen de 40 puntos desde el borde para evitar que la impresora los corte.
    margen = 40
    tamano_marcador = 30
    
    c.setFillColorRGB(0, 0, 0) # Negro absoluto
    # Superior Izquierda
    c.rect(margen, height - margen - tamano_marcador, tamano_marcador, tamano_marcador, fill=1)
    # Superior Derecha
    c.rect(width - margen - tamano_marcador, height - margen - tamano_marcador, tamano_marcador, tamano_marcador, fill=1)
    # Inferior Izquierda
    c.rect(margen, margen, tamano_marcador, tamano_marcador, fill=1)
    # Inferior Derecha
    c.rect(width - margen - tamano_marcador, margen, tamano_marcador, tamano_marcador, fill=1)


    # --- 2. GENERAR E INSERTAR CÓDIGO QR ---
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(asignacion_id) # El UUID que leerá OpenCV
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir imagen PIL a un formato que ReportLab entienda
    qr_io = io.BytesIO()
    img_qr.save(qr_io, format="PNG")
    qr_io.seek(0)
    
    # Ubicar QR en la esquina superior derecha, debajo del marcador
    tamano_qr = 80
    qr_x = width - margen - tamano_qr - 5
    qr_y = height - margen - tamano_marcador - tamano_qr - 20
    c.drawImage(ImageReader(qr_io), qr_x, qr_y, width=tamano_qr, height=tamano_qr)


    # --- 3. DIBUJAR TEXTOS (CABECERA) ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margen + 40, height - 80, "RÚBRICA DE EVALUACIÓN - CBA")
    
    c.setFont("Helvetica", 12)
    c.drawString(margen + 40, height - 110, f"Proyecto: {nombre_proyecto}")
    c.drawString(margen + 40, height - 130, f"Evaluador: {nombre_evaluador}")
    c.drawString(margen + 40, height - 150, "Instrucciones: Rellene completamente el círculo (Tinta negra/azul).")
    
    # Línea separadora
    c.line(margen, height - 170, width - margen, height - 170)


    # --- 4. DIBUJAR CRITERIOS Y BURBUJAS OMR ---
    y_actual = height - 220
    radio_burbuja = 8
    
    for idx, criterio in enumerate(criterios):
        # Si llegamos al final de la página, creamos una nueva (aunque lo ideal es que quepa en 1)
        if y_actual < 100:
            c.showPage()
            y_actual = height - 100
            
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margen, y_actual, f"{idx + 1}. {criterio['titulo']} ({criterio['peso_porcentual']}%)")
        
        c.setFont("Helvetica", 9)
        if 'descripcion' in criterio and criterio['descripcion']:
            c.drawString(margen, y_actual - 15, criterio['descripcion'][:80] + "...") # Truncar si es muy largo
        
        # Dibujar las 5 burbujas de calificación
        burbuja_x_inicial = 350
        espaciado = 40
        
        c.setFont("Helvetica", 8)
        for i in range(1, 6): # Escala del 1 al 5
            x_centro = burbuja_x_inicial + (i * espaciado)
            y_centro = y_actual - 5
            
            # Dibujar el círculo vacío
            c.setLineWidth(1)
            c.circle(x_centro, y_centro, radio_burbuja, stroke=1, fill=0)
            # Dibujar el número encima de la burbuja
            c.drawCentredString(x_centro, y_centro + 12, str(i))
            
        y_actual -= 60 # Espacio para el siguiente criterio

    # --- 5. FINALIZAR Y RETORNAR ---
    c.save()
    buffer.seek(0)
    return buffer