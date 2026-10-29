
import re
from datetime import date

import pandas as pd

from trip_models import TripRequest


def load_trip_data():
    destinations = pd.read_csv("data/destinations.csv")
    transport = pd.read_csv("data/transport.csv")
    transfers = pd.read_csv("data/transfers.csv")
    return destinations, transport, transfers


def normalize_text(text):
    return str(text).casefold().replace("ё", "е").strip()


def is_warm_sea_request(text):
    """
    True, когда пользователь явно просит именно тёплое море / тёплую воду.
    Порог в демо для ноября: не ниже +23 °C.
    """
    normalized = normalize_text(text)

    patterns = [
        r"\bтепл\w*\s+мор\w*\b",
        r"\bтепл\w*\s+вод\w*\b",
        r"\bмор\w*\s+(?:должн\w*\s+быть\s+)?тепл\w*\b",
        r"\bвод\w*\s+(?:должн\w*\s+быть\s+)?тепл\w*\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


MONTH_FORMS = {
    "январь": 1,
    "января": 1,
    "январе": 1,
    "февраль": 2,
    "февраля": 2,
    "феврале": 2,
    "март": 3,
    "марта": 3,
    "марте": 3,
    "апрель": 4,
    "апреля": 4,
    "апреле": 4,
    "май": 5,
    "мая": 5,
    "мае": 5,
    "июнь": 6,
    "июня": 6,
    "июне": 6,
    "июль": 7,
    "июля": 7,
    "июле": 7,
    "август": 8,
    "августа": 8,
    "августе": 8,
    "сентябрь": 9,
    "сентября": 9,
    "сентябре": 9,
    "октябрь": 10,
    "октября": 10,
    "октябре": 10,
    "ноябрь": 11,
    "ноября": 11,
    "ноябре": 11,
    "декабрь": 12,
    "декабря": 12,
    "декабре": 12,
}

MONTH_NAMES = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


def _calculate_nights(
    start_day,
    start_month,
    end_day,
    end_month,
):
    try:
        start = date(
            2000,
            int(start_month),
            int(start_day),
        )

        end_year = 2000
        if int(end_month) < int(start_month):
            end_year = 2001

        end = date(
            end_year,
            int(end_month),
            int(end_day),
        )
    except ValueError:
        return None

    nights = (end - start).days

    if nights <= 0:
        return None

    return nights


def extract_date_range(text):
    text = normalize_text(text)

    numeric_pattern = re.compile(
        r"(?:\bс\s+)?"
        r"(\d{1,2})[./](\d{1,2})"
        r"(?:[./](\d{2,4}))?"
        r"\s*(?:по|[-–—])\s*"
        r"(\d{1,2})[./](\d{1,2})"
        r"(?:[./](\d{2,4}))?"
    )

    match = numeric_pattern.search(text)

    if match:
        start_day = int(match.group(1))
        start_month = int(match.group(2))
        end_day = int(match.group(4))
        end_month = int(match.group(5))

        nights = _calculate_nights(
            start_day,
            start_month,
            end_day,
            end_month,
        )

        if nights is not None:
            return {
                "start_day": start_day,
                "start_month": start_month,
                "end_day": end_day,
                "end_month": end_month,
                "nights": nights,
                "travel_month": MONTH_NAMES.get(start_month),
            }

    explicit_month_pattern = re.compile(
        r"(?:\bс\s+)?"
        r"(\d{1,2})\s+([а-я]+)"
        r"\s*(?:по|[-–—])\s*"
        r"(\d{1,2})\s+([а-я]+)"
    )

    match = explicit_month_pattern.search(text)

    if match:
        start_day = int(match.group(1))
        start_month = MONTH_FORMS.get(match.group(2))
        end_day = int(match.group(3))
        end_month = MONTH_FORMS.get(match.group(4))

        if start_month and end_month:
            nights = _calculate_nights(
                start_day,
                start_month,
                end_day,
                end_month,
            )

            if nights is not None:
                return {
                    "start_day": start_day,
                    "start_month": start_month,
                    "end_day": end_day,
                    "end_month": end_month,
                    "nights": nights,
                    "travel_month": MONTH_NAMES.get(start_month),
                }

    same_month_pattern = re.compile(
        r"(?:\bс\s+)?"
        r"(\d{1,2})"
        r"\s*(?:по|[-–—])\s*"
        r"(\d{1,2})\s+([а-я]+)"
    )

    match = same_month_pattern.search(text)

    if match:
        start_day = int(match.group(1))
        end_day = int(match.group(2))
        month = MONTH_FORMS.get(match.group(3))

        if month:
            nights = _calculate_nights(
                start_day,
                month,
                end_day,
                month,
            )

            if nights is not None:
                return {
                    "start_day": start_day,
                    "start_month": month,
                    "end_day": end_day,
                    "end_month": month,
                    "nights": nights,
                    "travel_month": MONTH_NAMES.get(month),
                }

    return None


def extract_travel_month(text):
    date_range = extract_date_range(text)

    if date_range is not None:
        return date_range["travel_month"]

    normalized = normalize_text(text)

    for form, month_number in MONTH_FORMS.items():
        if re.search(
            rf"\b{re.escape(form)}\b",
            normalized,
        ):
            return MONTH_NAMES[month_number]

    return None


def extract_destination_city(text):
    normalized = normalize_text(text)

    destinations_map = {
        "Сочи": [
            r"сочи",
        ],
        "Анталья": [
            r"анталья",
            r"анталью",
            r"анталье",
            r"антальи",
        ],
        "Дубай": [
            r"дубай",
            r"дубае",
            r"дубая",
        ],
        "Калининград": [
            r"калининград",
            r"калининграде",
            r"калининграда",
        ],
        "Казань": [
            r"казань",
            r"казани",
            r"казанью",
        ],
    }

    for city, forms in destinations_map.items():
        for form in forms:
            if re.search(
                rf"\b(?:в|во|на)\s+{form}\b",
                normalized,
            ):
                return city

    for city, forms in destinations_map.items():
        for form in forms:
            city_found = re.search(
                rf"\b{form}\b",
                normalized,
            )

            origin_found = re.search(
                rf"\bиз\s+{form}\b",
                normalized,
            )

            if city_found and not origin_found:
                return city

    return None



def extract_trip_budget(text):
    text = normalize_text(text)

    patterns = [
        (
            r"(?:бюджет(?:ом)?(?:\s+до)?|до|не\s+дороже|максимум)"
            r"\s*(\d+(?:\s\d{3})*(?:[.,]\d+)?)"
            r"\s*(тыс(?:яч[аиу]?)?\.?|к)?\b"
        ),
        (
            r"\b(\d+(?:\s\d{3})*(?:[.,]\d+)?)"
            r"\s*(тыс(?:яч[аиу]?)?\.?|к)\b"
        ),
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        number = match.group(1).replace(" ", "").replace(",", ".")
        try:
            value = float(number)
        except ValueError:
            continue

        suffix = match.group(2)
        if suffix:
            suffix = normalize_text(suffix)
            if suffix.startswith("тыс") or suffix == "к":
                value *= 1000

        return int(value)

    return None


def extract_nights(text):
    date_range = extract_date_range(text)

    if date_range is not None:
        return date_range["nights"]

    text = normalize_text(text)

    match = re.search(
        r"на\s+(\d+)\s+(?:ноч|дн)",
        text,
    )
    if match:
        return int(match.group(1))

    if "на две недели" in text or "две недели" in text:
        return 14

    if "на неделю" in text or "неделю" in text:
        return 7

    return None


def extract_origin_city(text, transport):
    normalized_text = normalize_text(text)

    origin_cities = (
        transport["origin_city"]
        .dropna()
        .astype(str)
        .unique()
    )

    for city in origin_cities:
        normalized_city = normalize_text(city)

        if normalized_city in normalized_text:
            return city

        if city == "Москва" and (
            "москвы" in normalized_text
            or "москве" in normalized_text
        ):
            return city

        if city == "Ростов-на-Дону" and (
            "ростова-на-дону" in normalized_text
            or "ростове-на-дону" in normalized_text
        ):
            return city

        if city == "Санкт-Петербург" and (
            "санкт-петербурга" in normalized_text
            or "санкт-петербурге" in normalized_text
            or "питера" in normalized_text
        ):
            return city

    return None



PEOPLE_COUNT_WORDS = {
    "один": 1,
    "одна": 1,
    "одного": 1,
    "одной": 1,
    "два": 2,
    "две": 2,
    "двое": 2,
    "двух": 2,
    "двумя": 2,
    "три": 3,
    "трое": 3,
    "трех": 3,
    "тремя": 3,
    "четыре": 4,
    "четверо": 4,
    "четырех": 4,
    "четырьмя": 4,
    "пять": 5,
    "пятеро": 5,
    "пяти": 5,
    "шесть": 6,
    "шестеро": 6,
    "шести": 6,
    "семь": 7,
    "семеро": 7,
    "семи": 7,
    "восемь": 8,
    "восьмеро": 8,
    "восьми": 8,
    "девять": 9,
    "девятеро": 9,
    "девяти": 9,
    "десять": 10,
    "десятеро": 10,
    "десяти": 10,
}


def extract_people_count_answer(text):
    """
    Число людей из короткого уточняющего ответа:
    "2", "2 взрослых", "двое", "трое детей".
    """
    normalized = normalize_text(text)

    digit_match = re.search(
        r"\b(\d{1,2})\b",
        normalized,
    )

    if digit_match:
        value = int(
            digit_match.group(1)
        )

        if 1 <= value <= 20:
            return value

    for word, value in (
        PEOPLE_COUNT_WORDS.items()
    ):
        if re.search(
            rf"\b{re.escape(word)}\b",
            normalized,
        ):
            return value

    return None


def _extract_count_before_noun(
    text,
    noun_pattern,
):
    digit_match = re.search(
        rf"\b(\d{{1,2}})\s+{noun_pattern}\b",
        text,
    )

    if digit_match:
        value = int(
            digit_match.group(1)
        )

        if 1 <= value <= 20:
            return value

    for word, value in (
        PEOPLE_COUNT_WORDS.items()
    ):
        if re.search(
            rf"\b{re.escape(word)}\s+{noun_pattern}\b",
            text,
        ):
            return value

    return None


def extract_travel_party(text):
    """
    Возвращает состав группы и признаки,
    нужно ли уточнять количество взрослых/детей.

    Логика демо:
    - "хочу / еду / поеду" -> 1 взрослый;
    - "хотим / едем / поедем / мы ..." без числа
      -> количество взрослых нужно уточнить;
    - "с ребёнком" -> 1 ребёнок;
    - "с детьми" без числа -> количество детей
      нужно уточнить;
    - явные количества имеют приоритет.
    """
    normalized = normalize_text(text)

    explicit_adults = (
        _extract_count_before_noun(
            normalized,
            r"(?:взросл\w*|совершеннолетн\w*)",
        )
    )

    explicit_children = (
        _extract_count_before_noun(
            normalized,
            r"(?:ребен\w*|дет\w*)",
        )
    )

    plural_adult_cues = [
        r"\bмы\b",
        r"\bхотим\b",
        r"\bхотят\b",
        r"\bедем\b",
        r"\bедут\b",
        r"\bпоедем\b",
        r"\bпоедут\b",
        r"\bлетим\b",
        r"\bлетят\b",
        r"\bполетим\b",
        r"\bполетят\b",
        r"\bпланируем\b",
        r"\bпланируют\b",
        r"\bсобираемся\b",
        r"\bсобираются\b",
        r"\bпутешествуем\b",
        r"\bпутешествуют\b",
    ]

    if explicit_adults is not None:
        adults = explicit_adults
        adults_count_known = True
    else:
        plural_adults = any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in plural_adult_cues
        )

        adults = 1
        adults_count_known = (
            not plural_adults
        )

    no_children_patterns = [
        r"\bбез\s+дет\w*\b",
        r"\bдет\w*\s+не\s+ед\w*\b",
    ]

    if explicit_children is not None:
        children = explicit_children
        children_count_known = True

    elif any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in no_children_patterns
    ):
        children = 0
        children_count_known = True

    elif re.search(
        r"\bс\s+детьми\b",
        normalized,
    ):
        children = 0
        children_count_known = False

    elif re.search(
        r"\bс\s+ребенком\b",
        normalized,
    ) or re.search(
        r"\bребенок\s+едет\b",
        normalized,
    ):
        children = 1
        children_count_known = True

    else:
        children = 0
        children_count_known = True

    return {
        "adults": adults,
        "children": children,
        "adults_count_known": (
            adults_count_known
        ),
        "children_count_known": (
            children_count_known
        ),
    }


