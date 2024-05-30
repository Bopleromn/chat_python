import os
import shutil
from fastapi import APIRouter, HTTPException, File, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse


router = APIRouter(
    prefix='/images',
    tags=['Images']
)


@router.post('')
async def add_image(name: str, file: UploadFile = File(...)):
    try:
        name = f'../images/{name}'
        with open(name, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(
            status_code=200,
            content=dict(
                detail=f'image {file.filename} succesfully added'
            )
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=404,
            detail=f'can\'t save image, error {e}'
        )


@router.get('', response_class=FileResponse)
async def get_image(name: str):
    if (os.path.exists('../images/' + name)):
        return '../images/' + name

    raise HTTPException(
        status_code=404,
        detail='image not found'
    )
