"""
Schémas de validation pour l'API
"""

from .client_schemas import (
    ClientCreateSchema,
    ClientUpdateSchema,
    ClientResponseSchema,
    ClientListResponseSchema,
    ClientWithMissionsSchema,
    validate_client_data,
    serialize_client,
    serialize_client_list
)

__all__ = [
    'ClientCreateSchema',
    'ClientUpdateSchema', 
    'ClientResponseSchema',
    'ClientListResponseSchema',
    'ClientWithMissionsSchema',
    'validate_client_data',
    'serialize_client',
    'serialize_client_list'
]
