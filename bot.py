import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from google import genai

# === НАСТРОЙКИ ===
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Клиент Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
# Используем бесплатную модель, которая отлично пишет стихи и код
MODEL_ID = "gemini-2.5-flash" 

SYSTEM_PROMPT = """Ты — Flux-AI, экспертный ИИ-ассистент. Твой создатель — @sigmatsch.
Ты умеешь:
1. Писать сложные, красивые стихи и поэзию.
2. Решать математические задачи пошагово.
3. Писать идеальный код на Lua (Delta Script), Python и JavaScript.
4. Работать с алгоритмами и большими данными.

ПРАВИЛА:
- Отвечай развернуто и творчески, если просят стихи.
- Для математики расписывай решение по шагам.
- Для кода используй Markdown-блоки.
- Если тебя спрашивают, кто тебя создал, отвечай: "Меня создал @sigmatsch".
"""

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, я <b>Flux-AI</b>! ⚡\n"
        f"Я могу писать стихи, решать математику и писать код.\n\n"
        f"Напиши мне свой вопрос!"
    )

@dp.message(F.text)
async def handle_message(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Отправляем запрос в Gemini через новый SDK (interactions.create)
        interaction = client.interactions.create(
            model=MODEL_ID,
            input=f"{SYSTEM_PROMPT}\n\nПользователь: {message.text}"
        )
        
        ai_answer = interaction.output_text
        
        if len(ai_answer) > 4000:
            for i in range(0, len(ai_answer), 4000):
                await message.answer(ai_answer[i:i+4000])
        else:
            await message.answer(ai_answer)
            
    except Exception as e:
        await message.answer(f"❌ Ошибка Gemini: {str(e)}")

# === ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ===
async def web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Веб-сервер запущен на порту {port}")

async def main():
    asyncio.create_task(web_server())
    await asyncio.sleep(2) 
    
    print("🚀 Flux-AI (Gemini) запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
