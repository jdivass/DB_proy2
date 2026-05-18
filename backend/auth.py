
import uuid
from functools import wraps
from fastapi import HTTPException, Cookie
from dbConnection import db_connection

#User id, username y rol
_sessions: dict[str, dict] = {}


def create_session(user: dict) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "id_usuario": user["id_usuario"],
        "username":   user["username"],
        "rol":        user["rol"],
    }
    return session_id


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)

def get_current_user(session_id: str | None = Cookie(default=None)) -> dict:
    if not session_id:
        raise HTTPException(status_code=401, detail="No autenticado")

    user = get_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    return user


def require_roles(*roles: str):

    def dependency(session_id: str | None = Cookie(default=None)) -> dict:
        user = get_current_user(session_id)
        if user["rol"] not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Se requiere uno de los roles: {list(roles)}"
            )
        return user
    return dependency

# Autenticar usuarios de la db
def authenticate_user(username: str, password: str) -> dict | None:
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id_usuario, username, rol
            FROM app_usuario
            WHERE username = %s
              AND password = %s
              AND activo = TRUE;
            """,
            (username, password)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"id_usuario": row[0], "username": row[1], "rol": row[2]}
    finally:
        cursor.close()
        conn.close()