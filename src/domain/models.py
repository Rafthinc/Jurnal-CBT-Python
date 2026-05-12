from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class CBTEntry:
    situatie: str
    ganduri: str
    veridicitate_ganduri: int
    emotii: List[str]
    intensitate_emotie: int
    comportament: str
    data_creare: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y %H:%M:%S"))