def extract_child_ages_from_text(text):
    """
    Извлекает возраста детей из естественной фразы,
    если они указаны рядом с упоминанием детей.

    Поддерживает, например:
    - "ребёнку 5 лет"
    - "с ребёнком 5 лет"
    - "дети 1, 5 и 9 лет"
    - "детям 1, 5 и 9 лет"
    """
    normalized = normalize_text(text)

    if not re.search(
        r"\b(?:ребен\w*|дет\w*)\b",
        normalized,
    ):
        return []

    single = re.search(
        r"(?:ребен\w*|с\s+ребен\w*)"
        r"[^\d]{0,12}(\d{1,2})\s*"
        r"(?:год|года|лет)\b",
        normalized,
    )

    if single:
        age = int(single.group(1))
        if 0 <= age <= 17:
            return [age]

    group = re.search(
        r"(?:детям|дети|возраст\w*\s+дет\w*)"
        r"[^\d]{0,12}"
        r"([\d\s,;и]+?)\s*"
        r"(?:год|года|лет)\b",
        normalized,
    )

    if group:
        ages = [
            int(value)
            for value in re.findall(
                r"\d{1,2}",
                group.group(1),
            )
        ]

        if (
            ages
            and all(0 <= age <= 17 for age in ages)
        ):
            return ages

    return []


