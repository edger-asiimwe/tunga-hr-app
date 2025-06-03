import psycopg2
from . import account

from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)

from flask import request, jsonify, make_response

from tunga_hr_app import db

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from .email import send_invite_user_email, send_password_reset_email
from ..models.public import User, Organization, Invited_Users, UserOrganization
from ..utils.middleware import change_tenant_schema


@account.before_request
def before_request():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = request.headers.get(
            'Access-Control-Request-Headers', 'Authorization, Content-Type'
        )
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.status_code = 200
        return response  
    change_tenant_schema()


@account.route('/validate-account/<token>', methods=['GET', 'POST'])
def validate_account(token):
    user = User.verify_account_confirmation_token(token)

    if not user:
        return jsonify({'error': 'Account validation failed.'}), 400
    if user.verified:
        return jsonify({'error': 'Account is already verified'}), 400
    
    user.active = True
    user.verified = True

    organization = db.session.get(Organization, user.get_organization_id())
    organization.active = True
    db.session.commit()

    return jsonify({'message': 'Account successfully validated'}), 200


@account.route('/invite-user', methods=['POST'])
@jwt_required()
def invite_user():
    current_user = get_jwt_identity()

    request_data = request.get_json()

    try:
        invited_user = Invited_Users(
           email = request_data['email'],
           job_title = request_data.get('job_title'),
           role = request_data['role'], 
           invited_by = current_user
        )
        db.session.add(invited_user)
        db.session.commit()

        logged_user = User.query.filter_by(user_id=current_user).first()

        send_invite_user_email(
            invited_user=invited_user, 
            organization_id=logged_user.get_organization_id(),
            organization_name=logged_user.get_organization_name()
        )

    except Exception as e:
        return jsonify({'error': e}), 400

    return jsonify({'message': 'Email invite successfully sent'}), 200


@account.route('/join-organization/<token>', methods=['POST'])
def join_organization(token):

    request_data = request.get_json()

    token_payload = Invited_Users.verify_invite_token(token)

    try:
        user = User(request_data)
        user.email = token_payload['email']
        user.job_title = token_payload['job_title']
        user.role = token_payload['role']
        user.active = True
        user.verified = True
        db.session.add(user)
        db.session.flush()

        user_organization = UserOrganization(user_id=user.user_id,
                                             organization_id=token_payload['organization_id'])
        db.session.add(user_organization)
        db.session.flush()

        db.session.query(Invited_Users).filter_by(email=token_payload['email']).delete()
        db.session.commit()

    except IntegrityError as e:
        db.session.rollback()
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            return jsonify({'error': f"Email Already In Use"}), 400
        else:
            return jsonify({'error': str(e)}), 400 

    return jsonify({'message': 'Account successfylly created'}), 200


@account.route('/view-users', methods=['GET'])
@jwt_required()
def view_users():
    current_user = get_jwt_identity()

    user_organization = UserOrganization.query.filter_by(user_id=current_user).first()
    
    if not user_organization:
        return jsonify({'message': 'Organization not found for the current user.'}), 404
    
    organization_id = user_organization.organization_id
    
    users = db.session.query(User).join(UserOrganization, User.user_id == UserOrganization.user_id).filter(UserOrganization.organization_id == organization_id).all()

    user_list = [{
        'user_id': user.user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'job_title': user.job_title,
        'email': user.email,
        'phone_number': user.phone_number,
        'active': user.active,
        'verified': user.verified,
        'role': user.role,
        'created_at': user.created_at
    } for user in users]

    return jsonify({'users': user_list}), 200


