"""
Este script proporciona la clase `EmailSender` para enviar correos electronicos
utilizando el servidor SMTP de Gmail. Permite especificar destinatarios, incluir
archivos adjuntos y agregar direcciones de copia oculta (BCC).

### Descripcion
La clase `EmailSender` facilita el envio de correos electronicos utilizando el
protocolo SMTP de Gmail. Incluye la capacidad de adjuntar múltiples archivos y
agregar destinatarios en copia oculta para una mayor flexibilidad.

### Parámetros del constructor
- **user_gmail** (str): Direccion de correo de Gmail utilizada para el envio.
- **app_password** (str): Contraseña de la aplicacion generada en la configuracion
  de Gmail. Se requiere habilitar el acceso de aplicaciones menos seguras o usar
  la autenticacion de dos factores y generar una contraseña especifica para aplicaciones.

### Ejemplo de uso
```python
# Crear una instancia de EmailSender
email_sender = EmailSender("myuser@gmail.com", "mypassword")

# Configurar los detalles del correo
to_address = "recipient@example.com"
bcc_addresses = "hidden@example.com"
subject = "Asunto del correo"
body = "Este es el cuerpo del correo. Adjunto un archivo."
attachments = "documento1.pdf,imagen2.jpg"

# Enviar el correo
email_sender.send_email(to_address, subject, body, attachments, bcc_addresses)
"""

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


class EmailSender:
    """
    Clase para enviar correos electronicos utilizando el servidor SMTP de Gmail.

    :param user_gmail: Direccion de correo de Gmail.
    :type user_gmail: str
    :param app_password: Contraseña de la aplicacion generada en Gmail.
    :type app_password: str
    """

    def __init__(self, user_gmail: str, app_password: str) -> None:
        """
        Constructor de la clase EmailSender.

        :param user_gmail: Direccion de correo electronico de Gmail.
        :type user_gmail: str
        :param app_password: Contraseña de la aplicacion generada en la configuracion
          de Gmail. Se requiere habilitar el acceso de aplicaciones menos seguras o
          usar la autenticacion de dos factores y generar una contraseña especifica
          para aplicaciones.
        :type app_password: str
        """
        self.user_gmail = user_gmail
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: Optional[str] = None,
        bcc_addresses: Optional[str] = None,
    ) -> None:
        """
        Envia un correo electronico con los detalles especificados.

        :param to_address: Direccion de correo del destinatario.
        :type to_address: str
        :param subject: Asunto del correo.
        :type subject: str
        :param body: Cuerpo del correo.
        :type body: str
        :param attachments: Archivos adjuntos separados por comas (opcional).
        :type attachments: Optional[str]
        :param bcc_addresses: Direcciones de correo en copia oculta separadas por comas (opcional).
        :type bcc_addresses: Optional[str]
        """
        # Crear el mensaje
        msg = MIMEMultipart()
        msg["From"] = self.user_gmail
        msg["To"] = ", ".join([to_address.replace(" ", "")])
        if bcc_addresses:
            msg["Bcc"] = ", ".join([bcc_addresses.replace(" ", "")])
        msg["Subject"] = subject

        # Agregar el cuerpo del mensaje
        msg.attach(MIMEText(body, "plain"))

        # Adjuntar archivos si se especifican
        if attachments:
            attachments_list = attachments.replace(" ", "").split(",")
            for file in attachments_list:
                attachment = MIMEBase("application", "octet-stream")
                with open(file, "rb") as attachment_file:
                    attachment.set_payload(attachment_file.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file)}",
                )
                msg.attach(attachment)

        # Conectar al servidor SMTP y enviar el correo
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.user_gmail, self.app_password)
            server.send_message(msg)


if __name__ == "__main__":
    email_sender = EmailSender("myuser@gmail.com", "mypassword")
    to_address = "ctacoronte@itccanarias.org"
    bcc_addresses = "itc.eerr.info@gmail.com"
    subject = "Prueba de envio de correo"
    body = "Este es el cuerpo del correo. Adjunto un archivo docx. Aqui hay correos en CCO."
    attachments = "file1.docx,file2.pdf"

    email_sender.send_email(to_address, subject, body, attachments, bcc_addresses)
