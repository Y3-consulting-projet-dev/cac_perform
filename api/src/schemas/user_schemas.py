"""
Schémas de validation pour la gestion des utilisateurs
"""

from marshmallow import Schema, fields, validate, post_load, ValidationError
from bson import ObjectId
import re

class ObjectIdField(fields.Field):
    """Champ personnalisé pour ObjectId MongoDB"""
    
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        if not ObjectId.is_valid(value):
            raise ValidationError("Invalid ObjectId.")
        return ObjectId(value)

def validate_email(email):
    """Validation personnalisée pour l'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Format d'email invalide.")

def validate_password(password):
    """Validation personnalisée pour le mot de passe"""
    if len(password) < 8:
        raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Le mot de passe doit contenir au moins une majuscule.")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Le mot de passe doit contenir au moins une minuscule.")
    
    if not re.search(r'\d', password):
        raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")

class UserRegistrationSchema(Schema):
    """Schéma pour l'inscription d'un utilisateur"""
    
    user_id = fields.String(required=False, allow_none=True)  # Généré automatiquement
    firstname = fields.String(
        required=True, 
        validate=validate.Length(min=2, max=50),
        error_messages={"required": "Le prénom est requis."}
    )
    lastname = fields.String(
        required=True, 
        validate=validate.Length(min=2, max=50),
        error_messages={"required": "Le nom est requis."}
    )
    email = fields.Email(
        required=True,
        validate=validate_email,
        error_messages={"required": "L'email est requis."}
    )
    password = fields.String(
        required=True,
        validate=validate_password,
        load_only=True,  # Ne jamais sérialiser le mot de passe
        error_messages={"required": "Le mot de passe est requis."}
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf([
            "Administrateur", 
            "Manager", 
            "Auditeur Senior", 
            "Auditeur", 
            "Stagiaire"
        ]),
        error_messages={"required": "Le rôle est requis."}
    )
    grade = fields.String(
        required=True,
        validate=validate.OneOf([
            "Junior", 
            "Confirmé", 
            "Senior", 
            "Expert", 
            "Directeur"
        ]),
        error_messages={"required": "Le grade est requis."}
    )
    departement = fields.String(
        required=True,
        validate=validate.OneOf([
            "Audit", 
            "Conseil", 
            "Expertise Comptable", 
            "Juridique", 
            "Administration"
        ]),
        error_messages={"required": "Le département est requis."}
    )

class UserLoginSchema(Schema):
    """Schéma pour la connexion d'un utilisateur"""
    
    email = fields.Email(
        required=True,
        validate=validate_email,
        error_messages={"required": "L'email est requis."}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "Le mot de passe est requis."}
    )

class UserUpdateSchema(Schema):
    """Schéma pour la mise à jour d'un utilisateur"""
    
    user_id = ObjectIdField(required=False, data_key="_id")
    firstname = fields.String(validate=validate.Length(min=2, max=50))
    lastname = fields.String(validate=validate.Length(min=2, max=50))
    email = fields.Email(validate=validate_email)
    role = fields.String(
        validate=validate.OneOf([
            "Administrateur", 
            "Manager", 
            "Auditeur Senior", 
            "Auditeur", 
            "Stagiaire"
        ])
    )
    grade = fields.String(
        validate=validate.OneOf([
            "Junior", 
            "Confirmé", 
            "Senior", 
            "Expert", 
            "Directeur"
        ])
    )
    departement = fields.String(
        validate=validate.OneOf([
            "Audit", 
            "Conseil", 
            "Expertise Comptable", 
            "Juridique", 
            "Administration"
        ])
    )
    is_active = fields.Boolean()

class UserResponseSchema(Schema):
    """Schéma pour la réponse utilisateur (sans mot de passe)"""
    
    # Ajoute _id directement
    _id = ObjectIdField(dump_only=True)

    firstname = fields.String()
    lastname = fields.String()
    email = fields.String()
    role = fields.String()
    grade = fields.String()
    departement = fields.String()
    is_active = fields.Boolean()
    created_at = fields.Raw(dump_only=True)
    last_login = fields.Raw(dump_only=True, allow_none=True)
    
    @post_load
    def make_full_name(self, data, **kwargs):
        """Ajoute le nom complet"""
        if 'firstname' in data and 'lastname' in data:
            data['full_name'] = f"{data['firstname']} {data['lastname']}"
        return data

class TokenResponseSchema(Schema):
    """Schéma pour la réponse de connexion avec token"""
    
    token = fields.String(required=True)
    user = fields.Nested(UserResponseSchema, required=True)
    expires_in = fields.Integer(required=True)

# Instances des schémas pour utilisation
user_registration_schema = UserRegistrationSchema()
user_login_schema = UserLoginSchema()
user_update_schema = UserUpdateSchema()
user_response_schema = UserResponseSchema()
users_response_schema = UserResponseSchema(many=True)
token_response_schema = TokenResponseSchema()

def validate_user_registration(data):
    """Valide les données d'inscription"""
    errors = user_registration_schema.validate(data)
    if errors:
        raise ValidationError(errors)
    return user_registration_schema.load(data)

def validate_user_login(data):
    """Valide les données de connexion"""
    errors = user_login_schema.validate(data)
    if errors:
        raise ValidationError(errors)
    return user_login_schema.load(data)

def validate_user_update(data):
    """Valide les données de mise à jour"""
    errors = user_update_schema.validate(data, partial=True)
    if errors:
        raise ValidationError(errors)
    return user_update_schema.load(data, partial=True)

def serialize_user(user_doc):
    """Sérialise un document utilisateur"""
    return user_response_schema.dump(user_doc)

def serialize_user_list(user_docs):
    """Sérialise une liste d'utilisateurs"""
    return users_response_schema.dump(user_docs)

def serialize_token_response(token, user_doc, expires_in):
    """Sérialise la réponse de connexion"""
    return token_response_schema.dump({
        'token': token,
        'user': user_doc,
        'expires_in': expires_in
    })

# Constantes pour les rôles et grades
ROLES = [
    "Administrateur", 
    "Manager", 
    "Auditeur Senior", 
    "Auditeur", 
    "Stagiaire"
]

GRADES = [
    "Junior", 
    "Confirmé", 
    "Senior", 
    "Expert", 
    "Directeur"
]

DEPARTEMENTS = [
    "Audit", 
    "Conseil", 
    "Expertise Comptable", 
    "Juridique", 
    "Administration"
]
