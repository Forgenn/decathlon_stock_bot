# -*- coding: utf-8 -*-
import json
import time

import requests
import os
from bs4 import BeautifulSoup as bs
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Bot
from dotenv import load_dotenv


load_dotenv()

# Bot token
token = os.getenv('token')
# Dictionary with all users and urls associated
users = {}
#Init bot for sending messages
bot = Bot(token=token)



# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Use the command /subscribe followed by the urls of the decathlon pages you want notifications of. /unsubscribe if you dont want to receive anymore notifications')


def help(update, context):
    """Send a message when the command /help is issued."""

    update.message.reply_text('Help!')


def subscribe(update, context):
    if len(context.args) == 0:
        update.message.reply_text("You have to put one or more links")
        return

    add_user(update.message.chat_id, context.args)

    print("Adding user " + str(update.message.chat_id) + " with args " + " ".join(context.args))
    update.message.reply_text("You will be notified when there is stock of the product")


def unsubscribe(update, context):
    print("User " + str(update.message.chat_id) + " removed")
    remove_user(update.message.chat_id)
    update.message.reply_text("Canceled subscriptions")


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    print('Update ' + update + ' caused error ')


def init_dict():
    global users
    if os.path.getsize("users.json"):
        with open("users.json", "r") as read_file:
            users = json.load(read_file)
            pass


def write_dict():
    with open('users.json', 'w') as outfile:
        json.dump(users, outfile)


def add_user(user_id, urls):
    if str(user_id) not in users:
        users[user_id] = urls
    else:
        for url in urls:
            users[str(user_id)].append(url)
    write_dict()


def remove_user(user_id):
    if str(user_id) in users:
        users[str(user_id)] = []
        write_dict()


def check_stock():

    for user_id, user_urls in list(users.items()):
        if len(user_urls) != 0:
            for url in user_urls:
                in_stock, product_name = check_item_stock(url)
                if in_stock:
                    print('The product ' + product_name + ' is in stock')
                    bot.send_message(chat_id=user_id, text='El item ' + product_name + ' esta en stock')
                else:
                    print('The product ' + product_name + ' still doesn't have stock')


def check_item_stock(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    s = requests.Session()
    try:
        request = s.get(url, headers=headers)
        page = bs(request.content, features="html.parser")
        has_stock = page.find('div', class_='stock-notification__invite stock-notification__invite--active')
        has_stock = False if has_stock is None else True
        product_name = page.find("h1", class_='title--main product-title-right').text
    except requests.exceptions.RequestException as e:
        print("Error scrapping the web", e)
        product_name, has_stock = '', ''
    return (True, product_name) if not has_stock else (False, product_name)


def start_bot():
    """Start the bot."""
    #Init updater with bots token
    updater = Updater(token, use_context=True)

    print("Bot started")
    init_dict()

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("subscribe", subscribe, pass_args=True))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.


if __name__ == '__main__':
    start_bot()
    while True:
        print('Checking stock')
        check_stock()
        time.sleep(900)
