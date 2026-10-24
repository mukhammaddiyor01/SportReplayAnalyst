from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from backend.config import TEMPLATE_DIRECTORY

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIRECTORY)


@router.get("/")
def workspace(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.get("/health")
def health():
    return {"status": "ok"}
