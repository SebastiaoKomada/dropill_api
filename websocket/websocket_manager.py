import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
import websockets
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Armazena a conexão WebSocket globalmente
websocket_connection = None

async def websocket_endpoint(websocket: WebSocket):
    global websocket_connection
    await websocket.accept()
    logger.info("WebSocket conexão aceita")
    
    websocket_connection = websocket  # Armazena a conexão aberta

    try:
        while True:
            data = await websocket.receive_text()  # Aguarda uma mensagem
            logger.info(f"Mensagem recebida: {data}")
            # Processar a mensagem recebida
            # Você pode enviar uma resposta de volta se necessário
            response = {"message": "Mensagem recebida com sucesso"}
            await websocket.send_json(response)
    
    except WebSocketDisconnect:
        logger.info("WebSocket desconectado")
        websocket_connection = None  # Limpa a conexão ao desconectar
    
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")

    # Não feche a conexão aqui para que o WebSocket permaneça aberto enquanto necessário


async def send_websocket_notification(data_payload: Dict):
    global websocket_connection
    if websocket_connection:
        try:
            # Verifica se data_payload é um dict e converte para JSON
            if isinstance(data_payload, dict):
                message = json.dumps(data_payload)
            else:
                logger.error(f"Payload inválido: {data_payload}. Esperado dict.")
                return

            await websocket_connection.send_text(message)
            logger.info(f"Mensagem enviada: {message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem pelo WebSocket: {e}")
    else:
        logger.warning("Nenhuma conexão WebSocket disponível para enviar a mensagem")
