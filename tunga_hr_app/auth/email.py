from flask import render_template, current_app
from tunga_hr_app.email import send_email


def send_account_validation_email(user):
    token = user.get_account_confirmation_token()
    validation_link = f"{current_app.config['BASE_CLIENT_URL']}/account/validate-account/?token={token}"

    send_email(subject='[Tunga HR] - Confirm Account',
               sender=current_app.config['MAIL_DEFAULT_SENDER'],
               recipients=[user.email],
               html_body=render_template('account_validation.html',
                                         organization_name=user.get_organization_name(), 
                                         url=validation_link))