import asyncio
from aiohttp import web
from aiogram import types
from bot import bot, dp
from config import USE_WEBHOOK, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT

# --- webhook handlers (если используем webhook) ---
async def on_startup(app: web.Application):
    if USE_WEBHOOK:
        # Установка webhook на полный URL 
        await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    if USE_WEBHOOK:
        await bot.delete_webhook()
    await bot.session.close()

async def handle_webhook(request: web.Request):
    data = await request.json()
    update = types.Update(**data)
    # Передаём апдейт в диспетчер
    await dp.feed_update(update)
    return web.Response(text="ok")

def run_polling():
    print("Запуск бота в режиме polling...")
    asyncio.run(dp.start_polling(bot))

def run_webhook():
    print("Запуск бота в режиме webhook...")
    app = web.Application()
    # путь /webhook (указан в WEBHOOK_URL)
    app.router.add_post("/webhook", handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    if USE_WEBHOOK:
        run_webhook()
    else:
        run_polling()
