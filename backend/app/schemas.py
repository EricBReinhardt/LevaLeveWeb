from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None


class TokenResponse(BaseModel):
    user: dict


class UserUpdateIn(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    avatar_url: str | None = None


class ClientAddressIn(BaseModel):
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    zip_code: str | None = None
    has_elevator: bool = False
    floor: str | None = None


class ClientRegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    address: ClientAddressIn


class ClientTransportRequestIn(BaseModel):
    title: str
    category: str
    item_description: str
    dropoff_address: str
    dropoff_complement: str | None = None
    dropoff_floor: str | None = None
    distance_km: float
    eta_minutes: int
    item_count: int = Field(default=1, ge=1)
    helper_required: bool = False
    price: float | None = None


class ClientTripOut(BaseModel):
    id: str
    title: str
    client_name: str
    client_since: str
    category: str
    pickup_address: str
    dropoff_address: str
    distance_km: float
    eta_minutes: int
    price: float
    helper_required: bool
    item_description: str
    status: str


class ClientTripDetailOut(ClientTripOut):
    accepted_driver_name: str | None = None
    accepted_driver_phone: str | None = None


class NotificationOut(BaseModel):
    id: str
    kind: str
    title: str
    message: str
    request_id: str | None = None
    created_at: str


class DriverRegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    cpf: str
    cnh: str
    vehicle_name: str
    vehicle_plate: str
    vehicle_type: str
    capacity_kg: int = Field(default=0, ge=0)
    avatar_url: str | None = None


class DriverProfileIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    cpf: str | None = None
    cnh: str | None = None
    vehicle_name: str | None = None
    vehicle_plate: str | None = None
    vehicle_type: str | None = None
    capacity_kg: int | None = Field(default=None, ge=0)


class ClientAddressOut(ClientAddressIn):
    pass


class DriverProfileOut(BaseModel):
    name: str
    phone: str
    avatar_url: str | None = None
    cpf: str
    cnh: str
    vehicle_name: str
    vehicle_plate: str
    vehicle_type: str
    capacity_kg: int
    rating: float
    trips_completed: int
    available_balance: float


class DriverDashboardOut(BaseModel):
    total_balance: float
    today_earnings: float
    today_trips: int
    weekly_average: float
    active_requests: list[dict]
    history: list[dict]
    stats: dict


class DriverRequestOut(BaseModel):
    id: str
    title: str
    client_name: str
    client_since: str
    category: str
    pickup_address: str
    dropoff_address: str
    distance_km: float
    eta_minutes: int
    price: float
    driver_earnings: float
    helper_required: bool
    item_description: str


class DriverAcceptOut(BaseModel):
    request: ClientTripDetailOut
    notification: NotificationOut | None = None


class SimpleMessage(BaseModel):
    detail: str