def extract_child_ages_answer(text):
    """
    Разбирает ответ на уточнение возраста детей.
    Примеры: "5", "5 лет", "1, 5 и 9 лет".
    """
    values = [
        int(value)
        for value in re.findall(
            r"\d{1,2}",
            normalize_text(text),
        )
    ]

    if not values:
        return []

    if not all(0 <= age <= 17 for age in values):
        return []

    return values


def _round_money(value, step=100):
    return int(
        round(float(value) / step)
        * step
    )


def _base_adult_price(row):
    value = row.get(
        "adult_price",
        None,
    )

    if value is not None and not pd.isna(value):
        return int(value)

    legacy = int(
        row.get(
            "price_total",
            0,
        )
        or 0
    )

    return max(
        1,
        int(round(legacy / 2)),
    )


def calculate_transport_pricing(
    transport_row,
    trip_request,
):
    """
    Синтетическая демо-модель тарифа:
    взрослый / ребёнок 12+ = 100%,
    ребёнок 2–11 = 75%,
    младенец до 2 = 10%.
    """
    adult_unit = _base_adult_price(
        transport_row
    )
    child_unit = _round_money(
        adult_unit * 0.75
    )
    infant_unit = _round_money(
        adult_unit * 0.10
    )

    adults = max(
        1,
        int(trip_request.adults or 1),
    )

    ages = list(
        trip_request.child_ages or []
    )

    if len(ages) != int(trip_request.children or 0):
        ages = [6] * int(
            trip_request.children or 0
        )

    child_12_plus = sum(
        age >= 12
        for age in ages
    )
    child_2_11 = sum(
        2 <= age <= 11
        for age in ages
    )
    infants = sum(
        age < 2
        for age in ages
    )

    total = (
        adults * adult_unit
        + child_12_plus * adult_unit
        + child_2_11 * child_unit
        + infants * infant_unit
    )

    breakdown = []

    if adults:
        breakdown.append(
            f"взрослых: {adults} × "
            f"{adult_unit:,} ₽".replace(",", " ")
        )

    if child_12_plus:
        breakdown.append(
            f"детей 12+: {child_12_plus} × "
            f"{adult_unit:,} ₽ по взрослому тарифу"
            .replace(",", " ")
        )

    if child_2_11:
        breakdown.append(
            f"детей 2–11 лет: {child_2_11} × "
            f"{child_unit:,} ₽"
            .replace(",", " ")
        )

    if infants:
        breakdown.append(
            f"младенцев до 2 лет: {infants} × "
            f"{infant_unit:,} ₽"
            .replace(",", " ")
        )

    return {
        "total": int(total),
        "adult_unit_price": adult_unit,
        "child_unit_price": child_unit,
        "infant_unit_price": infant_unit,
        "fare_breakdown": breakdown,
    }


