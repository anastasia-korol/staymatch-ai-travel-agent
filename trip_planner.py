
from datetime import datetime, timedelta
from math import ceil

import pandas as pd

from trip_models import (
    TripPlan,
    TransportOption,
    TransferOption,
    HotelOption,
)

from trip_engine import (
    recommend_destinations,
    find_best_transport,
    find_transfer,
    calculate_transport_pricing,
    calculate_transfer_pricing,
)


def load_trip_hotels():
    return pd.read_csv("data/hotels.csv")


def calculate_room_allocation(
    hotel,
    trip_request,
):
    room_capacity = int(
        hotel.get(
            "room_capacity",
            2,
        )
        or 2
    )

    room_capacity = max(
        1,
        room_capacity,
    )

    adults = max(
        1,
        int(
            trip_request.adults
            or 1
        ),
    )

    children = max(
        0,
        int(
            trip_request.children
            or 0
        ),
    )

    total_guests = (
        adults
        + children
    )

    rooms_required = max(
        1,
        ceil(
            total_guests
            / room_capacity
        ),
    )

    nights = max(
        1,
        int(
            trip_request.nights
            or 7
        ),
    )

    base_price_7_nights = int(
        hotel["price_total"]
    )

    raw_room_price = (
        base_price_7_nights
        * nights
        / 7
    )

    price_per_room = int(
        round(
            raw_room_price
            / 500
        )
        * 500
    )

    price_per_room = max(
        500,
        price_per_room,
    )

    hotel_total_price = (
        price_per_room
        * rooms_required
    )

    return {
        "room_capacity": room_capacity,
        "rooms_required": rooms_required,
        "total_guests": total_guests,
        "price_per_room": price_per_room,
        "hotel_total_price": (
            hotel_total_price
        ),
    }


def format_room_count(
    count,
):
    count = int(count)

    last_two = count % 100
    last_one = count % 10

    if 11 <= last_two <= 14:
        word = "номеров"
    elif last_one == 1:
        word = "номер"
    elif 2 <= last_one <= 4:
        word = "номера"
    else:
        word = "номеров"

    return f"{count} {word}"


def calculate_hotel_match(
    hotel,
    trip_request,
):
    score = 0.0
    total_weight = 0.0
    strengths = []
    tradeoffs = []

    weights = {
        "rating": 2,
        "cleanliness_score": 2,
        "location_score": 2,
        "breakfast_score": 1,
        "quiet_score": 1,
    }

    if trip_request.children > 0:
        weights["family_score"] = 5
        weights["baby_cot"] = 2

    if trip_request.sea_required is True:
        weights["sea_score"] = 5

    for criterion, priority in (
        trip_request.hotel_preferences.items()
    ):
        weights[criterion] = priority

    for criterion, required_value in (
        trip_request.hotel_hard_filters.items()
    ):
        if criterion in hotel.index:
            if hotel[criterion] != required_value:
                return {
                    "eligible": False,
                    "score": 0,
                    "strengths": [],
                    "tradeoffs": [
                        (
                            "не выполняется обязательное "
                            f"условие {criterion}"
                        )
                    ],
                }

    max_values = {
        "rating": 5,
        "cleanliness_score": 5,
        "location_score": 5,
        "breakfast_score": 5,
        "quiet_score": 5,
        "family_score": 5,
        "sea_score": 5,
        "baby_cot": 1,
        "free_cancellation": 1,
        "elevator": 1,
        "pet_friendly": 1,
    }

    for criterion, weight in weights.items():
        if criterion not in hotel.index:
            continue

        max_value = max_values.get(criterion)
        if max_value is None:
            continue

        value = float(hotel[criterion])
        normalized = value / max_value

        score += normalized * weight
        total_weight += weight

    if total_weight > 0:
        score = score / total_weight * 100
    else:
        score = float(hotel["rating"]) / 5 * 100

    if float(hotel["rating"]) >= 4.5:
        strengths.append(
            f"высокий рейтинг {hotel['rating']}/5"
        )

    if trip_request.children > 0:
        if int(hotel["family_score"]) >= 4:
            family_phrase = (
                "хорошо подходит для отдыха "
                "с ребёнком"
                if trip_request.children == 1
                else "хорошо подходит для отдыха с детьми"
            )

            strengths.append(
                family_phrase
            )
        else:
            tradeoffs.append(
                "семейная инфраструктура слабее желаемой"
            )

        if int(hotel["baby_cot"]) == 1:
            strengths.append(
                "есть детская кроватка"
            )
        else:
            tradeoffs.append(
                "детская кроватка не заявлена"
            )

    if trip_request.sea_required is True:
        sea_minutes = int(
            hotel["distance_to_sea_min"]
        )

        if sea_minutes <= 10:
            strengths.append(
                f"до моря около {sea_minutes} мин."
            )
        elif sea_minutes > 15:
            tradeoffs.append(
                f"до моря около {sea_minutes} мин."
            )

    if int(hotel["free_cancellation"]) == 1:
        strengths.append(
            "есть бесплатная отмена"
        )
    else:
        tradeoffs.append(
            "нет бесплатной отмены"
        )

    if int(hotel["quiet_score"]) >= 4:
        strengths.append(
            "тихий отель"
        )

    if trip_request.pet:
        if int(hotel.get("pet_friendly", 0)) == 1:
            strengths.append(
                "можно с питомцем"
            )

    return {
        "eligible": True,
        "score": round(score, 1),
        "strengths": strengths,
        "tradeoffs": tradeoffs,
    }


