from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClientProfile, DriverProfile, RequestStatus, SessionToken, TransportRequest, User, UserRole


def _hash_password(password: str) -> str:
    return f"hash::{password}"


def seed_database(db: Session) -> None:
    client = db.scalar(select(User).where(User.email == "cliente.teste@levaleve.com"))
    if not client:
        client = User(
            role=UserRole.client,
            name="Cliente Teste",
            email="cliente.teste@levaleve.com",
            phone="(11) 90000-0001",
            password_hash=_hash_password("Cliente123!"),
            avatar_url=None,
        )
        client.client_profile = ClientProfile(
            street="Rua das Flores",
            number="123",
            complement="Apto 42",
            neighborhood="Vila Mariana",
            city="Sao Paulo",
            state="SP",
            zip_code="04000-000",
            has_elevator=True,
            floor="3",
        )
        db.add(client)

    driver = db.scalar(select(User).where(User.email == "motorista.teste@levaleve.com"))
    if not driver:
        driver = User(
            role=UserRole.driver,
            name="Carlos Silva",
            email="motorista.teste@levaleve.com",
            phone="(11) 98888-0002",
            password_hash=_hash_password("Motorista123!"),
            avatar_url=None,
        )
        driver.driver_profile = DriverProfile(
            cpf="123.456.789-00",
            cnh="12345678901",
            vehicle_name="Fiat Fiorino",
            vehicle_plate="ABC-1234",
            vehicle_type="Van cargo",
            capacity_kg=650,
            rating=4.9,
            trips_completed=2847,
            available_balance=3254.80,
        )
        db.add(driver)

    request_exists = db.scalar(select(TransportRequest).where(TransportRequest.title == "Sofa de 3 lugares"))
    if not request_exists:
        db.add(
            TransportRequest(
                status=RequestStatus.available,
                title="Sofa de 3 lugares",
                client_name="Joao M.",
                client_since="Cliente desde 2024",
                category="Moveis",
                pickup_address="Rua das Flores, 123 - Vila Mariana, Sao Paulo - SP",
                dropoff_address="Av. Paulista, 1500 - Bela Vista, Sao Paulo - SP",
                distance_km=8.5,
                eta_minutes=40,
                price=89.90,
                helper_required=True,
                item_description="Sofa de 3 lugares, 100x80x90 cm, ajudante incluso",
            )
        )

    db.commit()


def create_session(db: Session, user_id: str) -> str:
    token = f"session::{user_id}::{datetime.now(timezone.utc).timestamp()}"
    db.add(SessionToken(token=token, user_id=user_id, expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    db.commit()
    return token
