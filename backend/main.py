from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from board_service import process_board_image
from classifier import predict_all_squares

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_name": "Иван Петров"
    })

@app.get("/games/{game_id}")
async def game_page(request: Request, game_id: int):
    return templates.TemplateResponse("game.html", {
        "request": request,
        "user_name": "Иван Петров"
    })

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