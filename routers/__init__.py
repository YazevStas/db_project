from .admin import router as admin_router
from .tech_admin import router as tech_admin_router
from .manager import router as manager_router
from .cashier import router as cashier_router
from .trainer import router as trainer_router
from .client import router as client_router

__all__ = [
    'admin_router',
    'tech_admin_router',
    'manager_router',
    'cashier_router',
    'trainer_router',
    'client_router'
]