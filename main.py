from pymystem3 import Mystem
import telebot
from telebot import types
import datetime
import conf
import sqlite3
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
import string
from PIL import Image, ImageFont, ImageDraw
m = Mystem()
nltk.download("stopwords")

con = sqlite3.connect(
    'positive_bot.db', check_same_thread=False)
cur = con.cursor()

bot = telebot.TeleBot(conf.TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = types.InlineKeyboardMarkup()
    new_memory = types.InlineKeyboardButton(
        text="Новое", callback_data="new_memory")
    random_memory = types.InlineKeyboardButton(
        text="Случайное", callback_data="random_memory")
    wordcloud_button = types.InlineKeyboardButton(
        text="Облако слов", callback_data="wordcloud_button")
    keyboard.add(new_memory)
    keyboard.add(random_memory)
    keyboard.add(wordcloud_button)
    bot.send_message(message.chat.id,
                     '''Привет! Добро пожаловать в позитивный бот!
                     \nВы можете добавить хорошее воспоминание, запросить случайное или получить облако слов.
                     \nЧтобы начать заново, введите "/start"!
                     \nПроект на GitHub: https://github.com/chenopodiumlang/positive_bot''', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "new_memory":
            bot.send_message(
                call.message.chat.id, "Расскажите, что хорошего произошло сегодня!")
            record_message(call.message)
        if call.data == "random_memory":
            random_message_query = '''SELECT message FROM messages WHERE tg_id = ?
ORDER BY RANDOM()
LIMIT 1'''
            cur.execute(random_message_query, (str(call.message.chat.id),))
            random_message = cur.fetchall()
            s2 = ""

            counter = 0
            for sym in str(random_message[0]):
                if sym == ' ' and counter == 4:
                    s2 += '\n'
                else:
                    s2 += sym
                if counter != 4:
                    counter += 1
                else:
                    counter = 1

            my_image = Image.open("image.jpg")


            title_font = ImageFont.truetype('arial.ttf', 200)

            image_editable = ImageDraw.Draw(my_image)
            image_editable.text((2000, 15), s2,
                                (77, 66, 48), font=title_font)

            bot.send_photo(call.message.chat.id, my_image)
            bot.send_message(call.message.chat.id,
                             random_message)
        if call.data == "wordcloud_button":
            total_wordcloud(call.message.chat.id)


@bot.message_handler(func=lambda m: True)
def record_message(msg):
    tg_id = msg.from_user.id
    if tg_id != 5232996957:
        date = str(datetime.date.today())
        message = msg.text
        my_data = [tg_id, date, message]
        my_data = tuple(my_data)
        insert_query = "INSERT INTO messages(tg_id,date,message) VALUES (?,?,?)"
        cur.execute(insert_query, my_data)
        con.commit()
        bot.send_message(
            msg.from_user.id, "Готово!")

def total_wordcloud(userid):
    wordcloud_query = '''SELECT message FROM messages WHERE tg_id = ?'''
    cur.execute(wordcloud_query, (str(userid),))
    users_memories = cur.fetchall()
    users_memories_str = ''.join(str(users_memories))
    users_memories_better_string = ''
    for i in users_memories_str:
        if i not in string.punctuation:
            i = i.lower()
            users_memories_better_string += i

    stops = set(stopwords.words('russian'))
    users_memories_list = users_memories_better_string.split()
    users_memories_list_clean = []
    for word in users_memories_list:
        if word not in stops:
            users_memories_list_clean.append(word)
    non_lemm = ' '.join(users_memories_list_clean)
    lemmas = m.lemmatize(non_lemm)

    wordcloud = WordCloud(background_color='white').generate(
        ' '.join(lemmas))
    wordcloud_img = wordcloud.to_image()
    bot.send_photo(userid, wordcloud_img)

if __name__ == '__main__':
    bot.polling(none_stop=True)
