# BismillahBot -- Explore the Holy Qur'an on Telegram
# Copyright (C) 1436-1438 AH  Rahiel Kasim
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import re
import sys
from time import sleep, time
from typing import Tuple

import telegram
import ujson as json
from redis import StrictRedis
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import MAX_MESSAGE_LENGTH
from telegram.error import NetworkError, TelegramError, Unauthorized

from quran import Quran, make_index
from secret import TOKEN


r = StrictRedis()
redis_namespace = ""
update_id = None


def save_user(chat_id: int, state: Tuple[int, int, str]):
    """State is a tuple: (surah, ayah, type)"""
    r.set(redis_namespace + str(chat_id),
          json.dumps(state), ex=60 * 60 * 24 * 31 * 6)  # keep state for half a year


def get_user(chat_id: int):
    v = r.get(redis_namespace + str(chat_id))
    if v is not None:
        return json.loads(v)


def save_file(filename: str, file_id: str):
    r.set(redis_namespace + "file:" + filename,
          json.dumps(file_id), ex=60 * 60 * 24 * 31 * 3)  # keep for 3 months


def get_file(filename: str):
    f = r.get(redis_namespace + "file:" + filename)
    if f is not None:
        return json.loads(f)


def get_audio_filename(s: int, a: int) -> str:
    return "Husary/" + str(s).zfill(3) + str(a).zfill(3) + ".mp3"


def get_image_filename(s: int, a: int) -> str:
    return "quran_images/" + str(s) + "_" + str(a) + ".png"


def send_file(bot, filename, quran_type, **kwargs):
    """Tries to send file from Telegram's cache, only uploads from disk if necessary.
    Always saves the Telegram cache file_id in Redis and returns it.
    """

    def upload(f):
        if quran_type == "arabic":
            v = bot.send_photo(photo=f, **kwargs)["photo"][-1]["file_id"]
        elif quran_type == "audio":
            v = bot.send_audio(audio=f, **kwargs)["audio"]["file_id"]
        save_file(filename, v)
        return v

    def upload_from_disk():
        with open(filename, "rb") as f:
            return upload(f)

    f = get_file(filename)
    if f is not None:
        try:
            return upload(f)
        except telegram.TelegramError as e:
            if "file_id" in e.message:
                return upload_from_disk()
            else:
                raise e
    else:
        return upload_from_disk()


def get_default_query_results(quran: Quran):
    results = []
    ayat = [
        (13, 28), (33, 56), (2, 62), (10, 31), (17, 36), (5, 32), (39, 9), (17, 44), (28, 88), (17, 84), (33, 6),
        (7, 57), (3, 7), (2, 255), (63, 9), (57, 20), (49, 12), (16, 125), (24, 35), (73, 8), (4, 103)
    ]
    for s, a in ayat:
        ayah = "%d:%d" % (s, a)
        english = quran.get_ayah(s, a)
        results.append(InlineQueryResultArticle(
            ayah + "def", title=ayah,
            description=english[:120],
            input_message_content=InputTextMessageContent(english))
        )
    return results


def main():
    global update_id
    bot = telegram.Bot(token=TOKEN)

    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    interface = telegram.ReplyKeyboardMarkup(
        [["Arabic", "Audio", "English", "Tafsir"],
         ["Previous", "Random", "Next"]],
        resize_keyboard=True)

    data = {
        "english": Quran("translation"),
        "tafsir": Quran("tafsir"),
        "index": make_index(),
        "interface": interface
    }
    data["default_query_results"] = get_default_query_results(data["english"])

    while True:
        try:
            serve(bot, data)
        except NetworkError:
            sleep(1)
        except Unauthorized:  # user has removed or blocked the bot
            update_id += 1
        except TelegramError as e:
            if "Invalid server response" in str(e):
                sleep(3)
            else:
                raise e


