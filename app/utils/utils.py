from flask import flash, current_app, render_template
from flask import session
from flask_mail import Message
from ..extensions import mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def flash_message(message, category='info'):
    icon_map = {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'danger': 'error',
        'error': 'error'
    }
    icon = icon_map.get(category, 'info')
    session['flash_message'] = (icon, message)



YAHOO_PASS='fhdrznjvyessxlwy'    # not your account password
def send_email(subject, recipient, template, sender="workstation271s@yahoo.com", **kwargs):
    email_address = sender
    email_password = YAHOO_PASS 
    body = render_template(f'{template}.txt', **kwargs)
    
    # FIX ENCODING - Specifica UTF-8
    msg = MIMEMultipart('mixed')
    msg['From'] = email_address
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_charset('utf-8')
    
    # IMPORTANTE: Aggiungi encoding UTF-8 per il body
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.mail.yahoo.com', 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            text = msg.as_string()
            server.sendmail(email_address, recipient, text)
            print("Email inviata con successo!")
            server.quit()
    except Exception as e:
        print(f"Si è verificato un errore: {e}")
