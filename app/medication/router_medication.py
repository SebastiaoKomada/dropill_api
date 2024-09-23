from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud_medication, schema_medication
from app.db.database import SessionLocal

routerMedication = APIRouter(
    prefix="/medication",
    tags=["medication"],
    responses={404: {"description": "Not found"}},
)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@routerMedication.post("/{per_id}", response_model=schema_medication.MedicationInDB)
def create_medication(
    per_id: int,
    medication: schema_medication.MedicationBase,
    db: Session = Depends(get_db_session),
):
    return crud_medication.create_medication(db=db, medication=medication, per_id=per_id)

@routerMedication.get("/{med_id}", response_model=schema_medication.MedicationReturn)
def get_medication(
    med_id: int,
    db: Session = Depends(get_db_session),
):
    db_medication = crud_medication.get_medication(db=db, med_id=med_id)
    
    if not db_medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    return db_medication

@routerMedication.get("/profile/{per_id}", response_model=List[schema_medication.MedicationInDB])
def get_medication_perId(
    per_id: int,
    db: Session = Depends(get_db_session),
):
    db_medications = crud_medication.get_medication_perId(db=db, perId=per_id)
    if not db_medications:
        raise HTTPException(status_code=404, detail="No medications found for this profile")
    return db_medications

@routerMedication.delete("/{med_id}", response_model=dict)
def delete_medication(
    med_id: int,
    db: Session = Depends(get_db_session),
):
    return crud_medication.delete_medication(db=db, med_id=med_id)