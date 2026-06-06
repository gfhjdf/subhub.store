"""Audit service — log all important actions for traceability."""
import json
from src.database.connection import get_db


async def log_action(actor_type: str, action: str,
                     entity_type: str | None = None, entity_id: int | None = None,
                     meta: dict | None = None, admin_id: int | None = None) -> None:
    """Log an auditable action.
    
    Args:
        actor_type: 'admin', 'system', or 'user'
        action: e.g., 'order_approved', 'account_added', 'settings_updated'
        entity_type: e.g., 'order', 'account', 'platform', 'plan', 'user'
        entity_id: ID of the affected entity
        meta: Additional metadata as dict
        admin_id: Admin user ID if actor is admin
    """
    db = await get_db()
    meta_json = json.dumps(meta) if meta else None
    await db.execute(
        """INSERT INTO audit_logs (admin_user_id, actor_type, action, entity_type, entity_id, meta_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (admin_id, actor_type, action, entity_type, entity_id, meta_json)
    )
    await db.commit()


async def get_audit_logs(limit: int = 100, offset: int = 0,
                         entity_type: str | None = None,
                         action: str | None = None) -> list[dict]:
    """Get audit logs for admin panel."""
    db = await get_db()
    conditions = []
    params = []
    if entity_type:
        conditions.append("entity_type = ?")
        params.append(entity_type)
    if action:
        conditions.append("action = ?")
        params.append(action)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await db.execute_fetchall(
        f"""SELECT al.*, au.username as admin_username
            FROM audit_logs al
            LEFT JOIN admin_users au ON al.admin_user_id = au.id
            {where}
            ORDER BY al.created_at DESC LIMIT ? OFFSET ?""",
        params + [limit, offset]
    )
    return [dict(r) for r in rows]
