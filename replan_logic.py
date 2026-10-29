from copy import deepcopy
from datetime import datetime, timedelta
import re

from trip_engine import (
    MONTH_FORMS,
    MONTH_NAMES,
    extract_date_range,
    extract_trip_budget,
    extract_nights,
    normalize_text,
)

from trip_planner import (
    build_trip_plans,
)


NUMBER_WORDS = {
    "один": 1,
    "одну": 1,
    "два": 2,
    "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
}


def parse_date_value(value):
    if value is None:
        return None

    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(
                str(value),
                date_format,
            )
        except ValueError:
            continue

    return None


def extract_date_shift(text):
    text = normalize_text(text)

    match = re.search(
        r"на\s+(\d+)\s+"
        r"(?:день|дня|дней)\s+"
        r"(позже|раньше)",
        text,
    )

    if match:
        days = int(match.group(1))
        direction = match.group(2)

        if direction == "раньше":
            days = -days

        return days

    for word, number in NUMBER_WORDS.items():
        pattern = (
            rf"на\s+{word}\s+"
            rf"(?:день|дня|дней)\s+"
            rf"(позже|раньше)"
        )

        match = re.search(
            pattern,
            text,
        )

        if match:
            value = number

            if match.group(1) == "раньше":
                value = -value

            return value

    return None


def extract_explicit_start_date(
    text,
    reference_date=None,
):
    """
    Распознаёт явное изменение даты начала:
    - "давайте с 12 ноября"
    - "поедем с 12 ноября"
    - "дата начала 12 ноября"
    - "с 12.11"
    - "с 12.11.2026"
    """

    normalized = normalize_text(text)

    prefixes = (
        r"(?:"
        r"с|"
        r"начиная\s+с|"
        r"поедем\s+с|"
        r"поехать\s+с|"
        r"вылетаем\s+с|"
        r"выезжаем\s+с|"
        r"дата\s+начала(?:\s+поездки)?\s*[:\-]?"
        r")"
    )

    numeric_match = re.search(
        prefixes
        + r"\s*(\d{1,2})[./](\d{1,2})"
        + r"(?:[./](\d{2,4}))?",
        normalized,
    )

    day = None
    month = None
    year = None

    if numeric_match:
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))

        if numeric_match.group(3):
            year = int(numeric_match.group(3))

            if year < 100:
                year += 2000

    if day is None:
        text_match = re.search(
            prefixes
            + r"\s*(\d{1,2})\s+([а-я]+)"
            + r"(?:\s+(\d{4}))?",
            normalized,
        )

        if text_match:
            day = int(text_match.group(1))
            month = MONTH_FORMS.get(
                text_match.group(2)
            )

            if text_match.group(3):
                year = int(
                    text_match.group(3)
                )

    if (
        day is None
        or month is None
    ):
        return None

    reference = parse_date_value(
        reference_date
    )

    if year is None:
        if reference is not None:
            year = reference.year
        else:
            year = datetime.now().year

    try:
        value = datetime(
            year,
            month,
            day,
        )
    except ValueError:
        return None

    return value


def _set_travel_month_from_date(
    trip_request,
    date_value,
):
    if date_value is None:
        return

    trip_request.travel_month = (
        MONTH_NAMES.get(
            date_value.month
        )
    )


def _append_changes(
    changes,
    old_budget,
    old_pet,
    old_nights,
    old_dates,
    updated_request,
):
    if old_budget != updated_request.max_budget:
        changes.append(
            {
                "field": "max_budget",
                "old": old_budget,
                "new": updated_request.max_budget,
            }
        )

    if old_pet != updated_request.pet:
        changes.append(
            {
                "field": "pet",
                "old": old_pet,
                "new": updated_request.pet,
            }
        )

    if old_nights != updated_request.nights:
        changes.append(
            {
                "field": "nights",
                "old": old_nights,
                "new": updated_request.nights,
            }
        )

    new_dates = (
        updated_request.start_date,
        updated_request.end_date,
    )

    if old_dates != new_dates:
        changes.append(
            {
                "field": "dates",
                "old": old_dates,
                "new": new_dates,
            }
        )