def calculate_transfer_pricing(
    transfer_row,
    trip_request,
):
    """
    Синтетическая демо-модель трансфера:
    взрослый / ребёнок 12+ = 100%,
    ребёнок 2–11 = 50%,
    младенец до 2 = бесплатно.
    """
    if transfer_row is None:
        return {
            "total": 0,
            "adult_unit_price": 0,
            "child_unit_price": 0,
            "infant_unit_price": 0,
            "fare_breakdown": [],
        }

    adult_unit = _base_adult_price(
        transfer_row
    )
    child_unit = _round_money(
        adult_unit * 0.50,
        step=25,
    )
    infant_unit = 0

    adults = max(
        1,
        int(trip_request.adults or 1),
    )

    ages = list(
        trip_request.child_ages or []
    )

    if len(ages) != int(trip_request.children or 0):
        ages = [6] * int(
            trip_request.children or 0
        )

    child_12_plus = sum(
        age >= 12
        for age in ages
    )
    child_2_11 = sum(
        2 <= age <= 11
        for age in ages
    )
    infants = sum(
        age < 2
        for age in ages
    )

    total = (
        adults * adult_unit
        + child_12_plus * adult_unit
        + child_2_11 * child_unit
    )

    breakdown = []

    if adults:
        breakdown.append(
            f"взрослых: {adults} × "
            f"{adult_unit:,} ₽".replace(",", " ")
        )

    if child_12_plus:
        breakdown.append(
            f"детей 12+: {child_12_plus} × "
            f"{adult_unit:,} ₽ по взрослому тарифу"
            .replace(",", " ")
        )

    if child_2_11:
        breakdown.append(
            f"детей 2–11 лет: {child_2_11} × "
            f"{child_unit:,} ₽"
            .replace(",", " ")
        )

    if infants:
        breakdown.append(
            f"младенцев до 2 лет: {infants} × 0 ₽"
        )

    return {
        "total": int(total),
        "adult_unit_price": adult_unit,
        "child_unit_price": child_unit,
        "infant_unit_price": infant_unit,
        "fare_breakdown": breakdown,
    }


