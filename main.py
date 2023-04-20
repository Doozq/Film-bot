# Импортируем необходимые классы.
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import CommandHandler
from data import db_session
from data.films import Film
from data.chanels import Chanel
from admin import admin_login_handler, admin_menu, admin_logout, admin_add_film_handler, admin_add_advert_handler
from admin import admin_delete_advert_handler
from config import BOT_TOKEN

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start_command(update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"Привет {user.mention_html()}! Я кино-бот. Напишите код фильма, \
и я отвправлю вам его навзание, описиание и ссылку на просмотр",
    )


async def help_command(update, context):
    await update.message.reply_text("Введите код фильма")


async def code_to_film(update, context):
    user_id = update.effective_user.id

    if 'subscribed' not in context.user_data:
        context.user_data['subscribed'] = False

    if await check_sub_chanels(user_id):
        if context.user_data['subscribed']:
            film = db_sess.query(Film).filter(Film.code == int(update.message.text)).first()
            if film:
                if film.img:
                    await bot.send_photo(chat_id=update.message.chat.id, photo=film.img)
                await update.message.reply_text(f"Код: {film.code}\n\n"
                                                f"Название: {film.name}\n\n"
                                                f"Смотреть: {film.url}")
            else:
                await update.message.reply_text("Фильм с таким кодом не найден")
        else:
            await ask_for_sub(update.message.chat.id)
    else:
        await ask_for_sub(update.message.chat.id)


# Отправление списка каналов для подписки
async def ask_for_sub(user_id):
    keyboard = []
    for chanel in db_sess.query(Chanel).all():
        keyboard.append([InlineKeyboardButton(chanel.name, callback_data=1, url=chanel.url)])
    keyboard.append([InlineKeyboardButton("✅Я ПОДПИСАЛСЯ", callback_data=200)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(user_id, "Для БЕСЛАТНОГО просмотра\nПодпишитесь на каналы ниже👇\n\
И нажмите кнопку \n«✅Я ПОДПИСАЛСЯ»", reply_markup=reply_markup)


async def check_sub_chanels(user_id):
    for chanel in db_sess.query(Chanel).all():
        a = await bot.get_chat_member(chat_id=f'@{chanel.url[13:]}', user_id=user_id)
        if a["status"] == "left":
            return False
    return True


async def button_check_sub(update, context):

    query = update.callback_query

    if query.data == '200':
        print(update.effective_user.id)
        if await check_sub_chanels(update.effective_user.id):
            context.user_data['subscribed'] = True
            await bot.send_message(update.effective_user.id, f"Спасибо за подписку❤️ Для просмотра фильма введите код \
и бот отправит вам фильм")

        else:
            await bot.send_message(update.effective_user.id, "Вы не подписались на все каналы")
            await ask_for_sub(update.effective_user.id)


def main():
    # Создаём объект Application.
    application = Application.builder().token(BOT_TOKEN).build()

    # Создаём обработчик сообщений типа filters.TEXT
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, code_to_film)

    # Регистрируем обработчики в приложении:

    # Админ-мод
    application.add_handler(admin_login_handler)
    application.add_handler(admin_add_film_handler)
    application.add_handler(admin_add_advert_handler)
    application.add_handler(admin_delete_advert_handler)
    application.add_handler(CommandHandler("admin_menu", admin_menu))
    application.add_handler(CommandHandler("logout", admin_logout))

    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Текст
    application.add_handler(text_handler)

    # Кнопка проверки подписок
    application.add_handler(CallbackQueryHandler(button_check_sub))

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    bot = telegram.Bot(token=BOT_TOKEN)
    db_session.global_init("db/database.db")
    db_sess = db_session.create_session()
    main()
