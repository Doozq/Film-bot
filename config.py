from telegram import ReplyKeyboardMarkup

ADMIN_PASWORD = "123"

BOT_TOKEN = '6203323325:AAESD4nnAVEi33zXaDwcap5tHSUNFSFwE3A'

reply_keyboard = [['/admin_menu'],
                  ['/add_film'],
                  ['/add_chanel'],
                  ['/delete_chanel'],
                  ['/logout']]
admin_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

api_request = "https://api.kinopoisk.dev/v1.2/movie/search?token=R4R54CY-EWR4AGF-M98GFZE-MAN60P3&page=1&limit=1&query="
