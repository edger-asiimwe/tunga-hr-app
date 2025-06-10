from flask import render_template, current_app
from tunga_hr_app.email import send_email


def send_invite_user_email(invited_user, organization_id, organization_name):
    token = invited_user.get_invite_token(organization_id)
    invite_link = f"{current_app.config['BASE_CLIENT_URL']}/confirm-invite/?token={token}"

    print(f"Invite link: {invite_link}")

    #send_email(subject='[Tunga HR] - Invite to join workspace',
    #          sender=current_app.config['MAIL_DEFAULT_SENDER'],
    #          recipients=[invited_user.email],
    #          html_body=render_template('invite_user.html',
    #                                    organization_name=organization_name, 
    #                                    url=invite_link))
    

def send_password_reset_email(user):
    token = user.get_account_confirmation_token()
    reset_link = f"{current_app.config['BASE_CLIENT_URL']}/reset-password/?token={token}"

    send_email(subject='[Tunga HR] - Reset Password',
               sender=current_app.config['MAIL_DEFAULT_SENDER'],
               recipients=[user.email],
               html_body=render_template('password_reset.html',
                                         name=user.first_name,
                                         url=reset_link))