import os
from fastapi import FastAPI
from fastapi.websockets import WebSocketState
from app.db.database import engine
from .profile.router_profile import routerProfile
from .auth.router_auth import routerAuth
from .medication.router_medication import routerMedication
from .time.router_time import routerTime, routerConfirmation
from .monitoring.router_monitoring import routerMonitoring
from .time.crud_time import get_time_by_currentTime
from app.db.database import SessionLocal
import asyncio
from app.config import cache
import logging
from fastapi.responses import HTMLResponse
import firebase_admin
from firebase_admin import credentials

from websocket.websocket_manager import websocket_endpoint, send_websocket_notification

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()

# Configuração a partir das variáveis de ambiente
firebase_config = {
    "type": "service_account",
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n') if os.getenv('FIREBASE_PRIVATE_KEY') else None,
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
}

# Verifica se todas as variáveis necessárias estão definidas
for key, value in firebase_config.items():
    if value is None:
        raise ValueError(f"A variável de ambiente {key} não está definida.")

# Inicializa o Firebase usando o dicionário de configuração
cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)

app = FastAPI()

@app.get('/arduino')
def health_check():
    return True

# Incluindo o endpoint WebSocket
app.websocket("/ws")(websocket_endpoint)

app.include_router(routerProfile)
app.include_router(routerAuth)
app.include_router(routerMedication)
app.include_router(routerTime)
app.include_router(routerConfirmation)
app.include_router(routerMonitoring)

# Função para obter uma sessão do SQLAlchemy
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def periodic_task():
    websocket_url = "ws://172.20.10.11:8000/ws"
    while True:
        # Recupera o global_user_id do cache
        global_user_id = await cache.get("global_user_id")
        
        if global_user_id:
            db = SessionLocal()
            try:
                # Chama a função async usando await e passa o argumento necessário
                time_ids = await get_time_by_currentTime(db, SessionLocal, global_user_id, websocket_url)
                if time_ids:
                    print(f"Horários encontrados: {time_ids}")
                else:
                    print("Nenhum horário corresponde ao horário atual")
            except Exception as e:
                print(f"Erro na periodic_task: {e}")
            finally:
                db.close()  # Fecha a sessão
        else:
            print("Nenhum usuário logado")
        
        await asyncio.sleep(60)  # Espera por 60 segundos antes de repetir
        
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_task())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
