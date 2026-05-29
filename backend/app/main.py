from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import ClientProfile, DriverProfile, Notification, RequestStatus, SessionToken, TransportRequest, User, UserRole
from app.schemas import (
    ClientAddressIn,
    ClientAddressOut,
    ClientTransportRequestIn,
    ClientRegisterIn,
    ClientTripDetailOut,
    ClientTripOut,
    DriverAcceptOut,
    DriverDashboardOut,
    DriverProfileIn,
    DriverProfileOut,
    DriverRegisterIn,
    DriverRequestOut,
    LoginRequest,
    NotificationOut,
    SimpleMessage,
    TokenResponse,
)
from app.seed import create_session, seed_database

app = FastAPI(title="Leva Leve API", version="0.1.0")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_origins == "*" else [origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return f"hash::{password}"


def verify_password(password: str, password_hash: str) -> bool:
    return password_hash == hash_password(password)


def user_to_payload(user: User) -> dict:
    return {
        "id": user.id,
        "role": user.role.value,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
    }


def client_profile_payload(profile: ClientProfile) -> dict:
    return {
        "street": profile.street,
        "number": profile.number,
        "complement": profile.complement,
        "neighborhood": profile.neighborhood,
        "city": profile.city,
        "state": profile.state,
        "zip_code": profile.zip_code,
        "has_elevator": profile.has_elevator,
        "floor": profile.floor,
    }


def driver_profile_payload(user: User, profile: DriverProfile) -> dict:
    return {
        "name": user.name,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "cpf": profile.cpf,
        "cnh": profile.cnh,
        "vehicle_name": profile.vehicle_name,
        "vehicle_plate": profile.vehicle_plate,
        "vehicle_type": profile.vehicle_type,
        "capacity_kg": profile.capacity_kg,
        "rating": profile.rating,
        "trips_completed": profile.trips_completed,
        "available_balance": profile.available_balance,
    }


def request_payload(request: TransportRequest, accepted_driver_name: str | None = None) -> dict:
    payload = {
        "id": request.id,
        "title": request.title,
        "client_name": request.client_name,
        "client_since": request.client_since,
        "category": request.category,
        "pickup_address": request.pickup_address,
        "dropoff_address": request.dropoff_address,
        "distance_km": request.distance_km,
        "eta_minutes": request.eta_minutes,
        "price": request.price,
        "helper_required": request.helper_required,
        "item_description": request.item_description,
        "status": request.status.value,
    }
    if accepted_driver_name is not None:
        payload["accepted_driver_name"] = accepted_driver_name
    return payload


def notification_payload(notification: Notification | None) -> dict | None:
    if notification is None:
        return None

    created_at = notification.created_at
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return {
        "id": notification.id,
        "kind": notification.kind,
        "title": notification.title,
        "message": notification.message,
        "request_id": notification.request_id,
        "created_at": created_at.isoformat() if created_at else "",
    }


def completed_requests_for_driver(db: Session, driver_id: str) -> list[TransportRequest]:
    return db.scalars(
        select(TransportRequest)
        .where(TransportRequest.status == RequestStatus.completed)
        .where(TransportRequest.accepted_driver_id == driver_id)
        .order_by(TransportRequest.completed_at.desc().nullslast(), TransportRequest.created_at.desc())
    ).all()


def normalize_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def completed_today_for_driver(db: Session, driver_id: str) -> list[TransportRequest]:
    now = datetime.now(timezone.utc)
    today = now.date()
    requests = completed_requests_for_driver(db, driver_id)
    return [item for item in requests if normalize_utc(item.completed_at) and normalize_utc(item.completed_at).date() == today]


def completed_this_week_for_driver(db: Session, driver_id: str) -> list[TransportRequest]:
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=now.weekday())
    requests = completed_requests_for_driver(db, driver_id)
    return [item for item in requests if normalize_utc(item.completed_at) and normalize_utc(item.completed_at) >= start_of_week]


