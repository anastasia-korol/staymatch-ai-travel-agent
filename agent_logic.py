
from copy import deepcopy

from trip_engine import (
    extract_origin_city,
    extract_people_count_answer,
    extract_child_ages_answer,
    parse_trip_request_basic,
)


def get_missing_critical_info(
    trip_request,
):
    missing = []

    if trip_request.origin_city is None:
        missing.append("origin_city")

    dates_known = (
        trip_request.start_date is not None
        and trip_request.end_date is not None
    )

    if (
        not dates_known
        and trip_request.travel_month is None
    ):
        missing.append("travel_period")

    if (
        trip_request.nights is None
        and not dates_known
    ):
        missing.append("nights")

    if not trip_request.adults_count_known:
        missing.append(
            "adults_count"
        )

    if not trip_request.children_count_known:
        missing.append(
            "children_count"
        )

    if (
        trip_request.children_count_known
        and trip_request.children > 0
        and len(trip_request.child_ages)
        != trip_request.children
    ):
        missing.append(
            "child_ages"
        )

    return missing


def get_next_clarification(
    trip_request,
):
    missing = get_missing_critical_info(
        trip_request
    )

    if not missing:
        return {
            "needs_clarification": False,
            "missing_field": None,
            "question": None,
            "hint": None,
            "all_missing": [],
        }

    field = missing[0]

    questions = {
        "origin_city": {
            "question": (
                "Из какого города "
                "вы планируете отправляться?"
            ),
            "hint": (
                "Например: Москва, "
                "Санкт-Петербург или "
                "Ростов-на-Дону."
            ),
        },
        "travel_period": {
            "question": (
                "Когда вы хотите поехать?"
            ),
            "hint": (
                "Можно назвать точные даты "
                "или хотя бы месяц, "
                "например: «в ноябре»."
            ),
        },
        "nights": {
            "question": (
                "На сколько дней или ночей "
                "планируете поездку?"
            ),
            "hint": (
                "Например: «на неделю» "
                "или «на 7 ночей»."
            ),
        },
        "adults_count": {
            "question": (
                "Сколько взрослых поедет?"
            ),
            "hint": (
                "Например: «2 взрослых»."
            ),
        },
        "children_count": {
            "question": (
                "Сколько детей поедет?"
            ),
            "hint": (
                "Например: «2 ребёнка»."
            ),
        },
    }

    if field == "child_ages":
        if trip_request.children == 1:
            question_data = {
                "question": (
                    "Сколько лет ребёнку?"
                ),
                "hint": (
                    "Например: «5 лет»."
                ),
            }
        else:
            question_data = {
                "question": (
                    "Сколько лет детям? "
                    "Укажите возраст каждого ребёнка."
                ),
                "hint": (
                    "Например: «1, 5 и 9 лет»."
                ),
            }
    else:
        question_data = questions[field]

    return {
        "needs_clarification": True,
        "missing_field": field,
        "question": question_data["question"],
        "hint": question_data["hint"],
        "all_missing": missing,
    }


def refresh_missing_info(
    trip_request,
):
    updated_request = deepcopy(
        trip_request
    )

    updated_request.missing_critical_info = (
        get_missing_critical_info(
            updated_request
        )
    )

    return updated_request


def apply_clarification_answer(
    trip_request,
    missing_field,
    user_answer,
    transport,
):
    updated_request = deepcopy(
        trip_request
    )

    answer = str(user_answer).strip()

    if not answer:
        return {
            "status": "invalid_answer",
            "message": (
                "Ответ пустой. Нужно уточнить значение."
            ),
            "trip_request": updated_request,
        }

    if missing_field == "origin_city":
        origin_city = extract_origin_city(
            answer,
            transport,
        )

        if origin_city is None:
            return {
                "status": "invalid_answer",
                "message": (
                    "Не удалось распознать город "
                    "отправления среди доступных "
                    "в демо-данных."
                ),
                "trip_request": updated_request,
            }

        updated_request.origin_city = origin_city

    elif missing_field == "travel_period":
        parsed_answer = parse_trip_request_basic(
            answer,
            transport,
        )

        if (
            parsed_answer.travel_month is None
            and parsed_answer.start_date is None
        ):
            return {
                "status": "invalid_answer",
                "message": (
                    "Не удалось понять период поездки. "
                    "Например, можно ответить: "
                    "«в ноябре»."
                ),
                "trip_request": updated_request,
            }

        if (
            parsed_answer.travel_month
            is not None
        ):
            updated_request.travel_month = (
                parsed_answer.travel_month
            )

        if (
            parsed_answer.start_date
            is not None
        ):
            updated_request.start_date = (
                parsed_answer.start_date
            )

        if (
            parsed_answer.end_date
            is not None
        ):
            updated_request.end_date = (
                parsed_answer.end_date
            )

    elif missing_field == "nights":
        parsed_answer = parse_trip_request_basic(
            answer,
            transport,
        )

        if parsed_answer.nights is None:
            return {
                "status": "invalid_answer",
                "message": (
                    "Не удалось понять длительность "
                    "поездки. Например: «на неделю» "
                    "или «на 7 ночей»."
                ),
                "trip_request": updated_request,
            }

        updated_request.nights = (
            parsed_answer.nights
        )

    elif missing_field == "adults_count":
        adults_count = (
            extract_people_count_answer(
                answer
            )
        )

        if adults_count is None:
            return {
                "status": "invalid_answer",
                "message": (
                    "Не удалось понять количество "
                    "взрослых. Например: "
                    "«2 взрослых»."
                ),
                "trip_request": updated_request,
            }

        updated_request.adults = (
            adults_count
        )

        updated_request.adults_count_known = (
            True
        )

    elif missing_field == "children_count":
        children_count = (
            extract_people_count_answer(
                answer
            )
        )

        if children_count is None:
            return {
                "status": "invalid_answer",
                "message": (
                    "Не удалось понять количество "
                    "детей. Например: "
                    "«2 ребёнка»."
                ),
                "trip_request": updated_request,
            }

        updated_request.children = (
            children_count
        )

        updated_request.children_count_known = (
            True
        )

        if len(updated_request.child_ages) != children_count:
            updated_request.child_ages = []

    elif missing_field == "child_ages":
        ages = extract_child_ages_answer(
            answer
        )

        if len(ages) != updated_request.children:
            return {
                "status": "invalid_answer",
                "message": (
                    f"Нужно указать возраст каждого "
                    f"ребёнка. Ожидаю "
                    f"{updated_request.children} "
                    f"значения, например: "
                    f"«1, 5 и 9 лет»."
                ),
                "trip_request": updated_request,
            }

        updated_request.child_ages = ages

    else:
        return {
            "status": "error",
            "message": (
                f"Неизвестное поле для "
                f"уточнения: {missing_field}"
            ),
            "trip_request": updated_request,
        }

    updated_request = refresh_missing_info(
        updated_request
    )

    next_clarification = get_next_clarification(
        updated_request
    )

    return {
        "status": "updated",
        "message": "Ответ принят.",
        "trip_request": updated_request,
        "next_clarification": next_clarification,
    }
