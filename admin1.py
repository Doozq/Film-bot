# Импортируем необходимые классы.
import telegram
from telegram import ReplyKeyboardRemove
from telegram.ext import MessageHandler, filters, ConversationHandler
from telegram.ext import CommandHandler
from data import db_session
from data.films import Film
from data.chanels import Chanel
from config import ADMIN_PASWORD, admin_markup, BOT_TOKEN, api_request
import requests


bot = telegram.Bot(token=BOT_TOKEN)


# СЦЕНАРИЙ ВХОДА В РЕЖИМ АДМНИСТРАТОРА
async def ask_for_password(update, context):
    await update.message.reply_text("Введите пароль для входа в режим администратора")
    return 1


async def check_password(update, context):
    if update.message.text == ADMIN_PASWORD:
        context.user_data['admin_mode'] = True
        await update.message.reply_text("Вы вошли в режим администратора", reply_markup=admin_markup)
        await send_admin_menu(update)
    else:
        await update.message.reply_text("Вы ввели неверный пароль")
    return ConversationHandler.END


async def stop_login(update, context):
    context.user_data['admin_mode'] = False
    await update.message.reply_text("Отмена входа в режим администратора")
    return ConversationHandler.END


admin_login_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('admin_login', ask_for_password)],

        # Состояние внутри диалога.
        states={
            # Функция читает пароль и проверяет его.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)]
        },

        # Точка прерывания диалога — команда /stop.
        fallbacks=[CommandHandler('stop', stop_login)]
    )


# Проверка на администратора
def is_admin(context):
    if 'admin_mode' in context.user_data and context.user_data['admin_mode']:
        return True
    else:
        return False


# /admin_menu
async def admin_menu(update, context):
    if is_admin(context):
        await send_admin_menu(update)


# Отправка меню администратора
async def send_admin_menu(update):
    await update.message.reply_text("Команды администратора:\n\n"
                                    "/admin_menu - для описания команд администратора\n\n"
                                    "/add_film - для добавления нового фильма\n\n"
                                    "/add_advert - для добавления ного спонсора\n\n"
                                    "/delete_advert - для удаления спонсора\n\n"
                                    "/send_message - для отправки сообщения всем пользователям бота\n\n"
                                    "/logout - для выхода из режима администратора\n\n")


# /logout
async def admin_logout(update, context):
    if is_admin(context):
        context.user_data['admin_mode'] = False
        await update.message.reply_text(
            "Вы вышли из режима администратора",
            reply_markup=ReplyKeyboardRemove()
        )


# СЦЕНАРИЙ ДОБАВЛЕНИЯ ФИЛЬМА
async def ask_for_film_name(update, context):
    if is_admin(context):
        await update.message.reply_text("Введите название фильма")
        return 1


async def ask_for_film_url(update, context):
    context.user_data['film_name'] = update.message.text
    await update.message.reply_text("Введите ссылку на фильм")
    return 2


async def ask_for_add_poster(update, context):
    context.user_data['film_url'] = update.message.text
    context.user_data["poster"] = 0
    request = api_request + context.user_data['film_name']
    response = requests.get(request)
    if response:
        # Преобразуем ответ в json-объект
        json_response = response.json()

        film_info = json_response["docs"][0]
        film_poster_url = film_info["poster"]
        response_poster_url = requests.get(film_poster_url).content
        if response.status_code == 200:
            context.user_data["poster_url"] = response_poster_url
            await bot.send_photo(chat_id=update.message.chat.id, photo=response_poster_url)
            await update.message.reply_text("Для фашего фильма найден постер. Добавить его? (Да/Нет)")
            return 3
        else:
            return 4
    else:
        return 4


async def confirm_add_poster(update, context):
    if update.message.text == "Да":
        context.user_data["poster"] = context.user_data["poster_url"]
        await update.message.reply_text("Постер добавлен")
        await ask_for_confirm_add_film(update, context)
        return 4
    elif update.message.text == "Нет":
        await update.message.reply_text("Постер не добавлен")
        await ask_for_confirm_add_film(update, context)
        return 4
    else:
        await update.message.reply_text("Ответ не распознан. (Да/Нет)")
        return 3


async def ask_for_confirm_add_film(update, context):
    if context.user_data["poster"]:
        await bot.send_photo(chat_id=update.message.chat.id, photo=context.user_data["poster"])
    await update.message.reply_text(f"Название: {context.user_data['film_name']}\n\n"
                                    f"Ссылка: {context.user_data['film_url']}")
    await update.message.reply_text("Введённые данные верны? (Да/Нет)")


