from pydantic import BaseModel
from datetime import datetime

class HistoryQuery(BaseModel):
    query: str
    category: str
    timestamp: datetime
    clustered: bool = False
    