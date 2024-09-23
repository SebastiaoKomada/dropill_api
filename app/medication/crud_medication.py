from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import schema_medication
from datetime import datetime
from ..db.models import Medication, Profile, Time

def get_medication(db: Session, med_id: int) -> schema_medication.MedicationReturn:
    medication = db.query(Medication).filter(Medication.med_id == med_id).first()

    if not medication:
        return None

    times = db.query(Time).filter(Time.hor_medicacao == medication.med_id).all()

    return schema_medication.MedicationReturn(
        med_nome=medication.med_nome,
        med_descricao=medication.med_descricao,
        med_tipo=medication.med_tipo,
        med_quantidade=medication.med_quantidade,
        med_dataInicio=medication.med_dataInicio,
        med_dataFinal=medication.med_dataFinal,
        hor_horario=[time.hor_horario for time in times]
    )

def create_medication(db: Session, medication: schema_medication.MedicationBase, per_id: int):
    db_user = db.query(Profile).filter(Profile.per_id == per_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="profile not found")
    
    db_profile = Medication(
        med_nome=medication.med_nome, 
        med_descricao=medication.med_descricao,
        med_tipo=medication.med_tipo,
        med_quantidade=medication.med_quantidade, 
        med_dataInicio=medication.med_dataInicio,
        med_dataFinal=medication.med_dataFinal,
        med_perfilId=per_id, 
        med_estado=medication.med_estado
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def get_medication_perId(db: Session, perId: int):
    return db.query(Medication).filter(Medication.med_perfilId == perId).all()

def delete_medication(db: Session, med_id: int):
    db_profile = db.query(Medication).filter(Medication.med_id == med_id).first()
    if db_profile:
        db.delete(db_profile)
        db.commit()
        return {"message": "Medication deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Profile not found")