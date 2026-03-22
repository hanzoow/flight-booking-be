from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3, description="IATA origin")
    destination: str = Field(..., min_length=3, max_length=3, description="IATA destination")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD recommended)")
    return_date: str | None = None
    pax_count: int = Field(1, ge=1, le=9)
    cabin: str = Field("Y", min_length=1, max_length=1)

    @field_validator("origin", "destination")
    @classmethod
    def upper_iata(cls, v: str) -> str:
        return v.strip().upper()


class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PassengerCreate(BaseModel):
    title: str | None = None
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    dob: str | None = None
    nationality: str | None = Field(None, max_length=3)
    passport_no: str | None = Field(None, max_length=32)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=32)


class CreateBookingBody(BaseModel):
    offer_id: str = Field(..., min_length=4, max_length=64)
    contact_email: EmailStr
    contact_phone: str | None = Field(None, max_length=32)
    passengers: list[PassengerCreate] = Field(..., min_length=1, max_length=9)

    @field_validator("offer_id")
    @classmethod
    def strip_offer(cls, v: str) -> str:
        return v.strip()


class Money(BaseModel):
    amount: float
    currency: str


class TaxLine(BaseModel):
    code: str
    label: str | None = None
    amount: float


class LegSummary(BaseModel):
    departure_airport: str
    departure_city: str | None = None
    departure_terminal: str | None = None
    departure_at: str | None = None
    arrival_airport: str
    arrival_city: str | None = None
    arrival_terminal: str | None = None
    arrival_at: str | None = None
    marketing_carrier: str
    marketing_carrier_name: str | None = None
    flight_number: str | None = None
    cabin_code: str | None = None
    cabin_label: str | None = None
    duration_minutes: int | None = None
    aircraft_code: str | None = None
    aircraft_label: str | None = None


class OfferSummary(BaseModel):
    offer_id: str
    direction: str
    airline_code: str
    airline_name: str | None = None
    departure: dict[str, Any]
    arrival: dict[str, Any]
    stops: int
    duration_minutes: int | None = None
    duration_display: str | None = None
    price: dict[str, Any]
    cabin_code: str | None = None
    cabin_label: str | None = None
    legs: list[LegSummary]
    seats_remaining: int | None = None
    refundable: bool | None = None
    search_id: str | None = None


class FlightSearchResponse(BaseModel):
    search_id: str | None = None
    items: list[OfferSummary]
    page: int
    page_size: int
    total: int


class AirportOut(BaseModel):
    code: str
    city: str | None = None
    country_code: str | None = None
    tz_offset_hours: int | None = None
    latitude: float | None = None
    longitude: float | None = None


class BookingPassengerOut(BaseModel):
    id: str | None = None
    title: str | None = None
    first_name: str
    last_name: str
    date_of_birth: str | None = None
    nationality: str | None = None
    passport_number: str | None = None
    type_code: str | None = None
    type_label: str | None = None


class BookingConfirmation(BaseModel):
    booking_reference: str
    pnr: str | None = None
    status: str
    status_code: str | None = None
    status_label: str | None = None
    offer_id: str
    passengers: list[BookingPassengerOut]
    contact: dict[str, str | None]
    ticketing: dict[str, Any]
    created_at: str | None = None


class ReferenceLabelsResponse(BaseModel):
    """Static code → human-readable labels from BFF config (no legacy call)."""

    airlines: dict[str, str] = Field(..., description="IATA-style carrier code → airline name")
    cabins: dict[str, str] = Field(..., description="Cabin class code → cabin name")
    aircraft: dict[str, str] = Field(..., description="Equipment / type code → aircraft description")
    tax_codes: dict[str, str] = Field(..., description="Tax/fee code → short description")
    passenger_types: dict[str, str] = Field(..., description="Passenger type code → label (e.g. ADT → Adult)")
