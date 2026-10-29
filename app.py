
import streamlit as st

from trip_engine import (
    load_trip_data
)

from trip_planner import (
    load_trip_hotels
)

from agent_flow import (
    start_agent,
    continue_agent,
    create_agent_state
)

from replan_logic import (
    replan_agent
)

from checkout_logic import (
    select_plan,
    mock_checkout
)


# ===================================
# НАСТРОЙКИ СТРАНИЦЫ
# ===================================

st.set_page_config(
    page_title="StayMatch",
    page_icon="✈️",
    layout="centered"
)


# ===================================
# ЗАГРУЗКА ДАННЫХ
# ===================================

@st.cache_data
def load_data():

    (
        destinations,
        transport,
        transfers
    ) = load_trip_data()

    hotels = (
        load_trip_hotels()
    )

    return (
        destinations,
        transport,
        transfers,
        hotels
    )


(
    destinations,
    transport,
    transfers,
    hotels
) = load_data()


# ===================================
# SESSION STATE
# ===================================

if "agent_state" not in st.session_state:

    st.session_state.agent_state = (
        create_agent_state()
    )


if "messages" not in st.session_state:

    st.session_state.messages = []


if "latest_result" not in st.session_state:

    st.session_state.latest_result = None


if "cart" not in st.session_state:

    st.session_state.cart = None


if "order" not in st.session_state:

    st.session_state.order = None


# ===================================
# СБРОС
# ===================================

def reset_trip():

    st.session_state.agent_state = (
        create_agent_state()
    )

    st.session_state.messages = []

    st.session_state.latest_result = None

    st.session_state.cart = None

    st.session_state.order = None


# ===================================
# ФОРМАТ ПЕРИОДА ПОЕЗДКИ
# ===================================

def get_trip_value(
    source,
    field,
    default=None
):

    if source is None:

        return default


    if isinstance(
        source,
        dict
    ):

        return source.get(
            field,
            default
        )


    return getattr(
        source,
        field,
        default
    )


def format_nights(
    nights
):

    if nights is None:

        return None


    nights = int(
        nights
    )


    last_two = (
        nights % 100
    )

    last_one = (
        nights % 10
    )


    if (
        11 <= last_two <= 14
    ):

        word = "ночей"

    elif last_one == 1:

        word = "ночь"

    elif (
        2 <= last_one <= 4
    ):

        word = "ночи"

    else:

        word = "ночей"


    return (
        f"{nights} {word}"
    )


def format_travelers(
    source
):

    adults = get_trip_value(
        source,
        "adults",
        1,
    )

    children = get_trip_value(
        source,
        "children",
        0,
    )

    adults = int(
        adults or 1
    )

    children = int(
        children or 0
    )


    adult_last_two = (
        adults % 100
    )

    adult_last_one = (
        adults % 10
    )


    if (
        11 <= adult_last_two <= 14
    ):

        adult_word = "взрослых"

    elif adult_last_one == 1:

        adult_word = "взрослый"

    else:

        adult_word = "взрослых"


    parts = [
        f"{adults} {adult_word}"
    ]


    if children > 0:

        child_last_two = (
            children % 100
        )

        child_last_one = (
            children % 10
        )


        if (
            11 <= child_last_two <= 14
        ):

            child_word = "детей"

        elif child_last_one == 1:

            child_word = "ребёнок"

        elif (
            2 <= child_last_one <= 4
        ):

            child_word = "ребёнка"

        else:

            child_word = "детей"


        child_text = (
            f"{children} {child_word}"
        )

        child_ages = list(
            get_trip_value(
                source,
                "child_ages",
                [],
            )
            or []
        )

        if len(child_ages) == children:
            ages_text = ", ".join(
                str(age)
                for age in child_ages
            )

            child_text += (
                f" ({ages_text} лет)"
            )

        parts.append(
            child_text
        )


    return " · ".join(
        parts
    )


def format_rooms(
    count
):

    count = int(
        count or 1
    )

    last_two = (
        count % 100
    )

    last_one = (
        count % 10
    )


    if (
        11 <= last_two <= 14
    ):

        word = "номеров"

    elif last_one == 1:

        word = "номер"

    elif (
        2 <= last_one <= 4
    ):

        word = "номера"

    else:

        word = "номеров"


    return (
        f"{count} {word}"
    )


