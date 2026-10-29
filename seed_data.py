
from pathlib import Path
import pandas as pd


def seed_demo_data(data_dir="data"):
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    destinations = pd.DataFrame([
        {
            "destination_id": "sochi",
            "city": "Сочи",
            "country": "Россия",
            "sea": 1,
            "warm_weather": 0,
            "november_temp_c": 15,
            "november_sea_temp_c": 16,
            "family_score": 5,
            "relax_score": 4,
            "sightseeing_score": 4,
            "estimated_daily_budget": 9000,
            "description": "Море, прогулки, семейный отдых и мягкая погода без долгого перелёта."
        },
        {
            "destination_id": "antalya",
            "city": "Анталья",
            "country": "Турция",
            "sea": 1,
            "warm_weather": 1,
            "november_temp_c": 22,
            "november_sea_temp_c": 23,
            "family_score": 5,
            "relax_score": 5,
            "sightseeing_score": 4,
            "estimated_daily_budget": 12000,
            "description": "Тёплое море, семейные отели, спокойный отдых и прогулки."
        },
        {
            "destination_id": "dubai",
            "city": "Дубай",
            "country": "ОАЭ",
            "sea": 1,
            "warm_weather": 1,
            "november_temp_c": 30,
            "november_sea_temp_c": 28,
            "family_score": 5,
            "relax_score": 5,
            "sightseeing_score": 5,
            "estimated_daily_budget": 18000,
            "description": "Тёплое море в ноябре, развитая инфраструктура и много развлечений."
        },
        {
            "destination_id": "kaliningrad",
            "city": "Калининград",
            "country": "Россия",
            "sea": 1,
            "warm_weather": 0,
            "november_temp_c": 8,
            "november_sea_temp_c": 9,
            "family_score": 4,
            "relax_score": 3,
            "sightseeing_score": 5,
            "estimated_daily_budget": 8000,
            "description": "Балтийское море, архитектура, экскурсии и спокойные прогулки."
        },
        {
            "destination_id": "kazan",
            "city": "Казань",
            "country": "Россия",
            "sea": 0,
            "warm_weather": 0,
            "november_temp_c": 1,
            "november_sea_temp_c": None,
            "family_score": 4,
            "relax_score": 3,
            "sightseeing_score": 5,
            "estimated_daily_budget": 7500,
            "description": "Городская поездка с культурной программой, архитектурой и гастрономией."
        }
    ])

    transport = pd.DataFrame([
        {
            "transport_id": "tr_001",
            "transport_type": "Самолёт",
            "origin_city": "Москва",
            "destination_city": "Сочи",
            "departure_time": "08:00",
            "arrival_time": "11:30",
            "duration_hours": 3.5,
            "price_total": 28000
        },
        {
            "transport_id": "tr_002",
            "transport_type": "Поезд",
            "origin_city": "Москва",
            "destination_city": "Сочи",
            "departure_time": "14:00",
            "arrival_time": "13:00",
            "duration_hours": 23.0,
            "price_total": 18000
        },
        {
            "transport_id": "tr_003",
            "transport_type": "Самолёт",
            "origin_city": "Москва",
            "destination_city": "Анталья",
            "departure_time": "09:00",
            "arrival_time": "14:00",
            "duration_hours": 5.0,
            "price_total": 52000
        },
        {
            "transport_id": "tr_004",
            "transport_type": "Самолёт",
            "origin_city": "Москва",
            "destination_city": "Дубай",
            "departure_time": "07:30",
            "arrival_time": "13:15",
            "duration_hours": 5.75,
            "price_total": 68000
        },
        {
            "transport_id": "tr_005",
            "transport_type": "Самолёт",
            "origin_city": "Москва",
            "destination_city": "Калининград",
            "departure_time": "10:00",
            "arrival_time": "12:45",
            "duration_hours": 2.75,
            "price_total": 24000
        },
        {
            "transport_id": "tr_006",
            "transport_type": "Самолёт",
            "origin_city": "Москва",
            "destination_city": "Казань",
            "departure_time": "11:00",
            "arrival_time": "12:40",
            "duration_hours": 1.7,
            "price_total": 20000
        },
        {
            "transport_id": "tr_007",
            "transport_type": "Поезд",
            "origin_city": "Ростов-на-Дону",
            "destination_city": "Сочи",
            "departure_time": "07:00",
            "arrival_time": "15:00",
            "duration_hours": 8.0,
            "price_total": 12000
        },
        {
            "transport_id": "tr_008",
            "transport_type": "Самолёт",
            "origin_city": "Ростов-на-Дону",
            "destination_city": "Анталья",
            "departure_time": "08:00",
            "arrival_time": "12:30",
            "duration_hours": 4.5,
            "price_total": 46000
        },
        {
            "transport_id": "tr_009",
            "transport_type": "Самолёт",
            "origin_city": "Санкт-Петербург",
            "destination_city": "Сочи",
            "departure_time": "09:30",
            "arrival_time": "13:45",
            "duration_hours": 4.25,
            "price_total": 32000
        },
        {
            "transport_id": "tr_010",
            "transport_type": "Самолёт",
            "origin_city": "Санкт-Петербург",
            "destination_city": "Анталья",
            "departure_time": "06:30",
            "arrival_time": "12:00",
            "duration_hours": 5.5,
            "price_total": 58000
        }
    ])

    # Демо-тариф на одного взрослого пассажира.
    # Старое поле price_total оставлено для совместимости
    # с историей проекта, но расчёт поездки использует adult_price.
    transport["adult_price"] = (
        transport["price_total"] / 2
    ).round().astype(int)

    transfers = pd.DataFrame([
        {
            "transfer_id": "tf_001",
            "city": "Сочи",
            "transfer_type": "Такси",
            "duration_minutes": 35,
            "price_total": 2500
        },
        {
            "transfer_id": "tf_002",
            "city": "Анталья",
            "transfer_type": "Индивидуальный трансфер",
            "duration_minutes": 45,
            "price_total": 4500
        },
        {
            "transfer_id": "tf_003",
            "city": "Дубай",
            "transfer_type": "Такси",
            "duration_minutes": 30,
            "price_total": 5500
        },
        {
            "transfer_id": "tf_004",
            "city": "Калининград",
            "transfer_type": "Такси",
            "duration_minutes": 30,
            "price_total": 1800
        },
        {
            "transfer_id": "tf_005",
            "city": "Казань",
            "transfer_type": "Такси",
            "duration_minutes": 25,
            "price_total": 1500
        }
    ])

    # Демо-тариф трансфера на одного взрослого.
    # Детские коэффициенты применяются в trip_engine.py.
    transfers["adult_price"] = (
        transfers["price_total"] / 2
    ).round().astype(int)

    hotels = pd.DataFrame([
        {
            "hotel_id": "sochi_001",
            "hotel_name": "Sea Breeze",
            "city": "Сочи",
            "price_total": 87000,
            "room_capacity": 4,
            "rating": 4.6,
            "breakfast_score": 4,
            "quiet_score": 5,
            "family_score": 5,
            "cleanliness_score": 4,
            "location_score": 5,
            "distance_to_sea_min": 5,
            "free_cancellation": 1,
            "elevator": 1,
            "baby_cot": 1,
            "pet_friendly": 1
        },
        {
            "hotel_id": "sochi_002",
            "hotel_name": "Palm Hotel",
            "city": "Сочи",
            "price_total": 72000,
            "room_capacity": 3,
            "rating": 4.7,
            "breakfast_score": 5,
            "quiet_score": 5,
            "family_score": 4,
            "cleanliness_score": 5,
            "location_score": 4,
            "distance_to_sea_min": 15,
            "free_cancellation": 1,
            "elevator": 1,
            "baby_cot": 0,
            "pet_friendly": 0
        },
        {
            "hotel_id": "sochi_003",
            "hotel_name": "Proper Place",
            "city": "Сочи",
            "price_total": 74000,
            "room_capacity": 4,
            "rating": 4.6,
            "breakfast_score": 5,
            "quiet_score": 2,
            "family_score": 5,
            "cleanliness_score": 5,
            "location_score": 5,
            "distance_to_sea_min": 5,
            "free_cancellation": 0,
            "elevator": 1,
            "baby_cot": 1,
            "pet_friendly": 1
        },
        {
            "hotel_id": "antalya_001",
            "hotel_name": "Lara Family Resort",
            "city": "Анталья",
            "price_total": 76000,
            "room_capacity": 4,
            "rating": 4.8,
            "breakfast_score": 5,
            "quiet_score": 4,
            "family_score": 5,
            "cleanliness_score": 5,
            "location_score": 5,
            "distance_to_sea_min": 3,
            "free_cancellation": 1,
            "elevator": 1,
            "baby_cot": 1,
            "pet_friendly": 1
        },
        {
            "hotel_id": "antalya_002",
            "hotel_name": "Mediterranean Garden",
            "city": "Анталья",
            "price_total": 62000,
            "room_capacity": 3,
            "rating": 4.6,
            "breakfast_score": 4,
            "quiet_score": 5,
            "family_score": 4,
            "cleanliness_score": 5,
            "location_score": 4,
            "distance_to_sea_min": 10,
            "free_cancellation": 1,
            "elevator": 1,
            "baby_cot": 1,
            "pet_friendly": 0
        },
        {
            "hotel_id": "antalya_003",
            "hotel_name": "Old Town Beach Hotel",
            "city": "Анталья",
            "price_total": 55000,
            "room_capacity": 2,
            "rating": 4.5,
            "breakfast_score": 4,
            "quiet_score": 2,
            "family_score": 3,
            "cleanliness_score": 4,
            "location_score": 5,
            "distance_to_sea_min": 7,
            "free_cancellation": 0,
            "elevator": 1,
            "baby_cot": 0,
            "pet_friendly": 1
        },
        {
            "hotel_id": "dubai_001",
            "hotel_name": "Marina Family Suites",
            "city": "Дубай",
            "price_total": 105000,
            "room_capacity": 5,
            "rating": 4.8,
            "breakfast_score": 5,
            "quiet_score": 4,
            "family_score": 5,
            "cleanliness_score": 5,
            "location_score": 5,
            "distance_to_sea_min": 5,
            "free_cancellation": 1,
            "elevator": 1,
            "baby_cot": 1,
            "pet_friendly": 1
        },
        {
            "hotel_id": "dubai_002",
            "hotel_name": "Palm View Hotel",
            "city": "Дубай",
            "price_total": 92000,
            "room_capacity": 3,
            "rating": 4.7,
            "breakfast_score": 5,
            "quiet_score": 5,
            "family_score": 4,
            "cleanliness_score": 5,
            "location_score": 4,
            "distance_to_sea_min": 12,
            "free_cancellation": 1,
            "elevator": 1,
            "baby_cot": 1,
            "pet_friendly": 0
        },
        {
            "hotel_id": "dubai_003",
            "hotel_name": "City Beach Inn",
            "city": "Дубай",
            "price_total": 78000,
            "room_capacity": 2,
            "rating": 4.4,
            "breakfast_score": 4,
            "quiet_score": 3,
            "family_score": 4,
            "cleanliness_score": 4,
            "location_score": 4,
            "distance_to_sea_min": 20,
            "free_cancellation": 0,
            "elevator": 1,
            "baby_cot": 0,
            "pet_friendly": 1
        }
    ])

    def calculate_sea_score(minutes):
        if minutes <= 5:
            return 5
        if minutes <= 10:
            return 4
        if minutes <= 15:
            return 3
        if minutes <= 20:
            return 2
        return 1

    hotels["sea_score"] = hotels["distance_to_sea_min"].apply(calculate_sea_score)

    destinations.to_csv(data_path / "destinations.csv", index=False, encoding="utf-8-sig")
    transport.to_csv(data_path / "transport.csv", index=False, encoding="utf-8-sig")
    transfers.to_csv(data_path / "transfers.csv", index=False, encoding="utf-8-sig")
    hotels.to_csv(data_path / "hotels.csv", index=False, encoding="utf-8-sig")

    return {
        "destinations": len(destinations),
        "transport": len(transport),
        "transfers": len(transfers),
        "hotels": len(hotels),
    }


if __name__ == "__main__":
    print(seed_demo_data())
