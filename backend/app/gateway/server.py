"""SMTP Gateway server entry point.

Run as: python -m app.gateway.server
"""

import asyncio
import ssl

import structlog
from aiosmtpd.controller import Controller

from app.config import settings
from app.gateway.handler import GuardIAHandler

logger = structlog.get_logger()


def _build_tls_context() -> ssl.SSLContext | None:
    """Build TLS context if certificate paths are configured."""
    if not settings.smtp_tls_cert or not settings.smtp_tls_key:
        if settings.smtp_require_tls:
            logger.warning("tls_required_but_no_certs", msg="TLS required but no certs configured")
        return None

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(settings.smtp_tls_cert, settings.smtp_tls_key)
    logger.info("tls_configured", cert=settings.smtp_tls_cert)
    return ctx


async def start_smtp_server() -> None:
    """Start the Guard-IA SMTP gateway."""
    handler = GuardIAHandler()
    tls_context = _build_tls_context()

    controller = Controller(
        handler,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        tls_context=tls_context,
        ready_timeout=30,
    )

    controller.start()
    logger.info(
        "smtp_gateway_started",
        host=settings.smtp_host,
        port=settings.smtp_port,
        domain=settings.smtp_domain,
        tls=tls_context is not None,
        accepted_domains=settings.accepted_domains_list,
    )

    try:
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("smtp_gateway_stopping")
    finally:
        controller.stop()
        logger.info("smtp_gateway_stopped")


def main() -> None:
    """Entry point for `python -m app.gateway.server`."""
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer(),
        ],
    )
    logger.info("starting_guard_ia_smtp_gateway")
    asyncio.run(start_smtp_server())


if __name__ == "__main__":
    main()
