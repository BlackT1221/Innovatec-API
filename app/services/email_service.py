import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def enviar_correo_otp(destinatario: str, codigo: str):
    """
    Envía el código OTP utilizando la API HTTP de Resend (Puerto 443 - No bloqueado por Render).
    """
    try:
        params = {
            # Si usas el dominio gratuito de prueba de Resend, debe ser "onboarding@resend.dev"
            # Si ya verificaste tu dominio, puedes usar "no-reply@tudominio.com"
            "from": "Innovatec CBA <onboarding@resend.dev>",
            "to": [destinatario],
            "subject": "Código de Verificación - Innovatec CBA",
            "html": f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #38A800;">Innovatec CBA - Verificación de Acceso</h2>
                <p>Has solicitado iniciar sesión en la plataforma de evaluación.</p>
                <p>Tu código de acceso temporal es:</p>
                <div style="background: #f4f4f4; padding: 15px; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 5px; color: #38A800; border-radius: 8px;">
                    {codigo}
                </div>
                <p style="margin-top: 20px; font-size: 12px; color: #777;">Este código expirará en unos minutos. Si no solicitaste este código, puedes ignorar este mensaje.</p>
            </div>
            """,
        }

        response = resend.Emails.send(params)
        print(f"Correo enviado exitosamente a {destinatario}. ID: {response.get('id')}")
        return True
    except Exception as e:
        print(f"Error crítico al enviar correo con Resend: {e}")
        raise e