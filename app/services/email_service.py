import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import dotenv
dotenv.load_dotenv()

# Configura tus credenciales SMTP (o usa variables de entorno)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = dotenv.get_key(".env", "APPLICATION_EMAIL")
SENDER_PASSWORD = dotenv.get_key(".env", "APPLICATION_PASSWORD")

def enviar_correo_otp(destinatario: str, codigo: str):
    """Envía el código de acceso de 6 dígitos al correo del instructor."""
    asunto = "Tu código de acceso - Innovatec CBA"
    cuerpo = f"""
    <html>
      <body>
        <h2>Sistema de Evaluación de Proyectos CBA</h2>
        <p>Has solicitado iniciar sesión en la aplicación móvil.</p>
        <p>Tu código de acceso de un solo uso es:</p>
        <h1 style="color: #2e7d32; letter-spacing: 5px;">{codigo}</h1>
        <p>Este código expirará en 10 minutos. Si no solicitaste este código, puedes ignorar este mensaje.</p>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = asunto
    message["From"] = SENDER_EMAIL
    message["To"] = destinatario
    message.attach(MIMEText(cuerpo, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, destinatario, message.as_string())
    except Exception as e:
        print(f"Error enviando correo: {e}")
        # En desarrollo local, si no configuras SMTP, puedes imprimirlo en consola:
        print(f"[DEV] Código OTP para {destinatario}: {codigo}")