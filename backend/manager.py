from fastapi.websockets import WebSocket

class WebSocketManager:
    
    def __init__(self):
        self.connected_clients = {}


    async def connect(self,websocket:WebSocket, username: str):
            #client connected
            await websocket.accept()

            #add client to list of connected clients
            self.connected_clients[websocket] = username
            print(f"connected clients: {self.connected_clients}")


    async def send_message(self, websocket: WebSocket, message: dict, sender: str):
          print(f"message: {message}")
          message = {
            "client": sender,
            "message": message['content'],
            }

          await websocket.send_json(message)

    async def disconnect(self,websocket):
            username = self.connected_clients[websocket]
            print(f"client {username} disconnected")
            del self.connected_clients[websocket]
            
            print(f"connected clients: {self.connected_clients}")