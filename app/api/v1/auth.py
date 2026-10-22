import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.dependencies import get_db
from app.models.domain import Evaluador
from app.schemas.auth import RequestOTP, VerifyOTP
from app.services.email_service import enviar_correo_otp
from app.services.email import enviar_correo_otp

router = APIRouter(prefix="/auth", tags=["Autenticación por OTP"])

@router.post("/request-otp")
def solicitar_otp(payload: RequestOTP, db: Session = Depends(get_db)):
    """Busca al evaluador por correo, genera un código de 6 dígitos y se lo envía por Resend."""
    stmt = select(Evaluador).where(Evaluador.email == payload.email)
    evaluador = db.scalars(stmt).first()
    
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El correo electrónico no se encuentra registrado como evaluador en el sistema."
        )
        
    # Generar código aleatorio de 6 dígitos
    codigo_otp = f"{random.randint(0, 999999):06d}"
    
    # Expiración en 10 minutos (usando timezone UTC consciente)
    evaluador.otp_code = codigo_otp
    evaluador.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    db.commit()
    
    try:
        enviar_correo_otp(evaluador.email, codigo_otp)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo enviar el correo de verificación. Intente nuevamente en unos segundos."
        )
    
    return {"mensaje": "Código OTP enviado exitosamente al correo electrónico."}

@router.post("/verify-otp")
@router.post("/verify-otp")
def verificar_otp(payload: VerifyOTP, db: Session = Depends(get_db)):
    stmt = select(Evaluador).where(Evaluador.email == payload.email)
    evaluador = db.scalars(stmt).first()
    
    if not evaluador or evaluador.otp_code != payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código OTP inválido.")
        
    evaluador.otp_code = None
    evaluador.otp_expires_at = None
    db.commit()
    
    return {
        "mensaje": "Autenticación exitosa",
        "evaluador": {
            "id": str(evaluador.id),
            "nombre_completo": evaluador.nombre_completo,
            "email": evaluador.email,
            "rol": evaluador.rol
        }
    }