RUSSIAN_MONTHS_GENITIVE = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def parse_date_value(
    value
):

    if value is None:

        return None


    if (
        hasattr(value, "year")
        and hasattr(value, "month")
        and hasattr(value, "day")
    ):

        return value


    text = str(
        value
    ).strip()


    if not text:

        return None


    try:

        from datetime import datetime

        return datetime.fromisoformat(
            text
        ).date()

    except ValueError:

        return None


def format_exact_date_range(
    start_date,
    end_date
):

    start = parse_date_value(
        start_date
    )

    end = parse_date_value(
        end_date
    )


    if (
        start is None
        or end is None
    ):

        return None


    if (
        start.year == end.year
        and start.month == end.month
    ):

        return (
            f"{start.day}–{end.day} "
            f"{RUSSIAN_MONTHS_GENITIVE[end.month]}"
        )


    if start.year == end.year:

        return (
            f"{start.day} "
            f"{RUSSIAN_MONTHS_GENITIVE[start.month]} – "
            f"{end.day} "
            f"{RUSSIAN_MONTHS_GENITIVE[end.month]}"
        )


    return (
        f"{start.day} "
        f"{RUSSIAN_MONTHS_GENITIVE[start.month]} "
        f"{start.year} – "
        f"{end.day} "
        f"{RUSSIAN_MONTHS_GENITIVE[end.month]} "
        f"{end.year}"
    )


def format_trip_period(
    source
):

    if source is None:

        return None


    nights = get_trip_value(
        source,
        "nights"
    )

    start_date = get_trip_value(
        source,
        "start_date"
    )

    end_date = get_trip_value(
        source,
        "end_date"
    )

    travel_month = get_trip_value(
        source,
        "travel_month"
    )


    nights_text = (
        format_nights(
            nights
        )
    )


    exact_period = (
        format_exact_date_range(
            start_date,
            end_date
        )
    )


    parts = []


    if exact_period:

        parts.append(
            exact_period
        )

    elif travel_month:

        parts.append(
            str(
                travel_month
            ).capitalize()
        )


    if nights_text:

        parts.append(
            nights_text
        )


    if not parts:

        return None


    return " · ".join(
        parts
    )


def get_current_trip_request():

    state = (
        st.session_state
        .agent_state
    )


    if not isinstance(
        state,
        dict
    ):

        return None


    return (
        state.get(
            "trip_request"
        )
        or state.get(
            "request"
        )
    )


# ===================================
# ФОРМАТ ИЗМЕНЕНИЙ
# ===================================

def format_changes(
    changes
):

    if not changes:

        return ""


    lines = []


    labels = {
        "max_budget": "Бюджет",
        "pet": "Питомец",
        "nights": "Длительность",
        "dates": "Даты"
    }


    for change in changes:

        field = (
            change.get(
                "field"
            )
        )


        label = (
            labels.get(
                field,
                field
            )
        )


        old_value = (
            change.get(
                "old"
            )
        )


        new_value = (
            change.get(
                "new"
            )
        )


        if field == "max_budget":

            if old_value is None:

                old_text = (
                    "не был указан"
                )

            else:

                old_text = (
                    f"{int(old_value):,} ₽"
                    .replace(",", " ")
                )


            new_text = (
                f"{int(new_value):,} ₽"
                .replace(",", " ")
            )


        elif field == "pet":

            old_text = (
                "да"
                if old_value
                else "нет"
            )

            new_text = (
                "да"
                if new_value
                else "нет"
            )


        elif field == "dates":

            def format_changed_dates(
                value
            ):

                if (
                    isinstance(
                        value,
                        (list, tuple)
                    )
                    and len(value) >= 2
                ):

                    formatted = (
                        format_exact_date_range(
                            value[0],
                            value[1]
                        )
                    )

                    if formatted:

                        return formatted


                return str(
                    value
                )


            old_text = (
                format_changed_dates(
                    old_value
                )
            )

            new_text = (
                format_changed_dates(
                    new_value
                )
            )


        elif field == "nights":

            old_text = (
                format_nights(
                    old_value
                )
                or str(
                    old_value
                )
            )

            new_text = (
                format_nights(
                    new_value
                )
                or str(
                    new_value
                )
            )


        else:

            old_text = str(
                old_value
            )

            new_text = str(
                new_value
            )


        lines.append(
            f"• **{label}:** "
            f"{old_text} → {new_text}"
        )


    return "\n".join(
        lines
    )


