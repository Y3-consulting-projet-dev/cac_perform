"""
Schemas de validation pour la gestion des utilisateurs
"""

from marshmallow import Schema, fields, validate, post_load, ValidationError
from bson import ObjectId
import re


class ObjectIdField(fields.Field):
    """Champ personnalise pour ObjectId MongoDB"""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        if not ObjectId.is_valid(value):
            raise ValidationError("Invalid ObjectId.")
        return ObjectId(value)


def validate_email(email):
    """Validation personnalisee pour l'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Format d'email invalide.")


def validate_password(password):
    """Validation personnalisee pour le mot de passe"""
    if len(password) < 8:
        raise ValidationError("Le mot de passe doit contenir au moins 8 caracteres.")

    if not re.search(r'[A-Z]', password):
        raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")

    if not re.search(r'[a-z]', password):
        raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")

    if not re.search(r'\d', password):
        raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")


ROLES = [
    "Administrateur",
    "Manager",
    "Auditeur Senior",
    "Auditeur",
    "Stagiaire",
]

GRADES = [
    "Pre-emploi",
    "Assistant 1",
    "Assistant 2",
    "Senior 3",
    "Assistant Manager",
    "Manager 1",
    "Manager 2",
    "Manager 3",
    "Senior Manager",
]


class UserRegistrationSchema(Schema):
    """Schema pour l'inscription d'un utilisateur"""

    user_id = fields.String(required=False, allow_none=True)
    firstname = fields.String(
        required=True,
        validate=validate.Length(min=2, max=50),
        error_messages={"required": "Le prenom est requis."},
    )
    lastname = fields.String(
        required=True,
        validate=validate.Length(min=2, max=50),
        error_messages={"required": "Le nom est requis."},
    )
    email = fields.Email(
        required=True,
        validate=validate_email,
        error_messages={"required": "L'email est requis."},
    )
    password = fields.String(
        required=True,
        validate=validate_password,
        load_only=True,
        error_messages={"required": "Le mot de passe est requis."},
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf(ROLES),
        error_messages={"required": "Le role est requis."},
    )
    grade = fields.String(
        required=True,
        validate=validate.OneOf(GRADES),
        error_messages={"required": "Le grade est requis."},
    )


class UserLoginSchema(Schema):
    """Schema pour la connexion d'un utilisateur"""

    email = fields.Email(
        required=True,
        validate=validate_email,
        error_messages={"required": "L'email est requis."},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "Le mot de passe est requis."},
    )


class UserUpdateSchema(Schema):
    """Schema pour la mise a jour d'un utilisateur"""

    user_id = ObjectIdField(required=False, data_key="_id")
    firstname = fields.String(validate=validate.Length(min=2, max=50))
    lastname = fields.String(validate=validate.Length(min=2, max=50))
    email = fields.Email(validate=validate_email)
    role = fields.String(validate=validate.OneOf(ROLES))
    grade = fields.String(validate=validate.OneOf(GRADES))
    is_active = fields.Boolean()


class UserResponseSchema(Schema):
    """Schema pour la reponse utilisateur sans mot de passe"""

    _id = ObjectIdField(dump_only=True)
    firstname = fields.String()
    lastname = fields.String()
    email = fields.String()
    role = fields.String()
    grade = fields.String()
    is_active = fields.Boolean()
    created_at = fields.Raw(dump_only=True)
    last_login = fields.Raw(dump_only=True, allow_none=True)

    @post_load
    def make_full_name(self, data, **kwargs):
        if 'firstname' in data and 'lastname' in data:
            data['full_name'] = f"{data['firstname']} {data['lastname']}"
        return data


class TokenResponseSchema(Schema):
    """Schema pour la reponse de connexion avec token"""

    token = fields.String(required=True)
    user = fields.Nested(UserResponseSchema, required=True)
    expires_in = fields.Integer(required=True)


user_registration_schema = UserRegistrationSchema()
user_login_schema = UserLoginSchema()
user_update_schema = UserUpdateSchema()
user_response_schema = UserResponseSchema()
users_response_schema = UserResponseSchema(many=True)
token_response_schema = TokenResponseSchema()


def validate_user_registration(data):
    """Valide les donnees d'inscription"""
    errors = user_registration_schema.validate(data)
    if errors:
        raise ValidationError(errors)
    return user_registration_schema.load(data)


def validate_user_login(data):
    """Valide les donnees de connexion"""
    errors = user_login_schema.validate(data)
    if errors:
        raise ValidationError(errors)
    return user_login_schema.load(data)


def validate_user_update(data):
    """Valide les donnees de mise a jour"""
    errors = user_update_schema.validate(data, partial=True)
    if errors:
        raise ValidationError(errors)
    return user_update_schema.load(data, partial=True)


def serialize_user(user_doc):
    """Serialise un document utilisateur"""
    return user_response_schema.dump(user_doc)


def serialize_user_list(user_docs):
    """Serialise une liste d'utilisateurs"""
    return users_response_schema.dump(user_docs)


def serialize_token_response(token, user_doc, expires_in):
    """Serialise la reponse de connexion"""
    return token_response_schema.dump({
        'token': token,
        'user': user_doc,
        'expires_in': expires_in
    })
