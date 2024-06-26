from fastapi import Depends,  WebSocket, WebSocketDisconnect, APIRouter, HTTPException, status
from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import text, and_, desc

from request_models import ListOfIds as ListOfIdsReqModel
from table_models import ChatMessages as ChatMessagesTable
from table_models import ChatRooms as ChatRoomsTable
from table_models import Users as Users
from db import get_db


router = APIRouter(
    prefix='/chats',
    tags=['Chats']
)


@router.post('/rooms')
async def handle_get_or_create_room(ids: ListOfIdsReqModel, db: Session = Depends(get_db)):
    if len(ids.data) == 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='room must contain at least 2 users')

    result = db.execute(text(f"SELECT DISTINCT room_id FROM chat_rooms")).all()

    if result:
        for room_id in result:
            user_ids = db.execute(text(
                f"SELECT DISTINCT user_id FROM chat_rooms WHERE room_id = {room_id[0]}")).all()

            do_continue: bool = True

            for user_id in user_ids:
                if len(user_ids) != len(ids.data) or user_id[0] not in ids.data:
                    do_continue = False
                    break

            if do_continue:
                return {'data': {'room_id': room_id[0]}}

        result_id: int = db.query(ChatRoomsTable.room_id).order_by(
            ChatRoomsTable.room_id.desc()).first()[0] + 1

        for id in ids.data:
            chat = ChatRoomsTable(room_id=result_id, user_id=id)

            db.add(chat)
            db.commit()

        return {'data': {'room_id': result_id}}
    else:
        for id in ids.data:
            chat = ChatRoomsTable(room_id=1, user_id=id)

            db.add(chat)
            db.commit()

        return {'data': {'room_id': 1}}


# Get messages for the room
@router.get("/rooms/{room_id}")
async def handle_messages_get(room_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessagesTable).filter(
        ChatMessagesTable.room_id == room_id).order_by(ChatMessagesTable.created_at).all()

    return {'data': [{'id': msg.id, 'user_id': msg.user_id, 'message': msg.message, 'created_at': msg.created_at} for msg in messages]}


# Get rooms for user
@router.get("/rooms")
async def handle_rooms_get(user_id: int, db: Session = Depends(get_db)):
    rooms = db.query(ChatRoomsTable).filter(
        ChatRoomsTable.user_id == user_id).all()

    return {'data': [{'room_id': room.room_id, 'last_message': room.last_message, 'user_ids': [other_room.user_id
                                                                                               for other_room in db.query(ChatRoomsTable).filter(
                                                                                                   and_(
                                                                                                       ChatRoomsTable.room_id == room.room_id,
                                                                                                       ChatRoomsTable.user_id != user_id
                                                                                                   ))
                                                                                               ]}
                     for room in set(rooms)
                     if room.last_message is not None and len(room.last_message.strip()) > 0
                     ]}


# Delete messages for the room
@router.delete("/rooms/{room_id}")
async def handle_messages_delete(room_id: int, db: Session = Depends(get_db)):
    try:
        db.query(ChatMessagesTable).where(
            ChatMessagesTable.room_id == room_id).delete()
        db.commit()

        set_last_message(room_id, message='', db=db)

        await broadcast_message(room_id=room_id, message='__messages_cleared__')
    except:
        raise HTTPException(
            status_code=404,
            detail='could not delete messages from the room'
        )


@router.put("/messages/{message_id}")
async def handle_message_put(message_id: int, message: str, db: Session = Depends(get_db)):
    query = db.query(ChatMessagesTable).filter(
        ChatMessagesTable.id == message_id)

    if query.first() is None:
        raise HTTPException(
            status_code=404,
            detail='message not found'
        )

    query.update(values={'message': message}, synchronize_session=False)

    try:
        db.commit()

        updated_message = query.first()

        if updated_message.id == get_last_message(updated_message.room_id, db=db)['data'].id:
            set_last_message(room_id=updated_message.room_id,
                             message=updated_message.message, db=db)

        await broadcast_message(room_id=updated_message.room_id, message=f'__message_updated__{updated_message.id}_{updated_message.message}')

    except:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED,
                            detail='could not update user')


@router.delete("/messages/{message_id}")
async def handle_message_delete(message_id: int, db: Session = Depends(get_db)):
    message = db.query(ChatMessagesTable).filter(
        ChatMessagesTable.id == message_id).first()

    if message is None:
        raise HTTPException(
            status_code=404,
            detail='message not found'
        )

    if message.id == get_last_message(room_id=message.room_id, db=db)['data'].id:
        db.delete(message)
        db.commit()

        try:
            set_last_message(db=db, room_id=message.room_id, message=get_last_message(
                room_id=message.room_id, db=db)['data'].message)
        except:
            set_last_message(db=db, room_id=message.room_id, message='')
    else:
        db.delete(message)
        db.commit()

    await broadcast_message(room_id=message.room_id, message=f'__message_deleted__{message.id}')


# Dictionary to store connected clients and their corresponding rooms
rooms: Dict[int, List[WebSocket]] = {}


# Websocket connection
@router.websocket("/{room_id}/{user_id}")
async def handle_connect_websocket(websocket: WebSocket, room_id: int, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()

    # Add user to the room
    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            id: int = save_message(room_id, user_id, data, db)
            if id:
                await broadcast_message(room_id, '{"id": ' + str(id) + ', "user_id": ' + str(user_id) + ', "message": "' + str(data) + '", "created_at": "' + str(datetime.now()) + '"}')
    except WebSocketDisconnect:
        rooms[room_id].remove(websocket)


async def broadcast_message(room_id: str, message: str):
    if room_id in rooms:
        for client in rooms[room_id]:
            await client.send_text(message)


# Save message to database
def save_message(room_id: str, user_id: int, message: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user_id).first()

    if user is None:
        return 0

    if len(message) != 0:
        data = ChatMessagesTable(
            room_id=room_id, user_id=user_id, message=message, created_at=datetime.now())

        try:
            db.add(data)
            db.commit()

            db.refresh(data)

            set_last_message(room_id, message, db=db)

            return data.id
        except:
            return 0
    else:
        return 0


def set_last_message(room_id: int, message: str, db: Session = Depends(get_db)):
    query = db.query(ChatRoomsTable).filter(ChatRoomsTable.room_id == room_id)

    query.update(values={'last_message': message})

    try:
        db.commit()
    except:
        raise HTTPException(
            status_code=400,
            detail='couldn\'t update last message'
        )


def get_last_message(room_id: int, db: Session = Depends(get_db)):
    message = db.query(ChatMessagesTable).filter(ChatMessagesTable.room_id == room_id).order_by(
        desc(ChatMessagesTable.created_at)
    ).first()

    if message is not None:
        return {'data': message}
