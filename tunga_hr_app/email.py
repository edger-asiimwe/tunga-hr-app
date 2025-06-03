from threading import Thread
from flask import current_app
# import requests
from flask_mail import Message
from tunga_hr_app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, html_body, text_body=None,
               attachments=None, sync=False):
    msg = Message(subject, sender=('Cherio', sender), recipients=recipients)
    msg.html = html_body

    if text_body:
        msg.body = text_body
    
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()