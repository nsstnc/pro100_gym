from pydantic import BaseModel
from typing import Any, Optional, Dict


class StandardResponse(BaseModel):
    status_code: int
    error: Optional[Any] = None
    data: Optional[Any] = None
    path: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
