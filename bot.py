from telegram import Update
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram import Bot
from telegram.utils.request import Request
import pandas as pd
import telegram_send
import requests
from bs4 import BeautifulSoup
import time

df = pd.read_csv('df.csv')
eng_cities = df['City (eng)'].to_list()
cities = df['City (rus)'].to_list()



TG_TOKEN = '1925886680:AAFa6Aq5BGX7aYii-U10cGrGiKAjbiAxtQw'
TG_API_URL = 'https://api.telegram.org/bot'

BUTTON1_HELP = "Info"
BUTTON2_Start = "Start"

CALLBACK_BUTTON1 = "Start"
CALLBACK_BUTTON2 = "Info"
CALLBACK_BUTTON_HIDE_KEYBOARD = "callback_button_hide"


TITLES = {
    CALLBACK_BUTTON1: "Start",
    CALLBACK_BUTTON2: "Info",
    CALLBACK_BUTTON_HIDE_KEYBOARD: "Hide the keyboard"
}

def get_base_reply_keyboard():
    keyboard = [
        [
            KeyboardButton(BUTTON1_HELP),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

def keyboard_callback_handler(update: Update, context: CallbackContext):
    """ Handler for ALL buttons from ALL keyboards
    """
    query = update.callback_query
    data = query.data

    chat_id = update.effective_message.chat_id
    current_text = update.effective_message.text

    if data == CALLBACK_BUTTON_HIDE_KEYBOARD:
        # Hide keyboard
        # Works only when sending a new message
        context.bot.send_message(
            chat_id=chat_id,
            text="""I hid the keyboard
Press /start to bring it back""",
            reply_markup=ReplyKeyboardRemove(),
        )
    elif data == CALLBACK_BUTTON1:
        context.bot.send_message(
                chat_id=chat_id,
                text="""Send me a city name""",
        )


def get_base_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON1], callback_data=CALLBACK_BUTTON1),
        ],
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON_HIDE_KEYBOARD], callback_data=CALLBACK_BUTTON_HIDE_KEYBOARD),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)






def do_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Hi! Send me a city name",
        reply_markup=get_base_reply_keyboard(),
    )


def do_help(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="""This bot helps you getting data about YT tariffs in Russian cities""",
        reply_markup=get_base_inline_keyboard(),
    )


def do_echo(update: Update, context: CallbackContext):
    text = update.message.text
    if text == BUTTON1_HELP:
        return do_help(update=update, context=context)
    elif text == BUTTON2_Start:
        return do_start(update=update, context=context)
    else:
        city = update.message.text

        string = 'City is not found'
        if city in eng_cities:
            city_base = []
            city_more = []
            city_tariffs = []
            txt = []
            webs = df[df['City (eng)'] == city].reset_index()
            www = webs['website']
            if www[0] != 'Not supported':
                for web in webs['Tariffs (eng)'][0].split(', '):
                    url = www + '/' + web
                    r = requests.get(url[0])
                    soup = BeautifulSoup(r.text)
                    s = soup.find('div', {'class': "MainPrices__description"})
                    base = [x.text.replace('\xa0', ' ').replace('\u202f', ' ') for x in s.find_all('div')]
                    s = soup.find('div', {'class': 'PriceGroup PriceGroup_theme_normal PriceGroup_table'})
                    add_names = [x.text.replace('\xa0', '') for x in s.find_all('span', {'class': 'PriceGroup__name'})]
                    add_prices = [x.text.replace('\u202f', '') for x in
                                  s.find_all('div', {'class': 'PriceGroup__price'})]
                    s = soup.find('div', {'class': "MainPrices__title"})
                    txt.append(s.text)
                    more = [x + ' - ' + y for x, y in zip(add_names, add_prices)]
                    city_tariffs.append(soup.find_all('span', {'class': 'GroupSelectorItem__name'})[0].text)
                    city_base.append(base)
                    city_more.append(more)
                string = cities[eng_cities.index(city)] + ' (' + city + ') \n'
                for i in range(len(city_base)):
                    string = string + txt[i] + '\n'
                    string = string + webs['Tariffs (rus)'][0].split(', ')[i] + ', '
                    string = string + city_tariffs[i] + ':' + '\n'
                    string = string + ', '.join(map(str, city_base[i])) + '\n' + '\n'
                    string = string + ', '.join(map(str, city_more[i])) + '\n' + '\n' + '\n'
            else:
                string = city + ' (' + cities[eng_cities.index(city)] + ')' + ' is not supported'
        if len(string) > 4096:
            for x in range(0, len(string), 4096):
                update.message.reply_text(text = string[x:x + 4096])
        else:
            update.message.reply_text(
                text=string,
                reply_markup=get_base_inline_keyboard(),
            )



def main():

    req = Request(
        connect_timeout=0.5,
        read_timeout=1.0,
    )
    bot = Bot(
        token=TG_TOKEN,
        request=req,
        base_url=TG_API_URL,
    )
    updater = Updater(
        bot=bot,
        use_context=True,
    )

    # Check that the bot has correctly connected to the Telegram API
    info = bot.get_me()

    # Command handlers
    start_handler = CommandHandler("start", do_start)
    help_handler = CommandHandler("help", do_help)
    message_handler = MessageHandler(Filters.text, do_echo)
    buttons_handler = CallbackQueryHandler(callback=keyboard_callback_handler)

    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(help_handler)
    updater.dispatcher.add_handler(message_handler)
    updater.dispatcher.add_handler(buttons_handler)
    # Start endless processing of incoming messages
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()







