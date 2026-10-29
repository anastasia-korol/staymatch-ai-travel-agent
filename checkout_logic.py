from copy import deepcopy
from datetime import datetime
import uuid


def _get_request_value(
    trip_request,
    field,
    default=None,
):
    if trip_request is None:
        return default

    if isinstance(trip_request, dict):
        return trip_request.get(
            field,
            default,
        )

    return getattr(
        trip_request,
        field,
        default,
    )


def create_cart(
    plan,
    trip_request=None,
):
    nights = _get_request_value(
        trip_request,
        "nights",
    )

    start_date = _get_request_value(
        trip_request,
        "start_date",
    )

    end_date = _get_request_value(
        trip_request,
        "end_date",
    )

    travel_month = _get_request_value(
        trip_request,
        "travel_month",
    )

    adults = _get_request_value(
        trip_request,
        "adults",
        1,
    )

    children = _get_request_value(
        trip_request,
        "children",
        0,
    )

    child_ages = list(
        _get_request_value(
            trip_request,
            "child_ages",
            [],
        )
        or []
    )

    items = []

    items.append(
        {
            "type": "transport",
            "name": (
                f"{plan.transport.transport_type}: "
                f"{plan.transport.origin_city} → "
                f"{plan.transport.destination_city}"
            ),
            "details": (
                f"{plan.transport.departure_time} → "
                f"{plan.transport.arrival_time}, "
                f"{plan.transport.duration_hours:g} ч"
                + (
                    " · "
                    + " · ".join(
                        plan.transport.fare_breakdown
                    )
                    if plan.transport.fare_breakdown
                    else ""
                )
            ),
            "price": plan.transport_price,
        }
    )

    hotel_details = (
        f"{plan.hotel.city}, "
        f"match {plan.hotel.match_score}%"
    )

    rooms_required = int(
        getattr(
            plan.hotel,
            "rooms_required",
            1,
        )
        or 1
    )

    price_per_room = int(
        getattr(
            plan.hotel,
            "price_per_room",
            plan.hotel.price_total,
        )
        or plan.hotel.price_total
    )

    if nights is not None:
        hotel_details += (
            f", {int(nights)} ноч."
        )

    hotel_details += (
        f", {rooms_required} "
        + (
            "номер"
            if rooms_required == 1
            else (
                "номера"
                if 2 <= rooms_required <= 4
                else "номеров"
            )
        )
    )

    if rooms_required > 1:
        price_per_room_text = (
            f"{price_per_room:,}"
            .replace(",", " ")
        )

        hotel_details += (
            f", {price_per_room_text} ₽ за номер"
        )

    items.append(
        {
            "type": "hotel",
            "name": plan.hotel.hotel_name,
            "details": hotel_details,
            "price": plan.hotel_price,
        }
    )

    if plan.transfer is not None:
        items.append(
            {
                "type": "transfer",
                "name": plan.transfer.transfer_type,
                "details": (
                    f"{plan.transfer.duration_minutes} мин."
                    + (
                        " · "
                        + " · ".join(
                            plan.transfer.fare_breakdown
                        )
                        if plan.transfer.fare_breakdown
                        else ""
                    )
                ),
                "price": plan.transfer_price,
            }
        )

    calculated_total = sum(
        item["price"]
        for item in items
    )

    total_ok = (
        calculated_total
        == plan.total_price
    )

    return {
        "destination_city": plan.destination_city,
        "nights": nights,
        "start_date": start_date,
        "end_date": end_date,
        "travel_month": travel_month,
        "adults": int(adults or 1),
        "children": int(children or 0),
        "child_ages": child_ages,
        "rooms_required": rooms_required,
        "items": items,
        "calculated_total": calculated_total,
        "plan_total": plan.total_price,
        "total_ok": total_ok,
        "match_score": plan.match_score,
        "warnings": deepcopy(plan.warnings),
        "compatibility_ok": plan.compatibility_ok,
    }


def validate_cart(cart):
    errors = []

    if not cart["items"]:
        errors.append(
            "Корзина пуста."
        )

    if not cart["total_ok"]:
        errors.append(
            "Итоговая сумма корзины "
            "не совпадает со стоимостью "
            "TripPlan."
        )

    if cart["calculated_total"] <= 0:
        errors.append(
            "Некорректная итоговая стоимость."
        )

    if not cart["compatibility_ok"]:
        errors.append(
            "Обнаружена критическая "
            "проблема со стыковками."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def mock_checkout(
    cart,
    traveler_name,
    warnings_confirmed=False,
):
    validation = validate_cart(
        cart
    )

    if not validation["valid"]:
        return {
            "status": "checkout_error",
            "message": (
                "Не удалось оформить поездку."
            ),
            "errors": validation["errors"],
        }

    if (
        cart["warnings"]
        and not warnings_confirmed
    ):
        return {
            "status": "needs_warning_confirmation",
            "message": (
                "Перед оформлением нужно "
                "подтвердить, что вы ознакомились "
                "с предупреждениями."
            ),
            "warnings": cart["warnings"],
        }

    order_id = (
        "SM-"
        + uuid.uuid4().hex[:8].upper()
    )

    order = {
        "order_id": order_id,
        "status": "confirmed_mock",
        "traveler_name": traveler_name,
        "destination_city": cart[
            "destination_city"
        ],
        "nights": cart.get(
            "nights"
        ),
        "start_date": cart.get(
            "start_date"
        ),
        "end_date": cart.get(
            "end_date"
        ),
        "travel_month": cart.get(
            "travel_month"
        ),
        "adults": cart.get(
            "adults",
            1,
        ),
        "children": cart.get(
            "children",
            0,
        ),
        "child_ages": list(
            cart.get(
                "child_ages",
                [],
            )
            or []
        ),
        "rooms_required": cart.get(
            "rooms_required",
            1,
        ),
        "total_price": cart[
            "calculated_total"
        ],
        "currency": "RUB",
        "items": deepcopy(cart["items"]),
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "payment": "simulated",
    }

    return {
        "status": "success",
        "message": (
            "Поездка оформлена "
            "в демонстрационном режиме."
        ),
        "order": order,
    }


def select_plan(
    state,
    plan_index,
):
    state = deepcopy(state)

    result = state.get("result")

    if (
        result is None
        or result.get("status") != "success"
    ):
        return {
            "status": "error",
            "message": (
                "Нет доступных рекомендаций "
                "для выбора."
            ),
            "state": state,
        }

    plans = result["plans"]

    if (
        plan_index < 0
        or plan_index >= len(plans)
    ):
        return {
            "status": "error",
            "message": (
                "Некорректный номер варианта."
            ),
            "state": state,
        }

    selected_plan = plans[plan_index]

    trip_request = (
        state.get("trip_request")
        or state.get("request")
    )

    cart = create_cart(
        selected_plan,
        trip_request=trip_request,
    )

    state["selected_plan"] = selected_plan
    state["cart"] = cart
    state["status"] = "cart_ready"

    return {
        "status": "success",
        "message": (
            "Вариант добавлен в корзину."
        ),
        "state": state,
        "cart": cart,
    }