def parse_trip_request_basic(user_text, transport):
    text = normalize_text(user_text)

    origin_city = extract_origin_city(
        user_text,
        transport,
    )
    destination_city = extract_destination_city(
        user_text
    )
    max_budget = extract_trip_budget(user_text)

    date_range = extract_date_range(
        user_text
    )

    if date_range is not None:
        nights = date_range["nights"]
        travel_month = date_range["travel_month"]

        today = date.today()

        start_year = today.year
        start_candidate = date(
            start_year,
            date_range["start_month"],
            date_range["start_day"],
        )

        if start_candidate < today:
            start_year += 1

        end_year = start_year

        if (
            date_range["end_month"]
            < date_range["start_month"]
        ):
            end_year += 1

        start_date = date(
            start_year,
            date_range["start_month"],
            date_range["start_day"],
        ).isoformat()

        end_date = date(
            end_year,
            date_range["end_month"],
            date_range["end_day"],
        ).isoformat()

    else:
        nights = extract_nights(user_text)
        travel_month = extract_travel_month(user_text)
        start_date = None
        end_date = None

    sea_required = None
    if "мор" in text or "пляж" in text:
        sea_required = True

    warm_weather = None
    warm_phrases = [
        "тепл",
        "жарк",
        "погреться",
        "солнц",
    ]
    if any(
        phrase in text
        for phrase in warm_phrases
    ):
        warm_weather = True

    party = extract_travel_party(
        user_text
    )

    adults = party[
        "adults"
    ]

    children = party[
        "children"
    ]

    adults_count_known = party[
        "adults_count_known"
    ]

    children_count_known = party[
        "children_count_known"
    ]

    child_ages = extract_child_ages_from_text(
        user_text
    )

    if len(child_ages) != children:
        child_ages = []

    max_travel_hours = None
    long_trip_phrases = [
        "без долгих перелетов",
        "без долгих перелётов",
        "недолго лететь",
        "не хочется долго лететь",
        "недолгая дорога",
    ]
    if any(
        phrase in text
        for phrase in long_trip_phrases
    ):
        max_travel_hours = 6.0

    missing_critical_info = []
    if origin_city is None:
        missing_critical_info.append(
            "origin_city"
        )

    return TripRequest(
        raw_text=user_text,
        origin_city=origin_city,
        destination_city=destination_city,
        start_date=start_date,
        end_date=end_date,
        travel_month=travel_month,
        nights=nights,
        adults=adults,
        children=children,
        adults_count_known=(
            adults_count_known
        ),
        children_count_known=(
            children_count_known
        ),
        child_ages=child_ages,
        max_budget=max_budget,
        warm_weather=warm_weather,
        sea_required=sea_required,
        max_travel_hours=max_travel_hours,
        missing_critical_info=missing_critical_info,
    )