def choose_hotel(
    destination_city,
    hotels,
    trip_request,
    transport_price,
    transfer_price,
):
    city_hotels = hotels[
        hotels["city"] == destination_city
    ].copy()

    if city_hotels.empty:
        return None

    evaluated = []

    for _, hotel in city_hotels.iterrows():
        evaluation = calculate_hotel_match(
            hotel,
            trip_request,
        )

        if not evaluation["eligible"]:
            continue

        room_allocation = (
            calculate_room_allocation(
                hotel,
                trip_request,
            )
        )

        if (
            room_allocation[
                "rooms_required"
            ]
            > 1
        ):
            evaluation[
                "tradeoffs"
            ].append(
                (
                    f"для "
                    f"{room_allocation['total_guests']} "
                    f"гостей потребуется "
                    f"{format_room_count(room_allocation['rooms_required'])}"
                )
            )

        total_trip_price = (
            room_allocation[
                "hotel_total_price"
            ]
            + transport_price
            + transfer_price
        )

        within_budget = True
        if trip_request.max_budget is not None:
            within_budget = (
                total_trip_price
                <= trip_request.max_budget
            )

        evaluated.append(
            {
                "hotel": hotel,
                "hotel_score": evaluation["score"],
                "strengths": evaluation["strengths"],
                "tradeoffs": evaluation["tradeoffs"],
                "total_trip_price": total_trip_price,
                "within_budget": within_budget,
                "room_capacity": (
                    room_allocation[
                        "room_capacity"
                    ]
                ),
                "rooms_required": (
                    room_allocation[
                        "rooms_required"
                    ]
                ),
                "total_guests": (
                    room_allocation[
                        "total_guests"
                    ]
                ),
                "price_per_room": (
                    room_allocation[
                        "price_per_room"
                    ]
                ),
                "hotel_total_price": (
                    room_allocation[
                        "hotel_total_price"
                    ]
                ),
            }
        )

    if not evaluated:
        return None

    within_budget_options = [
        option
        for option in evaluated
        if option["within_budget"]
    ]

    pool = (
        within_budget_options
        if within_budget_options
        else evaluated
    )

    pool = sorted(
        pool,
        key=lambda option: (
            -option["hotel_score"],
            option["total_trip_price"],
        ),
    )

    return pool[0]


def validate_trip_timing(
    transport_row,
    transfer_row,
):
    warnings = []
    compatibility_ok = True

    arrival_time = str(
        transport_row["arrival_time"]
    )

    try:
        arrival_dt = datetime.strptime(
            arrival_time,
            "%H:%M",
        )

        transfer_minutes = 0

        if transfer_row is not None:
            transfer_minutes = int(
                transfer_row["duration_minutes"]
            )

        hotel_arrival = (
            arrival_dt
            + timedelta(
                minutes=transfer_minutes + 30
            )
        )

        check_in = datetime.strptime(
            "14:00",
            "%H:%M",
        )

        if hotel_arrival < check_in:
            warnings.append(
                "Вы приедете раньше стандартного "
                "заселения в 14:00. Возможно, "
                "понадобится ранний заезд "
                "или хранение багажа."
            )

        late_threshold = datetime.strptime(
            "23:00",
            "%H:%M",
        )

        if hotel_arrival > late_threshold:
            warnings.append(
                "Ожидаемое прибытие в отель "
                "позднее 23:00. Стоит заранее "
                "подтвердить позднее заселение."
            )

    except ValueError:
        warnings.append(
            "Не удалось автоматически "
            "проверить время заселения."
        )

    return compatibility_ok, warnings


