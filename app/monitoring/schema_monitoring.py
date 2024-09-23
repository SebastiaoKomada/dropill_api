from pydantic import BaseModel
from datetime import datetime

class MonitoringBase(BaseModel):
    mon_dataHorario: datetime

class MonitoringEdit(MonitoringBase):
    mon_sintomasId: int
    mon_perfilId: int

    class Config:
        orm_mode = True

class MonitoringWithSymptom(MonitoringBase):
    # Inclui o nome do sintoma associado
    symptom_name: str

    class Config:
        orm_mode = True
