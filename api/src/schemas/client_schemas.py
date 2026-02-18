"""
Schemas de validation pour les clients
"""

from datetime import date, datetime
from typing import Any, Dict
from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates


REFERENTIELS = ["SYSCOHADA", "IFRS", "PCG"]
CIVILITIES = ["M", "Mme", "Mlle"]


class ClientCreateSchema(Schema):
    """Schema pour la creation d'un client (aligne sur NewClient.vue)."""

    class Meta:
        unknown = EXCLUDE

    company_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
        error_messages={"required": "Le nom de l'entreprise est requis."},
    )
    sector = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
        error_messages={"required": "Le secteur est requis."},
    )
    address = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=300),
        error_messages={"required": "L'adresse est requise."},
    )
    referentiel = fields.Str(
        required=True,
        validate=validate.OneOf(REFERENTIELS),
        error_messages={"required": "Le referentiel comptable est requis."},
    )
    legal_form = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=80),
        error_messages={"required": "La forme legale est requise."},
    )
    responsable_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
        error_messages={"required": "Le nom du responsable est requis."},
    )
    civility = fields.Str(
        required=True,
        validate=validate.OneOf(CIVILITIES),
        error_messages={"required": "La civilite est requise."},
    )
    responsable_function = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
        error_messages={"required": "La fonction du responsable est requise."},
    )
    RCCM = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=80),
        error_messages={"required": "Le numero RCCM est requis."},
    )
    country = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
        error_messages={"required": "Le pays est requis."},
    )
    creation_date = fields.Date(
        required=True,
        format="%Y-%m-%d",
        error_messages={
            "required": "La date de creation de l'entreprise est requise.",
            "invalid": "Le format de la date de creation doit etre YYYY-MM-DD.",
        },
    )

    @validates("referentiel")
    def _normalize_referentiel(self, value: str) -> None:
        # Marshmallow validates after load; rely on allowed upper-case values.
        if value and value.upper() not in REFERENTIELS:
            raise ValidationError("Referentiel invalide. Valeurs autorisees: SYSCOHADA, IFRS, PCG.")


class ClientUpdateSchema(Schema):
    """Schema pour la mise a jour d'un client."""

    class Meta:
        unknown = EXCLUDE

    _id = fields.Str(required=True, error_messages={"required": "L'ID du client est requis."})
    company_name = fields.Str(required=False, validate=validate.Length(min=2, max=120))
    sector = fields.Str(required=False, validate=validate.Length(min=2, max=120))
    address = fields.Str(required=False, validate=validate.Length(min=2, max=300))
    referentiel = fields.Str(required=False, validate=validate.OneOf(REFERENTIELS))
    legal_form = fields.Str(required=False, validate=validate.Length(min=2, max=80))
    responsable_name = fields.Str(required=False, validate=validate.Length(min=2, max=120))
    civility = fields.Str(required=False, validate=validate.OneOf(CIVILITIES))
    responsable_function = fields.Str(required=False, validate=validate.Length(min=2, max=120))
    RCCM = fields.Str(required=False, validate=validate.Length(min=2, max=80))
    country = fields.Str(required=False, validate=validate.Length(min=2, max=120))
    creation_date = fields.Date(required=False, format="%Y-%m-%d", allow_none=True)


class ClientResponseSchema(Schema):
    """Schema de sortie pour les clients."""

    class Meta:
        unknown = EXCLUDE

    _id = fields.Str(required=True)
    company_name = fields.Str(required=True)
    sector = fields.Str(required=True)
    address = fields.Str(required=True)
    referentiel = fields.Str(required=False, allow_none=True)
    legal_form = fields.Str(required=False, allow_none=True)
    responsable_name = fields.Str(required=False, allow_none=True)
    civility = fields.Str(required=False, allow_none=True)
    responsable_function = fields.Str(required=False, allow_none=True)
    RCCM = fields.Str(required=False, allow_none=True)
    country = fields.Str(required=False, allow_none=True)
    creation_date = fields.Str(required=False, allow_none=True)


class ClientListResponseSchema(Schema):
    """Schema de liste clients."""

    clients = fields.List(fields.Nested(ClientResponseSchema))
    total = fields.Int()


class ClientWithMissionsSchema(ClientResponseSchema):
    """Schema client avec missions."""

    missions = fields.List(fields.Dict(), allow_none=True)


def validate_client_data(data: Dict[str, Any], schema_class: Schema) -> Dict[str, Any]:
    """Valide les donnees d'un client selon le schema fourni."""
    schema = schema_class()
    try:
        normalized = dict(data or {})
        if "referentiel" in normalized and isinstance(normalized["referentiel"], str):
            normalized["referentiel"] = normalized["referentiel"].upper().strip()
        if "creation_date" in normalized and isinstance(normalized["creation_date"], str):
            raw_date = normalized["creation_date"].strip()
            if raw_date:
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        normalized["creation_date"] = datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
        loaded = schema.load(normalized)
        if isinstance(loaded.get("creation_date"), (date, datetime)):
            loaded["creation_date"] = loaded["creation_date"].strftime("%Y-%m-%d")
        return loaded
    except ValidationError as err:
        raise ValidationError(err.messages)


def serialize_client(client_data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize un client pour la reponse."""
    schema = ClientResponseSchema()
    return schema.dump(client_data)


def serialize_client_list(clients_data: list) -> Dict[str, Any]:
    """Serialize une liste de clients pour la reponse."""
    schema = ClientListResponseSchema()
    return schema.dump({"clients": clients_data, "total": len(clients_data)})
