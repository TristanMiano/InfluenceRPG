# src/server/account.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from src.server.main import templates
from src.db.user_db import verify_user_password, update_password

router = APIRouter()


@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, error: str | None = None, message: str | None = None):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "account.html",
        {"request": request, "error": error, "message": message},
    )


@router.post("/account/change_password", response_class=HTMLResponse)
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password2: str = Form(...),
):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)

    if new_password != new_password2:
        return templates.TemplateResponse(
            "account.html",
            {"request": request, "error": "Passwords do not match."},
            status_code=400,
        )

    if not verify_user_password(username, current_password):
        return templates.TemplateResponse(
            "account.html",
            {"request": request, "error": "Current password is incorrect."},
            status_code=400,
        )

    update_password(username, new_password)

    return templates.TemplateResponse(
        "account.html",
        {"request": request, "message": "Password updated."},
    )