import psycopg2
import datetime

from . import auth

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)

from flask import request, jsonify

from tunga_hr_app import db

from .email import send_account_validation_email

from ..models import (
    User, 
    Organization,
    UserOrganization
)

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..utils.database import Database


@auth.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        request_data = request.get_json()

        try:
            # Create an organization profile
            organization = Organization(request_data)
            db.session.add(organization)

            # Create a user profile with a reference to the organization
            user = User(request_data)
            user.role = 'Admin'
            db.session.add(user)
            db.session.commit()

            # Create a user_organization profile with a reference to the user and organization
            account = UserOrganization(
                user_id=user.user_id,
                organization_id=organization.organization_id
            )
            db.session.add(account)
            db.session.commit()

            # Create new schema for Organization Tenant
            Database(organization.organization_id).create_tenant_schema()

            # Send account validation email 
            # Uncomment once emails are activated
            #send_account_validation_email(user=user)

        except IntegrityError as e:
            db.session.rollback()
            if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                return jsonify({'error': f"Email Already In Use"}), 400
            else:
                return jsonify({'error': str(e)}), 400    
        
        return jsonify({
            "status": "success",
            "message": "Account has been successfully created. A confirmation link has been sent to your email"
        }), 200


@auth.route('/login', methods=['POST'])
def login():
    request_data = request.get_json()
    try:
        user = User.query.filter_by(email=request_data['email']).first()
        
        if not user or not user.check_password(request_data['password']):
            return jsonify({
                    "message": "The email or password provided is incorrect."}), 401

        user_organization = UserOrganization.query.filter_by(
            user_id=user.user_id
            ).first_or_404()
            
        access_token = create_access_token(
                    identity=str(user.user_id),
                    additional_claims={"tenant": user_organization.organization_id},
                    expires_delta=datetime.timedelta(days=1)
                )
        
        refresh_token = create_refresh_token(
            identity=user.user_id,
            additional_claims={"tenant": str(user_organization.organization_id)}, 
            expires_delta=datetime.timedelta(days=1)
        )

        return jsonify(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "role": user.role
            }
        ), 200
    
    except ValidationError as err:
        return jsonify(err.messages), 400


@auth.route('/logout', methods=['POST'])
def logout():
    pass