async def confirm_add_film(update, context):
    if update.message.text == "Да":
        film = Film()
        film.name = context.user_data['film_name']
        film.url = context.user_data['film_url']
        if context.user_data["poster"]:
            img_response = context.user_data["poster"]
            film.img = bytes(img_response)
        db_sess = db_session.create_session()
        db_sess.add(film)
        db_sess.commit()
        code = db_sess.query(Film).filter(Film.url == str(context.user_data['film_url'])).first().code
        await update.message.reply_text(f"Фильм добавлен с кодом {code}")
        return ConversationHandler.END
    elif update.message.text == "Нет":
        await update.message.reply_text("Фильм не добавлен")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Ответ не распознан. (Да/Нет)")
        return 4


async def stop_add_film(update, context):
    await update.message.reply_text("Отмена добавления фильма")
    return ConversationHandler.END


admin_add_film_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('add_film', ask_for_film_name)],

        # Состояние внутри диалога.
        states={
            # Функция читает пароль и проверяет его.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_film_url)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_add_poster)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_add_poster)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_add_film)]
        },

        # Точка прерывания диалога — команда /stop.
        fallbacks=[CommandHandler('stop', stop_add_film)]
    )


# СЦЕНАРИЙ ДОБАВЛЕНИЯ КАНАЛА
async def ask_for_chanel_name(update, context):
    if is_admin(context):
        await update.message.reply_text("Введите название канала")
        return 1


async def ask_for_chanel_url(update, context):
    context.user_data['chanel_name'] = update.message.text
    await update.message.reply_text("Введите ссылку на канал")
    return 2


async def ask_for_confirm_add_chanel(update, context):
    context.user_data['chanel_url'] = update.message.text
    await update.message.reply_text(f"Название: {context.user_data['chanel_name']}\n\n"
                                    f"Ссылка: {context.user_data['chanel_url']}")
    await update.message.reply_text("Введённые данные верны? (Да/Нет)")
    return 3


async def confirm_add_chanel(update, context):
    if update.message.text == "Да":
        chanel = Chanel()
        chanel.name = context.user_data['chanel_name']
        chanel.url = context.user_data['chanel_url']
        db_sess = db_session.create_session()
        db_sess.add(chanel)
        db_sess.commit()
        await update.message.reply_text(f"Канал {context.user_data['chanel_name']} добавлен в список рекламы")
        return ConversationHandler.END
    elif update.message.text == "Нет":
        await update.message.reply_text("Канал не добавлен")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Ответ не распознан. (Да/Нет)")
        return 3


async def stop_add_chanel(update, context):
    await update.message.reply_text("Отмена добавления канала")
    return ConversationHandler.END


admin_add_advert_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('add_chanel', ask_for_chanel_name)],

        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_chanel_url)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_confirm_add_chanel)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_add_chanel)]
        },

        # Точка прерывания диалога — команда /stop.
        fallbacks=[CommandHandler('stop', stop_add_chanel)]
    )


# СЦЕНАРИЙ УДАЛЕНИЯ КАНАЛА
async def ask_for_deleted_chanel_url(update, context):
    if is_admin(context):
        await update.message.reply_text("Введите ссылку удаляемого канала канала")
        return 1


async def ask_for_confirm_delete_chanel(update, context):
    context.user_data['deleted_chanel_url'] = update.message.text
    db_sess = db_session.create_session()
    chanel = db_sess.query(Chanel).filter(Chanel.url == str(context.user_data['deleted_chanel_url'])).first()
    if chanel:
        await update.message.reply_text(f"Название: {chanel.name}\n\n"
                                        f"Ссылка: {context.user_data['deleted_chanel_url']}")
        await update.message.reply_text("Введённые данные верны и вы хотите удалить этот канал? (Да/Нет)")
        return 2
    else:
        await update.message.reply_text("Канал с такой ссылкой не найден, проверьте ссылку и попробуйте снова")
        return ConversationHandler.END


async def confirm_delete_chanel(update, context):
    if update.message.text == "Да":
        db_sess = db_session.create_session()
        name = db_sess.query(Chanel).filter(Chanel.url == str(context.user_data['deleted_chanel_url'])).first().name
        db_sess.query(Chanel).filter(Chanel.url == str(context.user_data['deleted_chanel_url'])).delete()
        db_sess.commit()
        await update.message.reply_text(f"Канал {name} удален из списка рекламы")
        return ConversationHandler.END
    elif update.message.text == "Нет":
        await update.message.reply_text("Канал не удален")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Ответ не распознан. (Да/Нет)")
        return 2


async def stop_delete_advert(update, context):
    await update.message.reply_text("Отмена удаления фильма")
    return ConversationHandler.END


admin_delete_advert_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('delete_chanel', ask_for_deleted_chanel_url)],

        # Состояние внутри диалога.
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_confirm_delete_chanel)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_chanel)]
        },

        # Точка прерывания диалога — команда /stop.
        fallbacks=[CommandHandler('stop', stop_delete_advert)]
    )
