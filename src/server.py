import uvicorn
from fastapi import FastAPI

from routers.user_routes import router as users_router
from routers.chat_routes import router as chats_router


class Server:
    def __init__(self, ip: str, port: int):
        self.__ip = ip
        self.__port = port
        self.app = FastAPI(debug=True, title="SPARKS")

    def init_routes(self):
        self.app.include_router(users_router)
        self.app.include_router(chats_router)
        
    def run(self):
        uvicorn.run(
            self.app, host=self.__ip, port=self.__port
        )