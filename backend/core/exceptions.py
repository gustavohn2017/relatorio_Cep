"""
core/exceptions.py — Handler global de exceções para garantir que
todos os erros retornem JSON, nunca HTML.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Exceções não tratadas pelo DRF — retorna JSON em vez de HTML
    logger.exception("Erro não tratado: %s", exc)
    return Response(
        {"detail": "Erro interno do servidor. Tente novamente."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