def update_trip_request(
    trip_request,
    user_message,
):
    updated_request = deepcopy(
        trip_request
    )

    text = normalize_text(
        user_message
    )

    old_budget = (
        updated_request.max_budget
    )

    old_pet = (
        updated_request.pet
    )

    old_nights = (
        updated_request.nights
    )

    old_dates = (
        updated_request.start_date,
        updated_request.end_date,
    )

    changes = []
    clarification = None

    if (
        "бюджет" in text
        or "дороже" in text
        or "тысяч" in text
        or re.search(
            r"\d+\s*к\b",
            text,
        )
    ):
        new_budget = extract_trip_budget(
            user_message
        )

        if new_budget is not None:
            updated_request.max_budget = (
                new_budget
            )

        elif "бюджет" in text:
            clarification = (
                "Какой максимальный бюджет "
                "заложить на поездку?"
            )

    pet_negative_patterns = [
        r"\bбез\s+(?:собаки|кошки|питомца)\b",
        r"\b(?:собака|кошка|питомец)\s+не\s+едет\b",
        r"\bне\s+(?:берем|берём|берем|возьмем|возьмём|брать|везем|везём)\s+"
        r"(?:с\s+собой\s+)?(?:собаку|кошку|питомца)\b",
        r"\b(?:собаку|кошку|питомца)\s+"
        r"(?:не\s+берем|не\s+берём|не\s+возьмем|не\s+возьмём)\b",
    ]

    pet_positive_patterns = [
        r"\bс\s+(?:собакой|кошкой|питомцем)\b",
        r"\bс\s+собой\s+(?:собаку|кошку|питомца)\b",
        r"\b(?:взять|берем|берём|возьмем|возьмём|везем|везём)\s+"
        r"(?:с\s+собой\s+)?(?:собаку|кошку|питомца)\b",
        r"\b(?:едет|поедет)\s+(?:собака|кошка|питомец)\b",
        r"\bс\s+нами\s+(?:собака|кошка|питомец)\b",
        r"\b(?:собака|кошка|питомец)\s+(?:едет|поедет)\s+с\s+нами\b",
    ]

    if any(
        re.search(
            pattern,
            text,
        )
        for pattern in pet_negative_patterns
    ):
        updated_request.pet = False

        updated_request.hotel_hard_filters.pop(
            "pet_friendly",
            None,
        )

    elif any(
        re.search(
            pattern,
            text,
        )
        for pattern in pet_positive_patterns
    ):
        updated_request.pet = True

        updated_request.hotel_hard_filters[
            "pet_friendly"
        ] = 1

    full_date_range = extract_date_range(
        user_message
    )

    date_shift = extract_date_shift(
        user_message
    )

    new_nights = extract_nights(
        user_message
    )

    if full_date_range is not None:
        current_start = parse_date_value(
            updated_request.start_date
        )

        base_year = (
            current_start.year
            if current_start is not None
            else datetime.now().year
        )

        end_year = base_year

        if (
            full_date_range["end_month"]
            < full_date_range["start_month"]
        ):
            end_year += 1

        try:
            new_start = datetime(
                base_year,
                full_date_range["start_month"],
                full_date_range["start_day"],
            )

            new_end = datetime(
                end_year,
                full_date_range["end_month"],
                full_date_range["end_day"],
            )
        except ValueError:
            clarification = (
                "Не удалось распознать новые даты. "
                "Например: «с 12 по 19 ноября»."
            )
        else:
            updated_request.start_date = (
                new_start.strftime(
                    "%Y-%m-%d"
                )
            )

            updated_request.end_date = (
                new_end.strftime(
                    "%Y-%m-%d"
                )
            )

            updated_request.nights = (
                full_date_range[
                    "nights"
                ]
            )

            _set_travel_month_from_date(
                updated_request,
                new_start,
            )

    elif date_shift is not None:
        start_date = parse_date_value(
            updated_request.start_date
        )

        end_date = parse_date_value(
            updated_request.end_date
        )

        if (
            start_date is None
            or end_date is None
        ):
            clarification = (
                "Чтобы сдвинуть поездку "
                "на несколько дней, нужны "
                "точные даты. Какие даты "
                "поездки вы рассматриваете?"
            )
        else:
            new_start = (
                start_date
                + timedelta(
                    days=date_shift
                )
            )

            new_end = (
                end_date
                + timedelta(
                    days=date_shift
                )
            )

            updated_request.start_date = (
                new_start.strftime(
                    "%Y-%m-%d"
                )
            )

            updated_request.end_date = (
                new_end.strftime(
                    "%Y-%m-%d"
                )
            )

            _set_travel_month_from_date(
                updated_request,
                new_start,
            )

    else:
        explicit_start = (
            extract_explicit_start_date(
                user_message,
                reference_date=(
                    updated_request.start_date
                ),
            )
        )

        if explicit_start is not None:
            updated_request.start_date = (
                explicit_start.strftime(
                    "%Y-%m-%d"
                )
            )

            if updated_request.nights is not None:
                new_end = (
                    explicit_start
                    + timedelta(
                        days=int(
                            updated_request.nights
                        )
                    )
                )

                updated_request.end_date = (
                    new_end.strftime(
                        "%Y-%m-%d"
                    )
                )

            else:
                clarification = (
                    "Дата начала изменена. "
                    "На сколько ночей планируется поездка?"
                )

            _set_travel_month_from_date(
                updated_request,
                explicit_start,
            )

        if (
            new_nights is not None
            and (
                updated_request.nights
                != new_nights
            )
        ):
            updated_request.nights = (
                new_nights
            )

            start_date = parse_date_value(
                updated_request.start_date
            )

            if start_date is not None:
                new_end = (
                    start_date
                    + timedelta(
                        days=int(
                            new_nights
                        )
                    )
                )

                updated_request.end_date = (
                    new_end.strftime(
                        "%Y-%m-%d"
                    )
                )

                _set_travel_month_from_date(
                    updated_request,
                    start_date,
                )

    _append_changes(
        changes=changes,
        old_budget=old_budget,
        old_pet=old_pet,
        old_nights=old_nights,
        old_dates=old_dates,
        updated_request=updated_request,
    )

    if clarification is not None:
        return {
            "status": "needs_clarification",
            "trip_request": updated_request,
            "changes": changes,
            "question": clarification,
        }

    if not changes:
        return {
            "status": "no_changes",
            "trip_request": updated_request,
            "changes": [],
            "message": (
                "Я пока не понял, какое "
                "условие поездки нужно изменить."
            ),
        }

    return {
        "status": "updated",
        "trip_request": updated_request,
        "changes": changes,
    }


