from pydantic import BaseModel

class SymptomsCreate(BaseModel):
    sin_nome: str

class SymptomsBase(BaseModel):
    sin_id: int
    sin_nome: str

    class Config:
        orm_mode = True

class SymptomsInBD(SymptomsBase):
    pass
