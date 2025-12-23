import asyncio
from aiohttp import web
from aiogram import types
from bot import bot, dp
from config import USE_WEBHOOK, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT
from training_manager import reminder_loop  # фоновые задачи

async def on_startup(app: web.Application):
    if USE_WEBHOOK:
        await bot.set_webhook(WEBHOOK_URL)
    # Запуск фоновой задачи напоминаний
    asyncio.create_task(reminder_loop(bot))

async def on_shutdown(app: web.Application):
    if USE_WEBHOOK:
        await bot.delete_webhook()
    await bot.session.close()

async def handle_webhook(request: web.Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update)
    return web.Response(text="ok")

def run_polling():
    print("Запуск бота в режиме polling...")
    asyncio.run(dp.start_polling(bot))

def run_webhook():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    if USE_WEBHOOK:
        run_webhook()
    else:
        run_polling()
