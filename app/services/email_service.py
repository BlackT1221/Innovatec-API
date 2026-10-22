import requests
import os

def enviar_correo_brevo(destinatario: str, codigo: str):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": os.getenv("BREVO_API_KEY"),
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Innovatec CBA", "email": "tu_correo_verificado@gmail.com"},
        "to": [{"email": destinatario}],
        "subject": "Código de Verificación - Innovatec CBA",
        "htmlContent": f"<h3>Tu código OTP es: <strong>{codigo}</strong></h3>"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Error en Brevo: {response.text}")