def serve(bot, data):
    global update_id

    def send_quran(s: int, a: int, quran_type: str, chat_id: int, reply_markup=None):
        if quran_type in ("english", "tafsir"):
            text = data[quran_type].get_ayah(s, a)
            bot.send_message(chat_id=chat_id, text=text[:MAX_MESSAGE_LENGTH],
                             reply_markup=reply_markup)
        elif quran_type == "arabic":
            bot.send_chat_action(chat_id=chat_id,
                                 action=telegram.ChatAction.UPLOAD_PHOTO)
            image = get_image_filename(s, a)
            send_file(bot, image, quran_type, chat_id=chat_id,
                      caption="Quran %d:%d" % (s, a),
                      reply_markup=reply_markup)
        elif quran_type == "audio":
            bot.send_chat_action(chat_id=chat_id,
                                 action=telegram.ChatAction.UPLOAD_AUDIO)
            audio = get_audio_filename(s, a)
            send_file(bot, audio, quran_type, chat_id=chat_id,
                      performer="Shaykh Mahmoud Khalil al-Husary",
                      title="Quran %d:%d" % (s, a),
                      reply_markup=reply_markup)
        save_user(chat_id, (s, a, quran_type))

    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1

        if update.inline_query:
            query_id = update.inline_query.id
            query = update.inline_query.query
            results = []
            cache_time = 66 * (60 ** 2 * 24)
            s, a = parse_ayah(query)
            if s is not None and Quran.exists(s, a):
                ayah = "%d:%d" % (s, a)
                english = data["english"].get_ayah(s, a)
                tafsir = data["tafsir"].get_ayah(s, a)
                results.append(InlineQueryResultArticle(
                    ayah + "english", title="English",
                    description=english[:120],
                    input_message_content=InputTextMessageContent(english))
                )
                results.append(InlineQueryResultArticle(
                    ayah + "tafsir", title="Tafsir",
                    description=tafsir[:120],
                    input_message_content=InputTextMessageContent(tafsir))
                )
            else:
                results = data["default_query_results"]
            bot.answer_inline_query(inline_query_id=query_id, cache_time=cache_time, results=results)
            continue

        if not update.message or not update.message.text:  # updates without text
            continue

        chat_id = update.message.chat_id
        message = update.message.text.lower()
        state = get_user(chat_id)
        if state is not None:
            s, a, quran_type = state
        else:
            s, a, quran_type = 1, 1, "english"

        print("%d:%.3f:%s" % (chat_id, time(), message.replace("\n", " ")))

        if chat_id < 0:
            continue            # bot should not be in a group

        # "special:quran_type"
        special_state = quran_type.split(":")

        if message.startswith("/"):
            command = message[1:]
            if command in ("start", "help"):
                text = ("Send me the numbers of a surah and ayah, for example:"
                        " <b>2:255</b>. Then I respond with that ayah from the Holy "
                        "Quran. Type /index to see all Surahs or try /random. "
                        "I'm available in any chat on Telegram, just type: <b>@BismillahBot</b>")
            elif command == "about":
                text = ("The English translation is by Imam Ahmed Raza from "
                        "tanzil.net/trans/. The audio is a recitation by "
                        "Shaykh Mahmoud Khalil al-Husary from everyayah.com. "
                        "The tafsir is Tafsir al-Jalalayn from altafsir.com."
                        "The source code of BismillahBot is available at: "
                        "https://github.com/rahiel/BismillahBot.")
            elif command == "index":
                text = data["index"]
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
                bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                continue

        if len(special_state) > 1:
            if special_state[0] == "feedback":
                with open("feedback.txt", "a") as f:
                    f.write("%d: %s\n" % (chat_id, message))
                text = "Feedback saved 😊"
                bot.send_message(chat_id=chat_id, text=text)
                save_user(chat_id, (s, a, special_state[1]))
                continue

        if message in ("english", "tafsir", "audio", "arabic"):
            send_quran(s, a, message, chat_id)
            continue
        elif message in ("next", "previous", "random", "/random"):
            if message == "next":
                s, a = Quran.get_next_ayah(s, a)
            elif message == "previous":
                s, a = Quran.get_previous_ayah(s, a)
            elif message in ("random", "/random"):
                s, a = Quran.get_random_ayah()
            send_quran(s, a, quran_type, chat_id)
            continue

        s, a = parse_ayah(message)
        if s:
            if Quran.exists(s, a):
                send_quran(s, a, quran_type, chat_id, reply_markup=data["interface"])
            else:
                bot.send_message(chat_id=chat_id, text="Ayah does not exist!")

    sys.stdout.flush()


def parse_ayah(message: str):
    match = re.match("/?(\d+)[ :\-;.,]*(\d*)", message)
    if match is not None:
        s = int(match.group(1))
        a = int(match.group(2)) if match.group(2) else 1
        return s, a
    else:
        return None, None


if __name__ == "__main__":
    main()
