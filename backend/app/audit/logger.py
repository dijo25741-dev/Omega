import logging
from datetime import datetime, UTC
from app.database import async_session_maker
from app.models.audit import AuditLog

logger = logging.getLogger("omega.audit")

async def log_event(
    event: str,
    module: str,
    user: str,
    decision: str,
    reason: str,
    confidence_score: float = 1.0,
    status: str = "SUCCESS"
) -> AuditLog:
    """
    Persists a security or operations audit event asynchronously to the database.
    Prints to standard application logging for real-time console tracing.
    """
    async with async_session_maker() as session:
        try:
            audit = AuditLog(
                timestamp=datetime.now(UTC),
                event=event,
                module=module,
                user=user,
                decision=decision,
                reason=reason,
                confidence_score=confidence_score,
                status=status
            )
            session.add(audit)
            await session.commit()
            await session.refresh(audit)
            
            # Formatted console output
            logger.info(
                f"[AUDIT] Event: {event} | Module: {module} | User: {user} | "
                f"Decision: {decision} | Status: {status} | Reason: {reason}"
            )
            return audit
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
            # Do not raise to prevent breaking primary plant loop operations
            # in case of minor database hiccups during attack simulations.
            return None