def calculate_final_trip_score(
    destination_option,
    hotel_score,
    actual_total_price,
    trip_request,
):
    destination_score = float(
        destination_option["match_score"]
    )

    if trip_request.max_budget is not None:
        preliminary_total = int(
            destination_option["estimated_total"]
        )

        old_budget_component = (
            15
            if preliminary_total
            <= trip_request.max_budget
            else -25
        )

        new_budget_component = (
            15
            if actual_total_price
            <= trip_request.max_budget
            else -25
        )

        destination_score = (
            destination_score
            - old_budget_component
            + new_budget_component
        )

        destination_score = max(
            0,
            min(destination_score, 100),
        )

    final_score = (
        destination_score * 0.55
        + float(hotel_score) * 0.45
    )

    if (
        trip_request.max_budget is not None
        and actual_total_price
        > trip_request.max_budget
    ):
        overspend = (
            actual_total_price
            - trip_request.max_budget
        )

        overspend_share = (
            overspend
            / trip_request.max_budget
        )

        overspend_penalty = min(
            overspend_share * 100,
            25,
        )

        final_score -= overspend_penalty

    final_score = round(
        max(0, min(final_score, 100)),
        1,
    )

    return final_score


def build_trip_plan(
    destination_option,
    trip_request,
    transport,
    transfers,
    hotels,
):
    destination_city = (
        destination_option["city"]
    )

    transport_row = find_best_transport(
        origin_city=trip_request.origin_city,
        destination_city=destination_city,
        transport=transport,
        max_travel_hours=(
            trip_request.max_travel_hours
        ),
    )

    if transport_row is None:
        return None

    transport_pricing = calculate_transport_pricing(
        transport_row,
        trip_request,
    )

    transport_price = int(
        transport_pricing["total"]
    )

    transfer_row = find_transfer(
        destination_city,
        transfers,
    )

    transfer_pricing = calculate_transfer_pricing(
        transfer_row,
        trip_request,
    )

    transfer_price = int(
        transfer_pricing["total"]
    )

    hotel_result = choose_hotel(
        destination_city=destination_city,
        hotels=hotels,
        trip_request=trip_request,
        transport_price=transport_price,
        transfer_price=transfer_price,
    )

    if hotel_result is None:
        return None

    hotel = hotel_result["hotel"]

    hotel_price = int(
        hotel_result[
            "hotel_total_price"
        ]
    )

    rooms_required = int(
        hotel_result[
            "rooms_required"
        ]
    )

    room_capacity = int(
        hotel_result[
            "room_capacity"
        ]
    )

    price_per_room = int(
        hotel_result[
            "price_per_room"
        ]
    )

    total_price = (
        transport_price
        + hotel_price
        + transfer_price
    )

    compatibility_ok, warnings = (
        validate_trip_timing(
            transport_row,
            transfer_row,
        )
    )

    destination_warnings = (
        destination_option.get(
            "warnings",
            []
        )
    )

    if isinstance(
        destination_warnings,
        list,
    ):
        warnings.extend(
            destination_warnings
        )

    if (
        trip_request.max_budget is not None
        and total_price > trip_request.max_budget
    ):
        overspend = (
            total_price
            - trip_request.max_budget
        )

        warnings.append(
            (
                f"Итоговая стоимость выше "
                f"бюджета на {overspend:,} ₽."
            ).replace(",", " ")
        )

    hotel_score = float(
        hotel_result["hotel_score"]
    )

    match_score = calculate_final_trip_score(
        destination_option=destination_option,
        hotel_score=hotel_score,
        actual_total_price=total_price,
        trip_request=trip_request,
    )

    destination_reasons = (
        destination_option["reasons"]
    )

    if isinstance(
        destination_reasons,
        list,
    ):
        destination_reason = ", ".join(
            destination_reasons
        )
    else:
        destination_reason = str(
            destination_reasons
        )

    strengths = hotel_result["strengths"]
    tradeoffs = hotel_result["tradeoffs"]

    strengths_text = (
        " • ".join(strengths)
        if strengths
        else "сбалансированный вариант"
    )

    tradeoffs_text = (
        " • ".join(tradeoffs)
        if tradeoffs
        else "существенных компромиссов нет"
    )

    why_not_100 = (
        tradeoffs_text
        if tradeoffs
        else (
            "Отель хорошо соответствует "
            "основным условиям поездки."
        )
    )

    explanation = (
        f"{destination_city} подходит, потому что "
        f"{destination_reason}. "
        f"Отель {hotel['hotel_name']}: "
        f"{strengths_text}."
    )

    transport_option = TransportOption(
        transport_id=str(
            transport_row["transport_id"]
        ),
        transport_type=str(
            transport_row["transport_type"]
        ),
        origin_city=str(
            transport_row["origin_city"]
        ),
        destination_city=str(
            transport_row["destination_city"]
        ),
        departure_time=str(
            transport_row["departure_time"]
        ),
        arrival_time=str(
            transport_row["arrival_time"]
        ),
        duration_hours=float(
            transport_row["duration_hours"]
        ),
        price_total=transport_price,
        adult_unit_price=int(
            transport_pricing["adult_unit_price"]
        ),
        child_unit_price=int(
            transport_pricing["child_unit_price"]
        ),
        infant_unit_price=int(
            transport_pricing["infant_unit_price"]
        ),
        fare_breakdown=list(
            transport_pricing["fare_breakdown"]
        ),
    )

    if transfer_row is not None:
        transfer_option = TransferOption(
            transfer_id=str(
                transfer_row["transfer_id"]
            ),
            city=str(
                transfer_row["city"]
            ),
            transfer_type=str(
                transfer_row["transfer_type"]
            ),
            duration_minutes=int(
                transfer_row["duration_minutes"]
            ),
            price_total=transfer_price,
            adult_unit_price=int(
                transfer_pricing["adult_unit_price"]
            ),
            child_unit_price=int(
                transfer_pricing["child_unit_price"]
            ),
            infant_unit_price=int(
                transfer_pricing["infant_unit_price"]
            ),
            fare_breakdown=list(
                transfer_pricing["fare_breakdown"]
            ),
        )
    else:
        transfer_option = None

    hotel_option = HotelOption(
        hotel_id=str(
            hotel["hotel_id"]
        ),
        hotel_name=str(
            hotel["hotel_name"]
        ),
        city=str(
            hotel["city"]
        ),
        price_total=hotel_price,
        price_per_room=price_per_room,
        room_capacity=room_capacity,
        rooms_required=rooms_required,
        match_score=float(
            hotel_result["hotel_score"]
        ),
        strengths=strengths_text,
        tradeoffs=tradeoffs_text,
        why_not_100=why_not_100,
    )

    return TripPlan(
        destination_city=destination_city,
        destination_reason=destination_reason,
        transport=transport_option,
        hotel=hotel_option,
        transfer=transfer_option,
        transport_price=transport_price,
        hotel_price=hotel_price,
        transfer_price=transfer_price,
        total_price=total_price,
        match_score=match_score,
        compatibility_ok=compatibility_ok,
        warnings=warnings,
        explanation=explanation,
    )


def build_trip_plans(
    trip_request,
    destinations,
    transport,
    transfers,
    hotels,
    top_n=3,
):
    destination_result = recommend_destinations(
        trip_request=trip_request,
        destinations=destinations,
        transport=transport,
        transfers=transfers,
        top_n=top_n,
    )

    if (
        destination_result["status"]
        == "needs_clarification"
    ):
        return destination_result

    if (
        destination_result["status"]
        != "success"
    ):
        return destination_result

    plans = []

    for _, destination_option in (
        destination_result["options"].iterrows()
    ):
        plan = build_trip_plan(
            destination_option=destination_option,
            trip_request=trip_request,
            transport=transport,
            transfers=transfers,
            hotels=hotels,
        )

        if plan is not None:
            plans.append(plan)

    if not plans:
        return {
            "status": "no_results",
            "message": (
                "Направления найдены, но не удалось "
                "собрать полную поездку с отелем "
                "и транспортом."
            ),
            "plans": [],
        }

    plans = sorted(
        plans,
        key=lambda plan: (
            -plan.match_score,
            plan.total_price,
        ),
    )

    return {
        "status": "success",
        "plans": plans[:top_n],
    }
