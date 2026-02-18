"""
Resources (contrôleurs) pour l'API
"""

from .client_resources import (
    ClientResource,
    new_cust,
    show_cust,
    show_info,
    update_cust,
    delete_cust
)

__all__ = [
    'ClientResource',
    'new_cust',
    'show_cust', 
    'show_info',
    'update_cust',
    'delete_cust'
]
