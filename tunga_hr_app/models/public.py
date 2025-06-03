from datetime import datetime, timezone
from typing import Optional
from flask import current_app
from time import time

from sqlalchemy import (
    Integer, 
    String, 
    ForeignKey, 
    Boolean, 
    DateTime
)

from sqlalchemy.orm import ( 
    Mapped, 
    mapped_column, 
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import jwt as jwt_serializer
from tunga_hr_app import db, jwt
from ..utils.applications import generate_organization_code


class User(db.Model):

    __bind_key__ = "public"
    __table_args__ = {"schema": "public"}

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64), index=True)
    last_name: Mapped[str] = mapped_column(String(64), index=True)
    job_title: Mapped[str] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(64), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[bool] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc), 
                                                 onupdate=lambda: datetime.now(timezone.utc))
    

    @property
    def password(self):
        raise AttributeError('Password cannot be accessed')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_organization_id(self):
        return UserOrganization.query.filter_by(user_id=self.user_id).first().organization_id
    
    def get_organization(self):
        organization_id = UserOrganization.query.filter_by(user_id=self.user_id).first()
        return Organization.query.filter_by(organization_id=organization_id.organization_id).first().organization_code
    
    def get_organization_name(self):
        organization_id = UserOrganization.query.filter_by(user_id=self.user_id).first()
        return Organization.query.filter_by(organization_id=organization_id.organization_id).first().organization_name
    
    def get_account_confirmation_token(self, expires_in=600000):
        return jwt_serializer.encode(
            {'confirm_account': self.user_id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_account_confirmation_token(token):
        try:
            user_id = jwt_serializer.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['confirm_account']
        except Exception:
            return
        return db.session.get(User, user_id)
    
    def __init__(self, data, new_user=True):
        for field in ['first_name', 'last_name', 'email', 'phone_number', 'role']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
        
    def __repr__(self):
        return f'<User: {self.email}> - Organization: {self.organization_id}>'

# callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format.
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user

# Callback function that loads a user from the database whenever
# a protected route is accessed.
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(user_id=identity).one_or_none()


class Organization(db.Model):

    __bind_key__ = "public"
    __table_args__ = {"schema": "public"}

    organization_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_name: Mapped[str] = mapped_column(String(240), index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    organization_code: Mapped[str] = mapped_column(String(120), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, 
                                                 default=lambda: datetime.now(timezone.utc), 
                                                 onupdate=lambda: datetime.now(timezone.utc))
 
    
    def __init__(self, data):
        for field in ['organization_name', 'country', 'organization_code']:             
            if field in data:
                setattr(self, field, data[field].title())
        if 'organization_code' not in data:
            setattr(self, 'organization_code', generate_organization_code(data['organization_name'])) 
            

    def __repr__(self):
        return f'<Organization: {self.organization_name}> - ID: {self.organization_id}>'

    
class UserOrganization(db.Model):

    __bind_key__ = "public"
    __table_args__ = {"schema": "public"}

    user_id: Mapped[Optional[int]] = mapped_column(Integer,
                                                    ForeignKey(User.user_id), 
                                                    primary_key=True)
    
    organization_id: Mapped[Optional[int]] = mapped_column(Integer,
                                                    ForeignKey(Organization.organization_id), 
                                                    primary_key=True)


class Invited_Users(db.Model):

    __bind_key__ = "public"
    __table_args__ = {"schema": "public"}

    invite_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(120), index=True, nullable=True)
    job_title: Mapped[str] = mapped_column(String(120), nullable=True)
    role: Mapped[bool] = mapped_column(String(20), nullable=True)
    invited_by: Mapped[int] = mapped_column(Integer) 
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, index=True, 
                                                 default=lambda: datetime.now(timezone.utc), 
                                                 onupdate=lambda: datetime.now(timezone.utc))
    

    def get_invite_token(self, organization_id, expires_in=600000): #TODO: Set a time for the time to expire
        return jwt_serializer.encode(
            {
                'email': self.email, 
                'organization_id': organization_id, 
                'role': self.role, 
                'job_title': self.job_title, 
                'exp': time() + expires_in
            },
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_invite_token(token):
        try:
            payload = jwt_serializer.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])
        except Exception:
            return
        return {
            'email': payload['email'],
            'role': payload['role'], 
            'organization_id': payload['organization_id']
        }

    def __repr__(self):
        return f'<Invite: {self.email}> - by: {self.invited_by}>'