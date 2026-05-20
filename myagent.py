"""Voice restaurant assistant — Google Gemini Live."""

import asyncio
import json
import logging
import secrets
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    FunctionToolsExecutedEvent,
    JobContext,
    cli,
)
from livekit.agents.llm import FunctionCallOutput, function_tool
from livekit.plugins import google, silero

logger = logging.getLogger("myagent")

load_dotenv()

server = AgentServer()

ORDERS_DIR = Path(__file__).resolve().parent / "orders"

RESTAURANT_CONTEXT = """
Restaurant: Golden Plate — simple American and grill food.
Address: 1245 Main Street, Austin, TX 78701.
Phone for reservations: (512) 555-0142. Delivery: yes. Parking: limited.

Hours: Monday–Thursday 11:00 AM–10:00 PM | Friday–Saturday 11:00 AM–11:00 PM | Sunday 12:00–9:00 PM

Menu (prices in USD):
- Cheeseburger with fries: $12 | Grilled chicken sandwich: $11 | Veggie burger: $10
- Caesar salad: $9 | Garden salad: $8
- Grilled salmon with rice: $18 | Steak with mashed potatoes: $22 | Pasta with tomato sauce: $14
- Chicken wings (8 pieces): $13 | Fish and chips: $15
- Soft drink / water: $3 | Coffee: $4 | Chocolate cake: $6

Soup of the day: $6. Delivery fee: $4.
Usual wait time: 25–40 minutes. Dining room seats about 60 people.
"""

AGENT_INSTRUCTIONS = (
    "You are the voice assistant for Golden Plate restaurant. "
    "Only talk about this restaurant: menu, prices, hours, reservations, address, "
    "delivery, and orders.\n"
    f"{RESTAURANT_CONTEXT.strip()}\n"
    "Rules:\n"
    "- Speak only in English. Use very simple words. Short sentences. "
    "Easy for beginners and tourists. No slang, no idioms, no hard words.\n"
    "- Each reply: one or two short sentences maximum.\n"
    "- If a dish or price is not on the menu, say we do not have it or you will check with the kitchen.\n"
    "- Politics, religion, news, sports, jokes, and anything not about the restaurant: "
    "say 'I can only help with the restaurant' and go back to the menu or order.\n"
    "- No emoji and no markdown.\n"
    "- When the customer confirms the final order, you must call register_order. "
    "Before that, get name, phone, order type (delivery / pickup / dine_in), "
    "and the full list of food. Summarize once and ask if it is correct.\n"
    "- After register_order, tell the customer the result. "
    "If success, say the order is saved. If not, say there was a problem saving the order."
)

ORDER_SUCCESS_MESSAGE = "Your order was saved successfully."
ORDER_ERROR_MESSAGE = "Sorry, there was a problem saving your order. Please try again."


def _order_result(*, success: bool, message: str, order_id: str | None = None) -> str:
    return json.dumps(
        {"success": success, "message": message, "order_id": order_id},
        ensure_ascii=False,
    )


def _new_order_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(3)
    return f"{stamp}-{suffix}"


def _save_order(payload: dict) -> Path:
    ORDERS_DIR.mkdir(parents=True, exist_ok=True)
    path = ORDERS_DIR / f"{payload['order_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _parse_items(items: str) -> list[str]:
    return [part.strip() for part in items.split(",") if part.strip()]


def _user_message_from_tool_output(output: FunctionCallOutput | None) -> str:
    if output is None or output.is_error:
        return ORDER_ERROR_MESSAGE

    try:
        result = json.loads(output.output)
    except json.JSONDecodeError:
        logger.warning("Could not parse register_order output: %s", output.output)
        return ORDER_ERROR_MESSAGE

    message = result.get("message")
    if result.get("success"):
        order_id = result.get("order_id")
        if order_id:
            return f"{ORDER_SUCCESS_MESSAGE} Your order number is {order_id}."
        return message or ORDER_SUCCESS_MESSAGE

    return message or ORDER_ERROR_MESSAGE


async def _announce_order_result(session: AgentSession, message: str) -> None:
    await session.generate_reply(
        instructions=(
            f"Tell the customer exactly this sentence in simple English. "
            f"Do not add anything else: \"{message}\""
        )
    )


class RestaurantAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTIONS,
            llm=google.realtime.RealtimeModel(),
        )

    @function_tool
    async def register_order(
        self,
        items: str,
        customer_name: str,
        customer_phone: str,
        order_type: str,
        total_usd: float,
        delivery_address: str = "",
        notes: str = "",
    ) -> str:
        """Save the customer's final order in the system.

        Args:
            items: Food list with quantities, comma-separated; e.g. "Cheeseburger x2, Water x1"
            customer_name: Customer name
            customer_phone: Customer phone number
            order_type: One of delivery, pickup, or dine_in
            total_usd: Approximate order total in US dollars
            delivery_address: Delivery address; required for delivery, otherwise empty
            notes: Extra notes such as no onions
        """
        parsed_items = _parse_items(items)
        if not parsed_items:
            return _order_result(
                success=False,
                message="The food list is empty. Ask the customer what they want first.",
            )

        normalized_type = order_type.strip().lower()
        if normalized_type not in {"delivery", "pickup", "dine_in"}:
            return _order_result(
                success=False,
                message="Invalid order type. Use delivery, pickup, or dine_in.",
            )

        if normalized_type == "delivery" and not delivery_address.strip():
            return _order_result(
                success=False,
                message="For delivery, ask the customer for their address.",
            )

        order_id = _new_order_id()
        payload = {
            "order_id": order_id,
            "created_at": datetime.now(UTC).isoformat(),
            "restaurant": "Golden Plate",
            "customer_name": customer_name.strip(),
            "customer_phone": customer_phone.strip(),
            "order_type": normalized_type,
            "delivery_address": delivery_address.strip() or None,
            "items": parsed_items,
            "total_usd": total_usd,
            "notes": notes.strip() or None,
        }

        try:
            path = _save_order(payload)
        except OSError:
            logger.exception("Failed to save order %s", order_id)
            return _order_result(
                success=False,
                message=ORDER_ERROR_MESSAGE,
                order_id=order_id,
            )

        logger.info("Order saved: %s -> %s", order_id, path)
        return _order_result(
            success=True,
            message=ORDER_SUCCESS_MESSAGE,
            order_id=order_id,
        )


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession(
        vad=silero.VAD.load(),
    )

    @session.on("function_tools_executed")
    def on_function_tools_executed(ev: FunctionToolsExecutedEvent) -> None:
        for call, output in ev.zipped():
            if call.name != "register_order":
                continue

            ev.cancel_tool_reply()
            message = _user_message_from_tool_output(output)
            asyncio.create_task(_announce_order_result(session, message))

    agent = RestaurantAgent()

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions=(
            "In one short, simple English sentence, say hello from Golden Plate restaurant "
            "and ask if they want to order food or make a reservation."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
