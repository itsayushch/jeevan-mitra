from app.core.logging import (
    setup_logger,
    redact_text,
    redact_data,
    request_id_ctx_var,
    RedactingJsonFormatter,
    RedactingConsoleFormatter,
)

logger = setup_logger()
