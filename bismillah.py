# -*- coding: utf-8 -*-
###############################################################################
# BismillahBot -- Explore the Noble Qur'an on Telegram                        #
# Copyright (C) 1436-1437 AH  Rahiel Kasim                                    #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################
import re
from time import sleep, time
import sys

import telegram
from telegram.error import NetworkError, Unauthorized
from redis import StrictRedis
import ujson as json

from quran import Quran, make_index
from secret import TOKEN


english = Quran("translation")
tafsir = Quran("tafsir")
index = make_index()
r = StrictRedis(unix_socket_path="/tmp/redis.sock")
redis_namespace = ""
update_id = None


def save_user(chat_id, state):
    """State is a list: [surah:int, ayah:int, type:str]"""
    r.set(redis_namespace + str(chat_id),
          json.dumps(state), ex=31536000)  # keep state for a year


def get_user(chat_id):
    v = r.get(redis_namespace + str(chat_id))
    if v is not None:
        return json.loads(v)


def save_file(filename, file_id):
    r.set(redis_namespace + "file:" + filename,
          json.dumps(file_id), ex=8035200)  # keep for 3 months


def get_file(filename):
    f = r.get(redis_namespace + "file:" + filename)
    if f is not None:
        return json.loads(f)


def main():
    global update_id
    bot = telegram.Bot(token=TOKEN)

    try:
        update_id = bot.getUpdates()[0].update_id
    except IndexError:
        update_id = None

    data = {"english": english, "tafsir": tafsir}

    while True:
        try:
            serve(bot, data)
        except NetworkError:
            sleep(0.2)
        except Unauthorized:  # user has removed or blocked the bot
            update_id += 1


def serve(bot, data):
    global update_id
    interface = telegram.ReplyKeyboardMarkup(
        [["Arabic", "Audio", "English", "Tafsir"],
         ["Previous", "Random", "Next"]],
        resize_keyboard=True)

    def send_quran(s, a, quran_type, chat_id, reply_markup=None):
        if not (0 < s < 115 and 0 < a <= Quran.surah_lengths[s]):
            bot.sendMessage(chat_id=chat_id, text="Ayah does not exist!")
            return
        elif quran_type in ("english", "tafsir"):
            text = data[quran_type].getAyah(s, a)
            bot.sendMessage(chat_id=chat_id, text=text[:4030],
                            reply_markup=reply_markup)
        elif quran_type == "arabic":
            bot.sendChatAction(chat_id=chat_id,
                               action=telegram.ChatAction.UPLOAD_PHOTO)
            image = "quran_images/" + str(s) + '_' + str(a) + ".png"
            upload_file(image, quran_type, chat_id=chat_id,
                        caption="Quran %d:%d" % (s, a),
                        reply_markup=reply_markup)
        elif quran_type == "audio":
            bot.sendChatAction(chat_id=chat_id,
                               action=telegram.ChatAction.UPLOAD_AUDIO)
            audio = ("Husary/" + str(s).zfill(3) + str(a).zfill(3) + ".mp3")
            upload_file(audio, quran_type, chat_id=chat_id,
                        performer="Shaykh Mahmoud Khalil al-Husary",
                        title="Quran %d:%d" % (s, a),
                        reply_markup=reply_markup)
        save_user(chat_id, [s, a, quran_type])

    def upload_file(filename, quran_type, **kwargs):

        def upload(f):
            if quran_type == "arabic":
                v = bot.sendPhoto(photo=f, **kwargs)["photo"][-1]["file_id"]
            elif quran_type == "audio":
                v = bot.sendAudio(audio=f, **kwargs)["audio"]["file_id"]
            save_file(filename, v)

        def upload_from_disk():
            with open(filename, "rb") as f:
                upload(f)

        f = get_file(filename)
        if f is not None:
            try:
                upload(f)
            except telegram.TelegramError as e:
                if "file_id" in e.message:
                    upload_from_disk()
                else:
                    raise e
        else:
            upload_from_disk()

    for update in bot.getUpdates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        if not update.message:  # weird Telegram update with only an update_id
            continue
        chat_id = update.message.chat_id
        message = update.message.text.encode("utf-8").lower()
        state = get_user(chat_id)
        if state is not None:
            s, a, quran_type = state
        else:
            s, a, quran_type = 1, 1, "english"

        print("%d:%.3f:%s" % (chat_id, time(), message.replace('\n', ' ')))

        if chat_id < 0:
            continue            # bot should not be in a group

        # "special:quran_type"
        special_state = quran_type.split(':')

        if message.startswith('/'):
            command = message[1:]
            parse_mode = None
            if command in ("start", "help"):
                text = ("Send me the numbers of a surah and ayah, for example:"
                        " 2 255. Then I respond with that ayah from the Noble "
                        "Quran. Type /index to see all Surahs or try /random.")
            elif command == "about":
                text = ("The English translation is by Imam Ahmed Raza from "
                        "tanzil.net/trans/. The audio is a recitation by "
                        "Shaykh Mahmoud Khalil al-Husary from everyayah.com. "
                        "The tafsir is Tafsir al-Jalalayn from altafsir.com."
                        "The source code of BismillahBot is available at: "
                        "https://github.com/rahiel/BismillahBot.")
            elif command == "index":
                text = index
                parse_mode = "HTML"
            elif command == "feedback":
                text = ("Jazak Allahu khayran! Your feedback is highly "
                        "appreciated and will help us improve our services. "
                        "Your next message will be sent to the developers. "
                        "Send /cancel to cancel.")
                save_user(chat_id, (s, a, "feedback:" + quran_type))
            elif command == "cancel":
                text = ("Cancelled.")
                if len(special_state) > 1:
                    save_user(chat_id, (s, a, special_state[1]))
            else:
                text = None  # "Invalid command"
            if text:
                bot.sendMessage(chat_id=chat_id, text=text, parse_mode=parse_mode)
                continue

        if len(special_state) > 1:
            if special_state[0] == "feedback":
                with open("feedback.txt", 'a') as f:
                    f.write("%d: %s\n" % (chat_id, message))
                text = "Feedback saved " + telegram.Emoji.SMILING_FACE_WITH_SMILING_EYES
                bot.sendMessage(chat_id=chat_id, text=text)
                save_user(chat_id, (s, a, special_state[1]))
                continue

        if message in ("english", "tafsir", "audio", "arabic"):
            send_quran(s, a, message, chat_id)
            continue
        elif message in ("next", "previous", "random", "/random"):
            if message == "next":
                s, a = Quran.getNextAyah(s, a)
            elif message == "previous":
                s, a = Quran.getPreviousAyah(s, a)
            elif message in ("random", "/random"):
                s, a = Quran.getRandomAyah()
            send_quran(s, a, quran_type, chat_id)
            continue

        match = re.match("/?(\d+)[ :\-;.,]*(\d*)", message)
        if match is not None:
            s = int(match.group(1))
            a = int(match.group(2)) if match.group(2) else 1
            send_quran(s, a, quran_type, chat_id, reply_markup=interface)

    sys.stdout.flush()


if __name__ == "__main__":
    main()
