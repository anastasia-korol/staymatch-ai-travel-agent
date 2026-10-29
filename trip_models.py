from typing import Optional

from pydantic import BaseModel, Field


class TripRequest(BaseModel):
    raw_text: str
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travel_month: Optional[str] = None
    nights: Optional[int] = None

    adults: int = 1
    children: int = 0
    adults_count_known: bool = True
    children_count_known: bool = True
    child_ages: list[int] = Field(default_factory=list)

    max_budget: Optional[int] = None
    currency: str = "RUB"

    trip_preferences: list[str] = Field(default_factory=list)
    warm_weather: Optional[bool] = None
    sea_required: Optional[bool] = None
    max_travel_hours: Optional[float] = None
    transport_preferences: list[str] = Field(default_factory=list)

    hotel_preferences: dict[str, int] = Field(default_factory=dict)
    hotel_hard_filters: dict[str, int] = Field(default_factory=dict)

    pet: bool = False
    flexible_dates: bool = False
    missing_critical_info: list[str] = Field(default_factory=list)


class TransportOption(BaseModel):
    transport_id: str
    transport_type: str
    origin_city: str
    destination_city: str
    departure_time: str
    arrival_time: str
    duration_hours: float
    price_total: int
    adult_unit_price: int = 0
    child_unit_price: int = 0
    infant_unit_price: int = 0
    fare_breakdown: list[str] = Field(default_factory=list)


class TransferOption(BaseModel):
    transfer_id: str
    city: str
    transfer_type: str
    duration_minutes: int
    price_total: int
    adult_unit_price: int = 0
    child_unit_price: int = 0
    infant_unit_price: int = 0
    fare_breakdown: list[str] = Field(default_factory=list)


class HotelOption(BaseModel):
    hotel_id: str
    hotel_name: str
    city: str
    price_total: int
    price_per_room: int = 0
    room_capacity: int = 2
    rooms_required: int = 1
    match_score: float
    strengths: str
    tradeoffs: str
    why_not_100: str


class TripPlan(BaseModel):
    destination_city: str
    destination_reason: str
    transport: TransportOption
    hotel: HotelOption
    transfer: Optional[TransferOption] = None

    transport_price: int
    hotel_price: int
    transfer_price: int = 0
    total_price: int

    match_score: float
    compatibility_ok: bool = True
    warnings: list[str] = Field(default_factory=list)
    explanation: str
