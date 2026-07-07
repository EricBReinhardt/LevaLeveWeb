from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password, hash_session_token, new_session_token
from app.models import ClientProfile, DriverProfile, RequestStatus, SessionToken, TransportRequest, User, UserRole


def seed_database(db: Session) -> None:
    client = db.scalar(select(User).where(User.email == "cliente.teste@levaleve.com"))
    if not client:
        client = User(
            role=UserRole.client,
            name="Cliente Teste",
            email="cliente.teste@levaleve.com",
            phone="(11) 90000-0001",
            password_hash=hash_password("Cliente123!"),
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
    
    if not client or not client.id:
        db.flush()

    driver = db.scalar(select(User).where(User.email == "motorista.teste@levaleve.com"))
    if not driver:
        driver = User(
            role=UserRole.driver,
            name="Carlos Silva",
            email="motorista.teste@levaleve.com",
            phone="(11) 98888-0002",
            password_hash=hash_password("Motorista123!"),
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
            available_balance=0.0,
        )
        db.add(driver)
    elif driver.driver_profile:
        driver.driver_profile.available_balance = 0.0
        driver.driver_profile.trips_completed = 0
        db.add(driver)
    
    if not driver or not driver.id:
        db.flush()

    db.execute(text("DELETE FROM transport_requests WHERE title = :title"), {"title": "Sofa de 3 lugares"})

    # Create sample completed trips for driver history
    now = datetime.now(timezone.utc)
    for i in range(5):
        existing = db.scalar(
            select(TransportRequest).where(
                TransportRequest.title == f"Mudança - Casa {i+1}"
            )
        )
        if not existing:
            trip = TransportRequest(
                client_id=client.id,
                title=f"Mudança - Casa {i+1}",
                category="Residencial",
                pickup_address=f"Rua A, {100 + i*10}, São Paulo, SP",
                dropoff_address=f"Rua B, {200 + i*10}, São Paulo, SP",
                distance_km=float(5 + i),
                eta_minutes=30 + i*5,
                price=150.0 + i*25,
                status=RequestStatus.completed,
                accepted_driver_id=driver.id,
                completed_at=now - timedelta(hours=i*2, minutes=30),
                rating=4.5 + (i % 5) * 0.1,
                helper_required=False,
                item_description=f"Móveis e pertences para mudança {i+1}",
            )
            db.add(trip)

    db.commit()


def create_session(db: Session, user_id: str) -> str:
    token = new_session_token()
    db.add(
        SessionToken(
            token=hash_session_token(token),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.commit()
    return token
