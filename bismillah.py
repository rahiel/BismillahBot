# -*- coding: utf-8 -*-
###############################################################################
# BismillahBot -- Explore the Noble Qur'an on Telegram                        #
# Copyright (C) 2015  Rahiel Kasim                                            #
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
from time import sleep
from urllib2 import URLError
import sys

import telegram
from redis import StrictRedis
import ujson as json

from quran import Quran
from secret import TOKEN


english = Quran("translation")
tafsir = Quran("tafsir")
r = StrictRedis()
redis_namespace = ""


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
    bot = telegram.Bot(token=TOKEN)

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.getUpdates()[0].update_id
    except IndexError:
        update_id = None

    data = {"english": english, "tafsir": tafsir}

    while True:
        try:
            update_id = serve(bot, update_id, data)
        except telegram.TelegramError as e:
            if e.message in ("Bad Gateway", "Timed out"):
                sleep(2)
            elif e.message == "Unauthorized":
                update_id += 1
            else:
                raise e
        except URLError as e:
            sleep(2)


def serve(bot, update_id, data):
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
            bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)
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
        chat_id = update.message.chat_id
        update_id = update.update_id + 1
        message = update.message.text.encode("utf-8").lower()
        state = get_user(chat_id)
        if state is not None:
            s, a, quran_type = state
        else:
            s, a, quran_type = 1, 1, "english"

        print("%d: %s" % (chat_id, message))

        if chat_id < 0:
            continue            # bot should not be in a group

        if message.startswith('/'):
            command = message[1:]
            if command in ("start", "help"):
                text = ("Send me the numbers of a surah and ayah, for example:"
                        " 2 255. Then I respond with that ayah from the Noble "
                        "Quran. Or type: random.")
            elif command == "about":
                text = ("The English translation is by Imam Ahmed Raza from "
                        "tanzil.net/trans/. The audio is a recitation by "
                        "Shaykh Mahmoud Khalil al-Husary from everyayah.com. "
                        "The tafsir is Tafsir al-Jalalayn from altafsir.com."
                        "The source code of the bot is available at: "
                        "https://github.com/rahiel/BismillahBot.")
            else:
                text = "Invalid command"
            bot.sendMessage(chat_id=chat_id, text=text)
            continue

        match = re.match("(\d+)[ :\-;.,]*(\d*)", message)
        if match is not None:
            s = int(match.group(1))
            a = int(match.group(2)) if match.group(2) else 1
            send_quran(s, a, quran_type, chat_id, reply_markup=interface)
        elif message in ("english", "tafsir", "audio", "arabic"):
                send_quran(s, a, message, chat_id)
        elif message in ("next", "previous", "random"):
            if message == "next":
                s, a = Quran.getNextAyah(s, a)
            elif message == "previous":
                s, a = Quran.getPreviousAyah(s, a)
            elif message == "random":
                s, a = Quran.getRandomAyah()
            send_quran(s, a, quran_type, chat_id)

    sys.stdout.flush()
    return update_id


if __name__ == '__main__':
    main()