def get_current_user(authorization: str | None, db: Session) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")

    token = authorization.removeprefix("Bearer ").strip()
    session = db.get(SessionToken, token)
    expires_at = session.expires_at if session else None
    if expires_at is not None:
        expires_at = normalize_utc(expires_at)
    if not session or not expires_at or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao expirada")

    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado")
    return user


def ensure_transport_request_completed_at_column() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(transport_requests)")}
        if "completed_at" not in columns:
            connection.exec_driver_sql("ALTER TABLE transport_requests ADD COLUMN completed_at DATETIME")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_transport_request_completed_at_column()
    with SessionLocal() as db:
        seed_database(db)


app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
app.mount("/pages", StaticFiles(directory=str(FRONTEND_DIR / "pages")), name="pages")


@app.get("/", include_in_schema=False)
def frontend_index() -> HTMLResponse:
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html")


@app.get("/index.html", include_in_schema=False)
def frontend_index_alias() -> HTMLResponse:
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html")


@app.get("/favicon.ico", include_in_schema=False)
def frontend_favicon() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "assets" / "brand-icon.svg", media_type="image/svg+xml")


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health", response_model=SimpleMessage)
def health() -> dict[str, str]:
    return {"detail": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")

    if payload.role and user.role.value != payload.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil incorreto")

    token = create_session(db, user.id)
    return {"token": token, "user": user_to_payload(user)}


@app.post("/auth/register/client", response_model=TokenResponse)
def register_client(payload: ClientRegisterIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail ja cadastrado")

    user = User(
        role=UserRole.client,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    user.client_profile = ClientProfile(**payload.address.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user.id)
    return {"token": token, "user": user_to_payload(user)}


@app.post("/auth/register/driver", response_model=TokenResponse)
def register_driver(payload: DriverRegisterIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail ja cadastrado")

    user = User(
        role=UserRole.driver,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        avatar_url=payload.avatar_url,
    )
    user.driver_profile = DriverProfile(
        cpf=payload.cpf,
        cnh=payload.cnh,
        vehicle_name=payload.vehicle_name,
        vehicle_plate=payload.vehicle_plate,
        vehicle_type=payload.vehicle_type,
        capacity_kg=payload.capacity_kg,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user.id)
    return {"token": token, "user": user_to_payload(user)}


@app.get("/me")
def me(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    payload = user_to_payload(user)
    payload["role"] = user.role.value
    if user.role == UserRole.client and user.client_profile:
        payload["address"] = client_profile_payload(user.client_profile)
    if user.role == UserRole.driver and user.driver_profile:
        payload["driver_profile"] = driver_profile_payload(user, user.driver_profile)
    return payload


@app.get("/client/address/me", response_model=ClientAddressOut)
def get_client_address(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client or not user.client_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")
    return client_profile_payload(user.client_profile)


@app.put("/client/address/me", response_model=ClientAddressOut)
def update_client_address(payload: ClientAddressIn, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")

    if not user.client_profile:
        user.client_profile = ClientProfile(**payload.model_dump())
    else:
        for key, value in payload.model_dump().items():
            setattr(user.client_profile, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return client_profile_payload(user.client_profile)


@app.post("/client/requests", response_model=DriverRequestOut)
def create_client_request(payload: ClientTransportRequestIn, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")
    if not user.client_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endereco do cliente nao cadastrado")

    pickup_parts = [user.client_profile.street, user.client_profile.number]
    pickup_address = f"{pickup_parts[0]}, {pickup_parts[1]}"
    pickup_extra_parts = [user.client_profile.neighborhood, user.client_profile.city, user.client_profile.state]
    if user.client_profile.complement:
        pickup_extra_parts.insert(1, user.client_profile.complement)
    if user.client_profile.floor:
        pickup_extra_parts.append(f"{user.client_profile.floor} andar")

    dropoff_parts = [payload.dropoff_address]
    dropoff_extra_parts = []
    if payload.dropoff_complement:
        dropoff_extra_parts.append(payload.dropoff_complement)
    if payload.dropoff_floor:
        dropoff_extra_parts.append(f"{payload.dropoff_floor} andar")

    transport_request = TransportRequest(
        status=RequestStatus.available,
        title=payload.title,
        client_name=user.name,
        client_since=f"Cliente desde {user.created_at.year}" if user.created_at else "Cliente verificado",
        category=payload.category,
        pickup_address=f"{pickup_address} - {', '.join(pickup_extra_parts)}",
        dropoff_address=f"{dropoff_parts[0]} - {', '.join(dropoff_extra_parts)}" if dropoff_extra_parts else dropoff_parts[0],
        distance_km=payload.distance_km,
        eta_minutes=payload.eta_minutes,
        price=payload.price,
        helper_required=payload.helper_required,
        item_description=payload.item_description,
    )
    db.add(transport_request)
    db.commit()
    db.refresh(transport_request)
    return request_payload(transport_request)


@app.get("/client/requests/me", response_model=list[ClientTripOut])
def list_client_requests_me(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")

    requests = db.scalars(
        select(TransportRequest)
        .where(TransportRequest.client_name == user.name)
        .order_by(TransportRequest.created_at.desc())
    ).all()

    return [
        request_payload(item)
        for item in requests
    ]


@app.get("/client/requests/{request_id}", response_model=ClientTripDetailOut)
def get_client_request(request_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")

    request = db.get(TransportRequest, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    if request.client_name != user.name:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode ver esta solicitacao")

    accepted_driver_name = None
    if request.accepted_driver_id:
        driver = db.get(User, request.accepted_driver_id)
        accepted_driver_name = driver.name if driver else None

    return request_payload(request, accepted_driver_name=accepted_driver_name)


@app.post("/client/requests/{request_id}/cancel", response_model=ClientTripOut)
def cancel_client_request(request_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")

    request = db.get(TransportRequest, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")

    if request.client_name != user.name:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode cancelar esta solicitacao")

    request.status = RequestStatus.canceled
    db.add(request)
    db.commit()
    db.refresh(request)

    return request_payload(request)


@app.get("/client/notifications/me")
def list_client_notifications_me(
    request_id: str | None = None,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = get_current_user(authorization, db)
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para cliente")

    notifications_query = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    if request_id:
        notifications_query = notifications_query.where(Notification.request_id == request_id)

    notifications = db.scalars(notifications_query).all()
    return {"items": [notification_payload(item) for item in notifications]}


@app.post("/driver/requests/{request_id}/accept", response_model=DriverAcceptOut)
def accept_driver_request(request_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")

    request = db.get(TransportRequest, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    if request.status != RequestStatus.available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta solicitacao nao esta mais disponivel")

    request.status = RequestStatus.accepted
    request.accepted_driver_id = user.id

    client_user = db.scalar(select(User).where(User.role == UserRole.client, User.name == request.client_name))
    notification = None
    if client_user:
        notification = Notification(
            user_id=client_user.id,
            kind="ride_accepted",
            title="Corrida aceita",
            message=f"{user.name} aceitou sua corrida {request.title}.",
            request_id=request.id,
        )
        db.add(notification)

    db.add(request)
    db.commit()
    db.refresh(request)
    if notification is not None:
        db.refresh(notification)

    return {
        "request": request_payload(request, accepted_driver_name=user.name),
        "notification": notification_payload(notification),
    }


@app.post("/driver/requests/{request_id}/complete", response_model=DriverAcceptOut)
def complete_driver_request(request_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver or not user.driver_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")

    request = db.get(TransportRequest, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    if request.status != RequestStatus.accepted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A corrida precisa estar em andamento para ser concluida")
    if request.accepted_driver_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode concluir esta solicitacao")

    request.status = RequestStatus.completed
    request.completed_at = datetime.now(timezone.utc)
    user.driver_profile.available_balance += request.price
    user.driver_profile.trips_completed += 1

    client_user = db.scalar(select(User).where(User.role == UserRole.client, User.name == request.client_name))
    notification = None
    if client_user:
        notification = Notification(
            user_id=client_user.id,
            kind="ride_completed",
            title="Corrida concluida",
            message=f"Sua corrida {request.title} foi concluida com sucesso.",
            request_id=request.id,
        )
        db.add(notification)

    db.add(request)
    db.add(user.driver_profile)
    db.commit()
    db.refresh(request)
    db.refresh(user.driver_profile)
    if notification is not None:
        db.refresh(notification)

    return {
        "request": request_payload(request, accepted_driver_name=user.name),
        "notification": notification_payload(notification),
    }


@app.get("/driver/profile/me", response_model=DriverProfileOut)
def get_driver_profile(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver or not user.driver_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")
    return driver_profile_payload(user, user.driver_profile)


@app.put("/driver/profile/me", response_model=DriverProfileOut)
def update_driver_profile(payload: DriverProfileIn, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver or not user.driver_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")

    if payload.name is not None:
        user.name = payload.name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url

    for key in ["cpf", "cnh", "vehicle_name", "vehicle_plate", "vehicle_type", "capacity_kg"]:
        value = getattr(payload, key)
        if value is not None:
            setattr(user.driver_profile, key, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return driver_profile_payload(user, user.driver_profile)


@app.get("/driver/requests")
def list_driver_requests(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")

    requests = db.scalars(select(TransportRequest).where(TransportRequest.status == RequestStatus.available)).all()
    return {
        "items": [
            {
                "id": request.id,
                "title": request.title,
                "client_name": request.client_name,
                "client_since": request.client_since,
                "category": request.category,
                "pickup_address": request.pickup_address,
                "dropoff_address": request.dropoff_address,
                "distance_km": request.distance_km,
                "eta_minutes": request.eta_minutes,
                "price": request.price,
                "helper_required": request.helper_required,
                "item_description": request.item_description,
            }
            for request in requests
        ]
    }


@app.get("/driver/requests/{request_id}")
def get_driver_request(request_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")

    request = db.get(TransportRequest, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")

    return {
        "id": request.id,
        "title": request.title,
        "client_name": request.client_name,
        "client_since": request.client_since,
        "category": request.category,
        "pickup_address": request.pickup_address,
        "dropoff_address": request.dropoff_address,
        "distance_km": request.distance_km,
        "eta_minutes": request.eta_minutes,
        "price": request.price,
        "helper_required": request.helper_required,
        "item_description": request.item_description,
    }


@app.get("/driver/dashboard/me", response_model=DriverDashboardOut)
def driver_dashboard(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    if user.role != UserRole.driver or not user.driver_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso permitido apenas para motorista")

    active_requests = db.scalars(select(TransportRequest).where(TransportRequest.status == RequestStatus.available)).all()
    completed_today = completed_today_for_driver(db, user.id)
    completed_week = completed_this_week_for_driver(db, user.id)
    today_earnings = sum(item.price for item in completed_today)
    today_trips = len(completed_today)
    weekly_average = (sum(item.price for item in completed_week) / len(completed_week)) if completed_week else 0.0
    return {
        "total_balance": user.driver_profile.available_balance,
        "today_earnings": today_earnings,
        "today_trips": today_trips,
        "weekly_average": weekly_average,
        "active_requests": [
            {
                "id": item.id,
                "title": item.title,
                "category": item.category,
                "pickup_address": item.pickup_address,
                "dropoff_address": item.dropoff_address,
                "distance_km": item.distance_km,
                "eta_minutes": item.eta_minutes,
                "price": item.price,
                "helper_required": item.helper_required,
                "item_description": item.item_description,
            }
            for item in active_requests
        ],
        "history": [],
        "stats": {
            "acceptance_rate": 0 if not active_requests and today_trips == 0 else 94,
            "completion_rate": 0 if today_trips == 0 else 98,
            "rating": user.driver_profile.rating,
            "week_trips": len(completed_week),
            "week_hours": 0 if not completed_week else round(len(completed_week) * 1.0, 2),
            "week_km": round(sum(item.distance_km for item in completed_week), 1),
            "hour_average": weekly_average,
        },
    }
