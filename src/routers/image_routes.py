import os
import shutil
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse


router = APIRouter(
    prefix='/image',
    tags=['Images']
)


@router.post('/{image_name}')
async def add_image(image_name: str, file: UploadFile = File(...)):
    try:
        image_name = f'../images/{image_name}'
        with open(image_name, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(
            status_code=200,
            content=dict(
                detail=f'image {file.filename} succesfully added'
            )
        )   
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f'can\'t save image, error {e}'
        )
    

@router.get("/{name_image}", response_class=FileResponse)
async def get_image(name_image: str):
    if (os.path.exists("../images/" + name_image)):
        return "../images/" + name_image
    
    raise HTTPException(
        status_code=404,
        detail='image not found'   
    )