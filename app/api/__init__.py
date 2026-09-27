from .customers import router as customers_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .loans import router as loans_router
from .products import router as products_router
from .conversations import router as conversations_router
from .chat import router as chat_router
from .health import router as health_router
from .policies import router as policies_router

__all__ = [
    "customers_router",
    "accounts_router",
    "transactions_router",
    "loans_router",
    "products_router",
    "conversations_router",
    "chat_router",
    "health_router",
    "policies_router",
]

