
from copy import deepcopy

from agent_logic import (
    get_next_clarification,
    apply_clarification_answer,
    refresh_missing_info,
)

from trip_engine import (
    parse_trip_request_basic,
)

from trip_planner import (
    build_trip_plans,
)


def create_agent_state():
    return {
        "trip_request": None,
        "pending_field": None,
        "status": "new",
        "result": None,
    }


def build_agent_trip(
    state,
    destinations,
    transport,
    transfers,
    hotels,
):
    trip_request = state["trip_request"]

    result = build_trip_plans(
        trip_request=trip_request,
        destinations=destinations,
        transport=transport,
        transfers=transfers,
        hotels=hotels,
        top_n=3,
    )

    state["result"] = result

    if result["status"] == "success":
        state["status"] = "recommendations_ready"

        return {
            "state": state,
            "action": "show_recommendations",
            "message": "Я собрал варианты поездки.",
            "result": result,
        }

    if result["status"] == "needs_clarification":
        state["status"] = "waiting_clarification"
        state["pending_field"] = result["missing_field"]

        return {
            "state": state,
            "action": "ask_question",
            "message": result["question"],
            "result": None,
        }

    state["status"] = "no_results"

    return {
        "state": state,
        "action": "no_results",
        "message": result.get(
            "message",
            "Не удалось собрать поездку.",
        ),
        "result": result,
    }


def start_agent(
    user_text,
    destinations,
    transport,
    transfers,
    hotels,
):
    state = create_agent_state()

    trip_request = parse_trip_request_basic(
        user_text,
        transport,
    )

    trip_request = refresh_missing_info(
        trip_request
    )

    state["trip_request"] = trip_request

    clarification = get_next_clarification(
        trip_request
    )

    if clarification["needs_clarification"]:
        state["status"] = "waiting_clarification"
        state["pending_field"] = clarification[
            "missing_field"
        ]

        return {
            "state": state,
            "action": "ask_question",
            "message": clarification["question"],
            "hint": clarification["hint"],
            "result": None,
        }

    state["pending_field"] = None

    return build_agent_trip(
        state=state,
        destinations=destinations,
        transport=transport,
        transfers=transfers,
        hotels=hotels,
    )


def continue_agent(
    state,
    user_answer,
    destinations,
    transport,
    transfers,
    hotels,
):
    state = deepcopy(state)

    if (
        state["status"] != "waiting_clarification"
        or state["pending_field"] is None
    ):
        return {
            "state": state,
            "action": "error",
            "message": (
                "Сейчас агент не ожидает "
                "уточняющего ответа."
            ),
            "result": state.get("result"),
        }

    clarification_result = (
        apply_clarification_answer(
            trip_request=state["trip_request"],
            missing_field=state["pending_field"],
            user_answer=user_answer,
            transport=transport,
        )
    )

    if (
        clarification_result["status"]
        != "updated"
    ):
        return {
            "state": state,
            "action": "ask_again",
            "message": clarification_result["message"],
            "result": None,
        }

    state["trip_request"] = clarification_result[
        "trip_request"
    ]

    next_clarification = clarification_result[
        "next_clarification"
    ]

    if next_clarification["needs_clarification"]:
        state["status"] = "waiting_clarification"
        state["pending_field"] = next_clarification[
            "missing_field"
        ]

        return {
            "state": state,
            "action": "ask_question",
            "message": next_clarification["question"],
            "hint": next_clarification["hint"],
            "result": None,
        }

    state["pending_field"] = None

    return build_agent_trip(
        state=state,
        destinations=destinations,
        transport=transport,
        transfers=transfers,
        hotels=hotels,
    )
