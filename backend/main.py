from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from board_service import process_board_image
from classifier import predict_all_squares

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def home():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/games/{game_id}")
async def game_page(game_id: int):
    return FileResponse(FRONTEND_DIR / "game.html")

@app.post("/api/predict")
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