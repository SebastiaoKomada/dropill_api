import asyncio
import logging
from typing import Dict, List
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from . import schema_time
from ..db.models import Confirmation, Time, Medication, User, Profile
from firebase_admin import messaging
from websocket.websocket_manager import send_websocket_notification  # Importa a função de envio do WebSocket

logger = logging.getLogger(__name__)

def get_time(db: Session, hor_id: int):
    return db.query(Time).filter(Time.hor_id == hor_id).first()

def create_time(db: Session, time: schema_time.TimeBase, med_id: int):
    db_medication = db.query(Medication).filter(Medication.med_id == med_id).first()
    if db_medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    db_time = Time(
        hor_horario=time.hor_horario,
        hor_medicacao=med_id
    )
    db.add(db_time)
    db.commit()
    db.refresh(db_time)
    return db_time

def send_notification(token: str, title: str, body: str, data: dict):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,
        data=data
    )

    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent message: {response}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

async def send_reminder_notification(create_new_db_session, fcm_token: str, websocket_url: str, medication, time_entry, profile_entry, data_payload):
    while True:
        db = create_new_db_session()
        try:
            medication_on_db = db.query(Medication).filter(Medication.med_id == medication.med_id).first()
            profile_on_db = db.query(Profile).filter(Profile.per_id == profile_entry.per_id).first()

            if medication_on_db is None:
                print(f"Medication with med_id {medication.med_id} not found in the database.")
                break

            if profile_on_db is None:
                print(f"profile with per_id {profile_entry.per_id} not found in the database.")
                break


            confirmation = db.query(Confirmation).filter(
                Confirmation.con_perfilId == profile_entry.per_id,
                Confirmation.con_medicacaoId == medication.med_id,
                Confirmation.con_horarioId == time_entry.hor_id
            ).first()

            if confirmation and confirmation.con_confirmado:
                logger.info(f"Confirmation already done for con_id: {confirmation.con_id}")
                break

            # Envio de notificação via FCM
            send_notification(
                token=fcm_token,
                title="Tome o seu medicamento!",
                body=f"Por favor, confirme que você tomou o medicamento {medication.med_nome}, horário: {time_entry.hor_horario.strftime('%H:%M')}",
                data=data_payload
            )

        except Exception as e:
            logger.error(f"Error in reminder notification loop: {e}")
        finally:
            db.close()

        await asyncio.sleep(120)

async def get_time_by_currentTime(db: Session, create_new_db_session, usu_id: int, websocket_url: str):
    user = db.query(Profile).filter(Profile.per_usuId == usu_id).all()
    if not user:
        return []

    matching_times = []
    current_datetime = datetime.now()
    current_time = current_datetime.time().strftime('%H:%M')
    current_date = current_datetime.date()

    for users in user:
        medications = db.query(Medication).filter(Medication.med_perfilId == users.per_id).all()

        for medication in medications:
            medication_date = medication.med_dataFinal

            if current_date > medication_date:
                continue

            times = db.query(Time).filter(Time.hor_medicacao == medication.med_id).all()

            for time_entry in times:
                if time_entry.hor_horario.strftime('%H:%M') == current_time:
                    logger.info(f"Horário encontrado: {time_entry}")
                    profile_entry = db.query(Profile).filter(Profile.per_id == medication.med_perfilId).first()
                    user = db.query(User).filter(User.usu_id == profile_entry.per_usuId).first()
                    fcm_token = user.fcm_token if user else None

                    if fcm_token:
                        try:
                            db_confirmation = Confirmation(
                                con_medicacaoId=medication.med_id,
                                con_horarioId=time_entry.hor_id,
                                con_perfilId=profile_entry.per_id,
                                con_dataHorario=current_datetime,
                                con_confirmado=False
                            )

                            db.add(db_confirmation)
                            db.commit()
                            db.refresh(db_confirmation)

                            data_payload = {
                                'hor_id': str(time_entry.hor_id),
                                'horario': time_entry.hor_horario.strftime('%H:%M'),
                                'perfil_id': str(profile_entry.per_id),
                                'med_id': str(medication.med_id),
                                'med_nome': str(medication.med_nome),
                                'con_id': str(db_confirmation.con_id)
                            }

                            # if medication.med_id:
                            #     send_notification(
                            #         token=fcm_token,
                            #         title="Hora de tomar o medicamento!",
                            #         body=f"É hora de tomar o medicamento {medication.med_nome}.",
                            #         data=data_payload 
                            #     )           
                            # Envio de notificação via WebSocket
                            await send_websocket_notification(data_payload)

                            asyncio.create_task(send_reminder_notification(
                                create_new_db_session, fcm_token, websocket_url, medication, time_entry, profile_entry, data_payload
                            ))

                        except Exception as e:
                            logger.error(f"Error sending notification: {e}")

                    matching_times.append({
                        "hor_id": time_entry.hor_id,
                        "hor_horario": time_entry.hor_horario
                    })

    return matching_times

def confirm_notification(db: Session, con_id: int):
    confirmation = db.query(Confirmation).filter(Confirmation.con_id == con_id).first()
    
    if confirmation and not confirmation.con_confirmado:
        confirmation.con_confirmado = True
        confirmation.con_dataHorarioConfirmacao = datetime.now()
        db.commit()
        db.refresh(confirmation)
        return confirmation       
    else:
        logger.warning("Confirmation not found or already confirmed.")
        return None
