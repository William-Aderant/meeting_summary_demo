"""Job storage module to avoid circular imports."""
from typing import Dict, Any

# Local storage for job metadata (SQLite would be better for production)
# This is a simple in-memory dictionary. In production, use a proper database.
jobs_db: Dict[str, Dict[str, Any]] = {}



