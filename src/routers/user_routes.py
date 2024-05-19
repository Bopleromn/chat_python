from random import randint
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..helpers import send_email
from ..request_models import UserBase as UserReqModel
from ..table_models import Users as UsersTable
from ..table_models import VerificationCodes as VerificationCodesTable
from ..routers import chat_routes
import status
from datetime import datetime


router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.get('')
async def handle_user_get(email: str, password: str, db: Session=Depends(get_db)):
    user = db.query(UsersTable).filter(UsersTable.email == email).filter(UsersTable.password == password).first()
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='user not found')
        
    await hanlde_post_last_seen(user_id=user.id, is_active=True, db=db)
    db.refresh(user)
         
    return {'data': user}


@router.get('/all')
async def handle_all_users_get(db: Session=Depends(get_db)):
    users = db.query(UsersTable).all()

    return {'data': [{'id': user.id, 'email': user.email, 'name': user.name, 'age': user.age, 'photo': user.photo, 'last_seen': user.last_seen} for user in users]}
    
    
@router.post('')
async def handle_user_post(user: UserReqModel, db: Session=Depends(get_db)):
    new_user = UsersTable(**user.model_dump())
    new_user.last_seen = ''
    new_user.name = '@' + new_user.name
    
    db.add(new_user)
    
    try:
        db.commit()
        db.refresh(new_user)
        
        return {'data': new_user}
    except Exception as e:
        raise HTTPException(
            status_code=409,
            detail=e
        )
    
    
@router.put('')
async def hande_user_put(email: str, password: str, new_user: UserReqModel, db: Session=Depends(get_db)):
    query = db.query(UsersTable).filter(UsersTable.email == email).filter(UsersTable.password == password)
    
    old_user = query.first()
    
    if old_user is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='user not found')
    
    query.update(values=new_user.model_dump(), synchronize_session=False)
    
    try:
        db.commit()
        
        updated_user = db.query(UsersTable).filter(UsersTable.email == new_user.email).filter(UsersTable.password == new_user.password).first()
        
        return {'data': updated_user}
    except:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, 
                            detail='could not update user')
    
    
@router.delete('')
async def handle_user_delete(email: str, password: str, db: Session=Depends(get_db)):
    user = db.query(UsersTable).filter(UsersTable.email == email).filter(UsersTable.password == password).first()
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='user not found')
    
    db.delete(user)
    db.commit()
    
    
@router.get('/verification_codes/send')
async def handle_verification_code_send(email: str, is_registration: bool, db: Session = Depends(get_db)):
    if not is_registration and db.query(UsersTable).filter(UsersTable.email == email).first() is None:
        raise HTTPException(
            status_code=404,
            detail='no such user'
        )
    
    current_code: int = randint(100000, 999999)
    
    recipient_info = dict(
        verification_code=current_code,
        email=email
    )
    
    try:
        await send_email(email, f"Здравствуйте, {email}. Ваш код подтверждения пришел", f"Код: {current_code}")
    except:
        raise HTTPException(
            status_code=400,
            detail='invalid email address'
        )

    query = db.query(VerificationCodesTable).filter(
        VerificationCodesTable.email == email
    )

    old_recipient_info = query.first()

    if old_recipient_info is None:
        new_recipient_info = VerificationCodesTable(**recipient_info)

        db.add(new_recipient_info)
        db.commit()

        db.refresh(new_recipient_info)

        return dict(
            data=new_recipient_info
        )

    else:

        query.update(recipient_info, synchronize_session=False)

        try:
            db.commit()

            return dict(
                data=recipient_info
            )

        except:
            raise HTTPException(
                status_code=304,
                detail='can\'t update vc'
            )
            

@router.get('/verification_codes/check')
async def handle_verification_code_check(email: str, verification_code: str, db: Session = Depends(get_db)):
    result = db.query(VerificationCodesTable).filter(VerificationCodesTable.email == email).filter(VerificationCodesTable.verification_code == verification_code).first()
    
    if result is None:
        raise HTTPException(
            status_code=409,
            detail='incorrect verification code'
        )
        
        
@router.get('/reset_password')
async def handle_reset_password(email: str, new_password: str, verification_code: str, db: Session = Depends(get_db)):
    await handle_verification_code_check(email, verification_code, db)

    user = db.query(UsersTable).filter(UsersTable.email == email).first()
    
    if user is None:
        raise HTTPException(
            status_code=404,
            detail='user not found'
        ) 
        
    user.password = new_password
    db.commit()
    
    
@router.post('/activity')
async def hanlde_post_last_seen(user_id: int, is_active: bool, db: Session = Depends(get_db)):
    try:
        user = db.query(UsersTable).filter(UsersTable.id == user_id).first()
        
        if is_active:
            user.last_seen = 'active'
        else:
           user.last_seen = str(datetime.now())
           
        db.commit()
        
        rooms = await chat_routes.handle_rooms_get(user_id=user.id, db=db)
        
        for room in rooms['data']:
            await chat_routes.broadcast_message(room_id=room['room_id'], message=f'__user_status_updated_{user_id}__')
    except:
        raise HTTPException(
            status_code=404,
            detail='user not found'
        )
        
    
@router.get('/activity')
async def hanlde_get_last_seen(user_id: int, db: Session = Depends(get_db)):
    try:
        return {'data': db.query(UsersTable).filter(UsersTable.id == user_id).first().last_seen}
    except:
        raise HTTPException(
            status_code=404,
            detail='user not found'
        )
        