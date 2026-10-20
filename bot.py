import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from openai import AsyncOpenAI

# === НАСТРОЙКИ ===
TOKEN = os.getenv("BOT_TOKEN")
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Инициализация клиента Cloudflare (через библиотеку OpenAI)
client = AsyncOpenAI(
    base_url=f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1",
    api_key=CF_API_TOKEN,
)

# Модель Cloudflare (Llama 3.1)
MODEL_ID = "@cf/meta/llama-3.1-8b-instruct"

SYSTEM_PROMPT = """Ты — Nexus_AI, экспертный ИИ-ассистент по программированию. Твой создатель — @sigmatsch.
Твоя главная цель — писать идеальный код на Lua (Roblox/Delta Script), Python и JavaScript.
ПРАВИЛА:
1. Ты пишешь только рабочий код. Если просят скрипт для Delta Script — используй правильный API Roblox (loadstring, getgenv и т.д.).
2. Всегда оформляй код в Markdown-блоки.
3. Никакой воды. Только факты и код.
4. Если тебя спрашивают, кто тебя создал, отвечай: "Меня создал @sigmatsch".
"""

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, я <b>Nexus_AI</b>! 🤖\n"
        f"Я работаю на нейросети Cloudflare.\n"
        f"Могу писать код на Lua (Delta Script), Python и JS.\n\n"
        f"Напиши мне задачу!"
    )

@dp.message(F.text)
async def handle_message(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        response = await client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            extra_headers={
                "Authorization": f"Bearer {CF_API_TOKEN}"
            }
        )
        
        ai_answer = response.choices[0].message.content
        
        if len(ai_answer) > 4000:
            for i in range(0, len(ai_answer), 4000):
                await message.answer(ai_answer[i:i+4000])
        else:
            await message.answer(ai_answer)
            
    except Exception as e:
        await message.answer(f"❌ Ошибка Cloudflare: {str(e)}")

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
    
    print("🚀 Бот Nexus_AI (Cloudflare) запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
