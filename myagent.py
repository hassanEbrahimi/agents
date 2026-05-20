"""دستیار صوتی رستوران — Google Gemini Live."""

import logging

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli
from livekit.plugins import google, silero

logger = logging.getLogger("myagent")

load_dotenv()

server = AgentServer()

RESTAURANT_CONTEXT = """
رستوران «سفره طلایی» — غذای ایرانی، تهران، خیابان ولیعصر، پلاک ۱۲۴۵.
تلفن رزرو: ۰۲۱-۸۸۷۷۶۶۵۵. تحویل بیرون‌بر: دارد. پارکینگ: محدود.

ساعت کار: شنبه تا پنج‌شنبه ۱۱:۰۰–۲۳:۰۰ | جمعه ۱۳:۰۰–۲۳:۰۰

منو (قیمت به تومان):
- چلوکباب کوبیده: ۳۸۵٬۰۰۰ | چلوکباب برگ: ۴۹۵٬۰۰۰ | جوجه کباب: ۳۶۵٬۰۰۰
- قورمه‌سبزی با برنج: ۲۹۵٬۰۰۰ | قیمه: ۲۸۵٬۰۰۰ | فسنجان: ۳۴۵٬۰۰۰
- زرشک پلو با مرغ: ۳۱۵٬۰۰۰ | باقلاقاتوق: ۲۷۵٬۰۰۰
- سالاد شیرازی: ۸۵٬۰۰۰ | ماست موسیر: ۶۵٬۰۰۰ | دوغ: ۴۵٬۰۰۰
- نوشابه / آب معدنی: ۳۵٬۰۰۰ | چای: ۴۰٬۰۰۰ | دسر زعفرانی: ۱۲۰٬۰۰۰

پیش‌غذا: سوپ جو ۹۵٬۰۰۰. بسته‌بندی بیرون‌بر: ۳۰٬۰۰۰ تومان.
زمان آماده‌سازی معمول: ۲۵–۴۰ دقیقه. ظرفیت سالن: حدود ۸۰ نفر.
"""

AGENT_INSTRUCTIONS = (
    "تو منشی صوتی رستوران «سفره طلایی» هستی. فقط درباره همین رستوران صحبت کن: "
    "منو، قیمت، ساعت کار، رزرو، آدرس، بیرون‌بر و سفارش.\n"
    f"{RESTAURANT_CONTEXT.strip()}\n"
    "قوانین:\n"
    "- هر جواب حداکثر یک یا دو جمله کوتاه؛ محاوره‌ای و فارسی.\n"
    "- اگر غذا یا قیمتی در منو نیست، بگو موجود نیست یا با آشپزخانه هماهنگ می‌کنی.\n"
    "- سیاست، مذهب، خبر، ورزش، شوخی حاشیه‌ای و هر موضوع غیررستورانی: "
    "«فقط درباره رستوران کمک می‌کنم» و برگرد به منو یا سفارش.\n"
    "- ایموجی و مارک‌داون نه."
)


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession(
        vad=silero.VAD.load(),
        llm=google.realtime.RealtimeModel(),
    )

    agent = Agent(instructions=AGENT_INSTRUCTIONS)

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions=(
            "به فارسی در یک جمله معرفی کن: رستوران سفره طلایی، "
            "و بپرس چی میل دارید یا رزرو می‌خواهید."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
