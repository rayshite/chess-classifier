from fastapi import FastAPI, UploadFile, File, HTTPException

from board_service import process_board_image
from classifier import predict_all_squares

app = FastAPI()


@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    """
    Принимает изображение шахматной доски и возвращает предсказания.
    """
    contents = await image.read()

    try:
        squares = process_board_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Классификация каждой клетки
    predictions = predict_all_squares(squares)

    return {
        "predictions": predictions
    }