@account.route('/invited-users', methods=['GET'])
@jwt_required()
def invited_users():
    current_user_id = get_jwt_identity()
    
    user_org = UserOrganization.query.filter_by(user_id=current_user_id).first()
    
    if not user_org:
        return jsonify({"message": "Organization not found"}), 404
    
    organization_id = user_org.organization_id

    invited_by_user = Invited_Users.query.filter_by(invited_by=current_user_id).all()
    
    invited_in_org = (Invited_Users.query
                      .join(UserOrganization, UserOrganization.user_id == Invited_Users.invited_by)
                      .filter(UserOrganization.organization_id == organization_id)
                      .all())
    
    invited_users = {invite.invite_id: invite for invite in invited_by_user + invited_in_org}.values()
    
    invited_users_list = [
        {
            "invite_id": invite.invite_id,
            "email": invite.email,
            "job_title": invite.job_title,
            "role": invite.role,
            "invited_by": invite.invited_by,
            "created_at": invite.created_at.isoformat(),
            "updated_at": invite.updated_at.isoformat()
        } for invite in invited_users
    ]
    
    return jsonify({'users': invited_users_list}), 200


@account.route('/view-user', methods=['GET'])
@jwt_required()
def view_user():
    current_user = get_jwt_identity()

    user = db.session.query(User).filter_by(user_id=current_user).first()

    if not user:
        return jsonify({'message': 'You are not registered'}), 403
    
    return jsonify(
        {
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'job_title': user.job_title,
            'email': user.email,
            'phone_number': user.phone_number,
            'active': user.active,
            'created_at': user.created_at
        }
    ), 200


@account.route('/organization-info', methods=['GET'])
@jwt_required()
def orgnization_info():
    current_user = get_jwt_identity()

    user_organization = UserOrganization.query.filter_by(user_id=current_user).first()

    if not user_organization:
        return jsonify({"message": "You do not have permission to view this information"}), 403
    
    organization = db.session.query(Organization).filter_by(organization_id=user_organization.organization_id).first()

    if not organization:
        return jsonify({"message": "Organization not found"}), 404

    return jsonify({
        'organization_name': organization.organization_name,
        'country': organization.country, 
        'organization_code': organization.organization_code,
        'created_at': organization.created_at
    }), 200


@account.route('/update-user/<user_id>', methods=['PATCH'])
@jwt_required()
def update_user(user_id):
    current_user = get_jwt_identity()

    payload = request.get_json()

    user = db.session.query(User).filter_by(user_id=user_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    for field in payload:
        setattr(user, field, payload[field])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the user", "error": str(e)}), 500
    
    return jsonify({"message": "User updated successfully"}), 200


@account.route('/deactivate-user/<user_id>', methods=['GET'])
@jwt_required()
def deactivate_user(user_id):
    try:
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user.active:
            return jsonify({'message': 'User is already deactivated'}), 400
        user.active = False
        db.session.commit()
    except Exception as e:
        return jsonify({'error': e}), 400

    return jsonify(user_id), 200


@account.route('/reactivate-user/<user_id>', methods=['GET'])
@jwt_required()
def reactivate_user(user_id):
    try:
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if user.active:
            return jsonify({'message': 'User is already active'}), 400
        user.active = True
        db.session.commit()
    except Exception as e:
        return jsonify({'error': e}), 400

    return jsonify(user_id), 200


@account.route('/send-password-reset-email', methods=['POST'])
def send_passowrd_reset_email():
    email = request.get_json()['email']

    user = db.session.query(User).filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'No account associated with this email'}), 400
    
    send_password_reset_email(user)

    return jsonify({'message': 'Password reset email sent'}), 200


@account.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    password = request.get_json()['password']

    try:
        user = User.verify_account_confirmation_token(token)
    except Exception as e:
        return jsonify({'message': 'Failed to reset passowrd.'}), 400
    
    user.set_password(password)
    db.session.commit()

    return jsonify({'message': 'Password reset successfully'}), 200


@account.route('/update-organization', methods=['POST'])
@jwt_required()
def update_organization():
    current_user = get_jwt_identity()
    
    user_organization = UserOrganization.query.filter_by(user_id=current_user).first()
    if not user_organization:
        return jsonify({"message": "You do not have permission to update this organization"}), 403
    
    payload = request.get_json()

    organization = db.session.query(Organization).filter_by(organization_id=user_organization.organization_id).first()

    if not organization:
        return jsonify({"message": "Organization not found"}), 404

    for field in payload:
        if hasattr(organization, field):
            setattr(organization, field, payload[field])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the organization", "error": str(e)}), 500

    return jsonify({"message": "Organization updated successfully"}), 200