# ===================================
# ЗАГОЛОВОК
# ===================================

st.title(
    "✈️ StayMatch"
)


st.write(
    "Расскажите о поездке своими словами. "
    "StayMatch уточнит только необходимое, "
    "сравнит направления и соберёт "
    "готовые варианты поездки."
)


st.caption(
    "Демо-версия использует "
    "синтетические данные. "
    "Бронирование и оплата имитируются."
)


# ===================================
# НОВАЯ ПОЕЗДКА
# ===================================

if st.button(
    "Начать новую поездку"
):

    reset_trip()

    st.rerun()


# ===================================
# ИСТОРИЯ ДИАЛОГА
# ===================================

for message in (
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ===================================
# TOP-3
# ===================================

def show_trip_plans(
    result
):

    if (
        result is None
        or result.get(
            "status"
        )
        != "success"
    ):

        return


    plans = (
        result["plans"]
    )


    trip_request = (
        get_current_trip_request()
    )


    period_text = (
        format_trip_period(
            trip_request
        )
    )


    st.subheader(
        "Подобранные поездки"
    )


    if period_text:

        st.caption(
            f"📅 Период поездки: "
            f"{period_text}"
        )


    travelers_text = (
        format_travelers(
            trip_request
        )
    )


    if travelers_text:

        st.caption(
            f"👥 Путешественники: "
            f"{travelers_text}"
        )


    for position, plan in enumerate(
        plans,
        start=1
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {position}. "
                f"{plan.destination_city}"
            )


            col1, col2 = (
                st.columns(2)
            )


            with col1:

                st.metric(
                    "Соответствие",
                    f"{plan.match_score}%"
                )


            with col2:

                st.metric(
                    "Стоимость",
                    (
                        f"{plan.total_price:,} ₽"
                        .replace(",", " ")
                    )
                )


            # -----------------------------------
            # ДОРОГА
            # -----------------------------------

            st.markdown(
                "#### ✈️ Дорога"
            )


            st.write(
                f"{plan.transport.transport_type}: "
                f"{plan.transport.origin_city} → "
                f"{plan.transport.destination_city}"
            )


            st.write(
                f"{plan.transport.departure_time} → "
                f"{plan.transport.arrival_time}"
            )


            st.write(
                f"В пути: "
                f"{plan.transport.duration_hours:g} ч"
            )


            st.write(
                f"{plan.transport_price:,} ₽"
                .replace(",", " ")
            )


            if plan.transport.fare_breakdown:

                st.caption(
                    "Демо-тарифы: "
                    + " · ".join(
                        plan.transport.fare_breakdown
                    )
                )


            # -----------------------------------
            # ОТЕЛЬ
            # -----------------------------------

            st.markdown(
                "#### 🏨 Отель"
            )


            st.write(
                f"**{plan.hotel.hotel_name}**"
            )


            st.write(
                f"Match отеля: "
                f"{plan.hotel.match_score}%"
            )


            hotel_price_text = (
                f"{plan.hotel_price:,} ₽"
                .replace(",", " ")
            )


            nights_text = (
                format_nights(
                    get_trip_value(
                        trip_request,
                        "nights"
                    )
                )
            )


            rooms_required = int(
                getattr(
                    plan.hotel,
                    "rooms_required",
                    1,
                )
                or 1
            )


            rooms_text = (
                format_rooms(
                    rooms_required
                )
            )


            if nights_text:

                st.write(
                    f"{hotel_price_text} "
                    f"· {rooms_text} "
                    f"· {nights_text}"
                )

            else:

                st.write(
                    f"{hotel_price_text} "
                    f"· {rooms_text}"
                )


            if rooms_required > 1:

                price_per_room = int(
                    getattr(
                        plan.hotel,
                        "price_per_room",
                        0,
                    )
                    or 0
                )

                room_capacity = int(
                    getattr(
                        plan.hotel,
                        "room_capacity",
                        0,
                    )
                    or 0
                )


                details = []

                if price_per_room > 0:

                    details.append(
                        (
                            f"{price_per_room:,} ₽ "
                            f"за номер"
                        ).replace(
                            ",",
                            " "
                        )
                    )

                if room_capacity > 0:

                    details.append(
                        f"до {room_capacity} "
                        f"гостей в номере"
                    )


                if details:

                    st.caption(
                        " · ".join(
                            details
                        )
                    )


            st.markdown(
                "**Почему подходит**"
            )


            st.write(
                plan.hotel.strengths
            )


            # -----------------------------------
            # ЧТО ВАЖНО УЧЕСТЬ
            # -----------------------------------

            considerations = []

            tradeoffs_text = str(
                plan.hotel.tradeoffs
                or ""
            ).strip()

            empty_tradeoff_phrases = {
                "",
                "существенных компромиссов нет",
                "нет существенных компромиссов",
            }

            if (
                tradeoffs_text.casefold()
                not in empty_tradeoff_phrases
            ):
                tradeoff_items = [
                    item.strip()
                    for item in tradeoffs_text.split(
                        " • "
                    )
                    if item.strip()
                ]

                considerations.extend(
                    tradeoff_items
                )

            if plan.warnings:
                considerations.extend(
                    [
                        str(item).strip()
                        for item in plan.warnings
                        if str(item).strip()
                    ]
                )

            if considerations:
                st.markdown(
                    "**Что важно учесть**"
                )

                for item in considerations:
                    st.write(
                        f"• {item}"
                    )


            # -----------------------------------
            # ТРАНСФЕР
            # -----------------------------------

            if (
                plan.transfer
                is not None
            ):

                st.markdown(
                    "#### 🚕 Трансфер"
                )


                st.write(
                    f"{plan.transfer.transfer_type} "
                    f"· "
                    f"{plan.transfer.duration_minutes} мин."
                )


                st.write(
                    f"{plan.transfer_price:,} ₽"
                    .replace(",", " ")
                )


                if plan.transfer.fare_breakdown:

                    st.caption(
                        "Демо-тарифы: "
                        + " · ".join(
                            plan.transfer.fare_breakdown
                        )
                    )


            # ===================================
            # ВЫБОР ВАРИАНТА
            # ===================================

            if st.button(
                "Выбрать этот вариант",
                key=(
                    f"select_plan_"
                    f"{position}"
                ),
                type=(
                    "primary"
                    if position == 1
                    else "secondary"
                ),
                use_container_width=True
            ):

                selection = (
                    select_plan(
                        state=(
                            st.session_state
                            .agent_state
                        ),

                        plan_index=(
                            position - 1
                        )
                    )
                )


                if (
                    selection[
                        "status"
                    ]
                    == "success"
                ):

                    st.session_state.agent_state = (
                        selection[
                            "state"
                        ]
                    )

                    st.session_state.cart = (
                        selection[
                            "cart"
                        ]
                    )

                    st.session_state.order = None

                    st.rerun()


                else:

                    st.error(
                        selection[
                            "message"
                        ]
                    )


# ===================================
# КОРЗИНА
# ===================================

def show_cart(
    cart
):

    st.subheader(
        "🛒 Ваша поездка"
    )


    period_text = (
        format_trip_period(
            cart
        )
    )


    if period_text:

        st.caption(
            f"📅 Период поездки: "
            f"{period_text}"
        )


    travelers_text = (
        format_travelers(
            cart
        )
    )


    if travelers_text:

        st.caption(
            f"👥 Путешественники: "
            f"{travelers_text}"
        )


    with st.container(
        border=True
    ):

        for item in (
            cart["items"]
        ):

            st.markdown(
                f"**{item['name']}**"
            )


            st.caption(
                item["details"]
            )


            st.write(
                f"{item['price']:,} ₽"
                .replace(",", " ")
            )


            st.divider()


        st.markdown(
            "### Итого"
        )


        st.markdown(
            f"## "
            f"{cart['calculated_total']:,} ₽"
            .replace(",", " ")
        )


        if not cart[
            "total_ok"
        ]:

            st.error(
                "Не удалось подтвердить "
                "итоговую стоимость. "
                "Проверьте состав поездки."
            )


        if cart[
            "warnings"
        ]:

            st.warning(
                "\n\n".join(
                    cart[
                        "warnings"
                    ]
                )
            )


# ===================================
# ОФОРМЛЕНИЕ
# ===================================

def show_checkout(
    cart
):

    st.subheader(
        "Оформление поездки"
    )


    period_text = (
        format_trip_period(
            cart
        )
    )


    if period_text:

        st.info(
            f"✈️ {cart['destination_city']} "
            f"· 📅 {period_text} "
            f"· {cart['calculated_total']:,} ₽"
            .replace(",", " ")
        )


    travelers_text = (
        format_travelers(
            cart
        )
    )


    if travelers_text:

        st.write(
            "**Путешественники:** "
            f"{travelers_text}"
        )


    rooms_required = int(
        cart.get(
            "rooms_required",
            1,
        )
        or 1
    )


    st.write(
        "**Номера:** "
        f"{format_rooms(rooms_required)}"
    )


    traveler_name = (
        st.text_input(
            "Имя путешественника",
            placeholder=(
                "Например: "
                "Анна Иванова"
            )
        )
    )


    warnings_confirmed = True


    if cart[
        "warnings"
    ]:

        warnings_confirmed = (
            st.checkbox(
                "Я ознакомился(лась) "
                "с предупреждениями "
                "по этой поездке."
            )
        )


    st.caption(
        "В демо-версии реальная оплата "
        "не производится."
    )


    if st.button(
        "Оформить поездку",
        type="primary",
        use_container_width=True
    ):

        if not traveler_name.strip():

            st.warning(
                "Укажите имя путешественника."
            )

            return


        checkout = (
            mock_checkout(
                cart=cart,

                traveler_name=(
                    traveler_name.strip()
                ),

                warnings_confirmed=(
                    warnings_confirmed
                )
            )
        )


        if (
            checkout[
                "status"
            ]
            == "success"
        ):

            order = (
                checkout[
                    "order"
                ]
            )


            st.session_state.order = (
                order
            )


            st.session_state.agent_state[
                "order"
            ] = order


            st.session_state.agent_state[
                "status"
            ] = "booked"


            st.rerun()


        elif (
            checkout[
                "status"
            ]
            == "needs_warning_confirmation"
        ):

            st.warning(
                checkout[
                    "message"
                ]
            )


        else:

            st.error(
                checkout[
                    "message"
                ]
            )


# ===================================
# УСПЕШНОЕ ОФОРМЛЕНИЕ
# ===================================

def show_order(
    order
):

    st.success(
        "✅ Поездка оформлена "
        "в демонстрационном режиме."
    )


    with st.container(
        border=True
    ):

        st.markdown(
            "### Бронирование подтверждено"
        )


        st.write(
            "**Номер заказа:** "
            f"{order['order_id']}"
        )


        st.write(
            "**Направление:** "
            f"{order['destination_city']}"
        )


        period_text = (
            format_trip_period(
                order
            )
        )


        if period_text:

            st.write(
                "**Период поездки:** "
                f"{period_text}"
            )


        travelers_text = (
            format_travelers(
                order
            )
        )


        if travelers_text:

            st.write(
                "**Состав путешественников:** "
                f"{travelers_text}"
            )


        rooms_required = int(
            order.get(
                "rooms_required",
                1,
            )
            or 1
        )


        st.write(
            "**Номера:** "
            f"{format_rooms(rooms_required)}"
        )


        st.write(
            "**Основной путешественник:** "
            f"{order['traveler_name']}"
        )


        st.write(
            "**Итоговая стоимость:** "
            f"{order['total_price']:,} ₽"
            .replace(",", " ")
        )


        st.write(
            "**Оплата:** "
            "имитация"
        )


        st.caption(
            "На реальном продукте "
            "здесь пользователь перешёл бы "
            "к оплате и подтверждению бронирования."
        )


# ===================================
# ТЕКУЩИЙ ЭКРАН
# ===================================

current_status = (
    st.session_state
    .agent_state[
        "status"
    ]
)


# -----------------------------------
# ORDER
# -----------------------------------

if (
    st.session_state.order
    is not None
):

    show_order(
        st.session_state.order
    )


# -----------------------------------
# CART
# -----------------------------------

elif (
    st.session_state.cart
    is not None
):

    show_cart(
        st.session_state.cart
    )


    if st.button(
        "← Вернуться к вариантам"
    ):

        st.session_state.cart = None

        st.session_state.agent_state[
            "status"
        ] = "recommendations_ready"

        st.rerun()


    show_checkout(
        st.session_state.cart
    )


# -----------------------------------
# RECOMMENDATIONS
# -----------------------------------

elif (
    st.session_state.latest_result
    is not None
):

    show_trip_plans(
        st.session_state.latest_result
    )


# ===================================
# CHAT INPUT
# ===================================

if (
    st.session_state.cart
    is None
    and st.session_state.order
    is None
):

    user_message = (
        st.chat_input(
            "Напишите сообщение StayMatch"
        )
    )


else:

    user_message = None


if user_message:

    # -----------------------------------
    # USER MESSAGE
    # -----------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    current_status = (
        st.session_state
        .agent_state[
            "status"
        ]
    )


    # ===================================
    # НОВЫЙ ЗАПРОС
    # ===================================

    if (
        current_status
        == "new"
    ):

        response = (
            start_agent(
                user_text=(
                    user_message
                ),

                destinations=(
                    destinations
                ),

                transport=(
                    transport
                ),

                transfers=(
                    transfers
                ),

                hotels=(
                    hotels
                )
            )
        )


    # ===================================
    # УТОЧНЕНИЕ
    # ===================================

    elif (
        current_status
        == "waiting_clarification"
    ):

        response = (
            continue_agent(
                state=(
                    st.session_state
                    .agent_state
                ),

                user_answer=(
                    user_message
                ),

                destinations=(
                    destinations
                ),

                transport=(
                    transport
                ),

                transfers=(
                    transfers
                ),

                hotels=(
                    hotels
                )
            )
        )


    # ===================================
    # ПЕРЕСБОРКА
    # ===================================

    elif (
        current_status
        == "recommendations_ready"
    ):

        response = (
            replan_agent(
                state=(
                    st.session_state
                    .agent_state
                ),

                user_message=(
                    user_message
                ),

                destinations=(
                    destinations
                ),

                transport=(
                    transport
                ),

                transfers=(
                    transfers
                ),

                hotels=(
                    hotels
                )
            )
        )


    # ===================================
    # ПРОЧЕЕ
    # ===================================

    else:

        response = {
            "state":
                st.session_state
                .agent_state,

            "action":
                "error",

            "message": (
                "Сейчас этот сценарий "
                "не поддерживается. "
                "Начните новую поездку."
            ),

            "result":
                st.session_state
                .latest_result
        }


    # ===================================
    # СОХРАНЯЕМ STATE
    # ===================================

    st.session_state.agent_state = (
        response[
            "state"
        ]
    )


    # ===================================
    # ОТВЕТ АГЕНТА
    # ===================================

    assistant_message = (
        response[
            "message"
        ]
    )


    if response.get(
        "hint"
    ):

        assistant_message += (
            "\n\n"
            f"_{response['hint']}_"
        )


    changes_text = (
        format_changes(
            response.get(
                "changes",
                []
            )
        )
    )


    if changes_text:

        assistant_message += (
            "\n\n"
            "**Что изменилось:**\n"
            f"{changes_text}"
        )


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content":
                assistant_message
        }
    )


    # ===================================
    # РЕКОМЕНДАЦИИ
    # ===================================

    if (
        response[
            "action"
        ]
        == "show_recommendations"
    ):

        st.session_state.latest_result = (
            response[
                "result"
            ]
        )

        st.session_state.cart = None

        st.session_state.order = None


    st.rerun()