def replan_agent(
    state,
    user_message,
    destinations,
    transport,
    transfers,
    hotels,
):
    state = deepcopy(state)

    if state.get("trip_request") is None:
        return {
            "state": state,
            "action": "error",
            "message": (
                "Сначала нужно создать "
                "исходный запрос поездки."
            ),
            "result": None,
        }

    update_result = update_trip_request(
        trip_request=state[
            "trip_request"
        ],
        user_message=user_message,
    )

    if (
        update_result["status"]
        == "needs_clarification"
    ):
        return {
            "state": state,
            "action": "ask_question",
            "message": update_result[
                "question"
            ],
            "changes": update_result[
                "changes"
            ],
            "result": state.get(
                "result"
            ),
        }

    if (
        update_result["status"]
        == "no_changes"
    ):
        return {
            "state": state,
            "action": "ask_again",
            "message": update_result[
                "message"
            ],
            "changes": [],
            "result": state.get(
                "result"
            ),
        }

    updated_request = (
        update_result[
            "trip_request"
        ]
    )

    state["trip_request"] = (
        updated_request
    )

    result = build_trip_plans(
        trip_request=updated_request,
        destinations=destinations,
        transport=transport,
        transfers=transfers,
        hotels=hotels,
        top_n=3,
    )

    state["result"] = result

    if result["status"] == "success":
        state["status"] = (
            "recommendations_ready"
        )

        return {
            "state": state,
            "action": "show_recommendations",
            "message": (
                "Условия обновлены. "
                "Я пересобрал поездку."
            ),
            "changes": update_result[
                "changes"
            ],
            "result": result,
        }

    return {
        "state": state,
        "action": "no_results",
        "message": result.get(
            "message",
            (
                "После изменения условий "
                "не удалось собрать поездку."
            ),
        ),
        "changes": update_result[
            "changes"
        ],
        "result": result,
    }