def find_best_transport(
    origin_city,
    destination_city,
    transport,
    max_travel_hours=None,
):
    options = transport[
        (transport["origin_city"] == origin_city)
        & (transport["destination_city"] == destination_city)
    ].copy()

    if options.empty:
        return None

    if max_travel_hours is not None:
        within_limit = options[
            options["duration_hours"] <= max_travel_hours
        ]
        if not within_limit.empty:
            options = within_limit

    price_column = (
        "adult_price"
        if "adult_price" in options.columns
        else "price_total"
    )

    options = options.sort_values(
        by=[price_column, "duration_hours"],
        ascending=[True, True],
    )

    return options.iloc[0]


def find_transfer(destination_city, transfers):
    options = transfers[
        transfers["city"] == destination_city
    ]

    if options.empty:
        return None

    price_column = (
        "adult_price"
        if "adult_price" in options.columns
        else "price_total"
    )

    return options.sort_values(
        by=price_column
    ).iloc[0]


def recommend_destinations(
    trip_request,
    destinations,
    transport,
    transfers,
    top_n=3,
):
    if trip_request.origin_city is None:
        return {
            "status": "needs_clarification",
            "question": "Из какого города вы планируете отправляться?",
            "missing_field": "origin_city",
            "options": None,
        }

    warm_sea_required = is_warm_sea_request(
        trip_request.raw_text
    )

    if trip_request.destination_city:
        destinations = destinations[
            destinations["city"]
            .astype(str)
            .str.casefold()
            == str(
                trip_request.destination_city
            ).casefold()
        ].copy()

        if destinations.empty:
            return {
                "status": "no_results",
                "message": (
                    "Указанное направление отсутствует "
                    "в текущем демо-наборе данных."
                ),
                "options": [],
            }

    candidates = []

    for _, destination in destinations.iterrows():
        city = destination["city"]

        if (
            trip_request.sea_required is True
            and destination["sea"] != 1
        ):
            continue

        sea_temp = None

        if (
            warm_sea_required
            and trip_request.travel_month == "ноябрь"
        ):
            raw_sea_temp = destination.get(
                "november_sea_temp_c"
            )

            if (
                raw_sea_temp is None
                or pd.isna(raw_sea_temp)
            ):
                continue

            sea_temp = float(
                raw_sea_temp
            )

            if sea_temp < 23:
                continue

        best_transport = find_best_transport(
            origin_city=trip_request.origin_city,
            destination_city=city,
            transport=transport,
            max_travel_hours=trip_request.max_travel_hours,
        )

        if best_transport is None:
            continue

        transfer = find_transfer(city, transfers)
        transfer_pricing = calculate_transfer_pricing(
            transfer,
            trip_request,
        )

        transfer_price = int(
            transfer_pricing["total"]
        )

        nights = trip_request.nights if trip_request.nights is not None else 7
        stay_estimate = int(
            destination["estimated_daily_budget"] * nights
        )
        transport_pricing = calculate_transport_pricing(
            best_transport,
            trip_request,
        )

        transport_price = int(
            transport_pricing["total"]
        )

        estimated_total = (
            stay_estimate
            + transport_price
            + transfer_price
        )

        score = 50.0
        reasons = []
        tradeoffs = []
        destination_warnings = []

        if trip_request.warm_weather is True:
            if destination["warm_weather"] == 1:
                score += 20
                reasons.append("тёплая погода")
            else:
                score -= 20
                tradeoffs.append(
                    "погода может быть прохладнее желаемой"
                )

        if trip_request.sea_required is True:
            if destination["sea"] == 1:
                score += 15
                reasons.append("есть морской отдых")

        if sea_temp is not None:
            sea_temp_text = (
                f"+{sea_temp:g} °C"
            )

            reasons.append(
                f"море в ноябре около {sea_temp_text}"
            )

            if sea_temp == 23:
                destination_warnings.append(
                    "Температура моря около +23 °C — "
                    "это нижняя граница заданного условия "
                    "«тёплое море»."
                )
            else:
                score += 10

        if trip_request.children > 0:
            family_score = int(destination["family_score"])
            score += family_score / 5 * 15
            if family_score >= 4:
                reasons.append(
                    "подходит для отдыха с ребёнком"
                )

        duration = float(best_transport["duration_hours"])

        if trip_request.max_travel_hours is not None:
            if duration <= trip_request.max_travel_hours:
                score += 10
                reasons.append(
                    f"дорога около {duration:g} ч"
                )
            else:
                score -= 15
                tradeoffs.append(
                    f"дорога около {duration:g} ч"
                )

        if trip_request.max_budget is not None:
            if estimated_total <= trip_request.max_budget:
                score += 15
                reasons.append(
                    "укладывается в ориентировочный бюджет"
                )
            else:
                overspend = (
                    estimated_total
                    - trip_request.max_budget
                )
                score -= 25
                tradeoffs.append(
                    (
                        f"ориентировочно выше бюджета "
                        f"на {overspend:,} ₽"
                    ).replace(",", " ")
                )

        if (
            trip_request.travel_month == "ноябрь"
            and trip_request.warm_weather is True
        ):
            november_temp = int(
                destination["november_temp_c"]
            )

            if november_temp >= 20:
                score += 10
                reasons.append(
                    f"в ноябре около +{november_temp} °C"
                )
            else:
                score -= 10
                tradeoffs.append(
                    f"в ноябре около +{november_temp} °C"
                )

        score = max(0, min(score, 100))

        candidates.append(
            {
                "destination_id": destination["destination_id"],
                "city": city,
                "country": destination["country"],
                "match_score": round(score, 1),
                "estimated_total": estimated_total,
                "temperature": int(
                    destination["november_temp_c"]
                ),
                "sea_temperature": (
                    sea_temp
                    if sea_temp is not None
                    else destination.get(
                        "november_sea_temp_c"
                    )
                ),
                "warnings": destination_warnings,
                "transport_type": best_transport["transport_type"],
                "travel_hours": duration,
                "transport_price": transport_price,
                "transfer_price": transfer_price,
                "reasons": reasons,
                "tradeoffs": tradeoffs,
                "description": destination["description"],
            }
        )

    if not candidates:
        return {
            "status": "no_results",
            "message": (
                "Не удалось найти направление, которое "
                "подходит под заданные ограничения."
            ),
            "options": [],
        }

    result = pd.DataFrame(candidates)
    result = (
        result.sort_values(
            by=["match_score", "estimated_total"],
            ascending=[False, True],
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return {
        "status": "success",
        "options": result,
    }


