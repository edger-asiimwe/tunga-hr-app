"""Middleware for the API

for handling tenant requests
"""

from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from ..models.public import UserOrganization
from .database import Database


def change_tenant_schema():
    """Before request

    switch tenant schema
    """
    verify_jwt_in_request()

    tenant = get_jwt().get("tenant")

    if not tenant:
        return {"message": "You are not logged into any tenant"}, 403

    user = get_jwt_identity()
    
    if not UserOrganization.query.filter_by(user_id=user, organization_id=tenant).first():
        return {"message": "You are not a member of this tenant"}, 403

    Database(tenant).switch_schema()