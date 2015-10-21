بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيْمِ

BismillahBot is a bot on telegram to explore the Qur'an.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Usage](#usage)
- [Installation](#installation)
    - [Data files](#data-files)
    - [Updating](#updating)
- [License](#license)

<!-- markdown-toc end -->

# Usage

The bot can be used by messaging
[@Bismillahbot](https://telegram.me/BismillahBot) on
[Telegram](https://telegram.org/). A conversation looks like
![BismillahBot](https://i.imgur.com/kITXcHz.png "Sample conversation").

# Installation

You can run your own instance of BismillahBot. First you need to request a
[bot username and token](https://core.telegram.org/bots#3-how-do-i-create-a-bot).
You also need a Unix system to run the bot on. BismillahBot is running on a
[DigitalOcean droplet](https://www.digitalocean.com/?refcode=8b7b76e3230d)
(referral link) running Ubuntu. The following gets the code, and installs the
dependencies on Ubuntu:

```bash
sudo apt-get install redis-server git python-pip
git clone https://github.com/rahiel/BismillahBot.git
cd BismillahBot/
pip install python-telegram-bot redis hiredis ujson
```

In the same directory you should define a `secret.py` with the token you got
from the [BotFather](https://telegram.me/botfather):

```python
TOKEN = "<your-token-here"
```

Disable group chats for the bot by sending the BotFather the `/setjoingroups`
command and customize the bot further.

## Data files

The bot serves Quranic data collected from several projects. These are necessary
for the bot to function. Run the following in the bot's directory to get the
data:

```bash
wget "http://tanzil.net/trans/en.ahmedraza"
wget "https://drive.google.com/uc?export=download&id=0B24P_FGD7V4jeTVaMXpaUFNiMlk" -O "Al_Jalalain_Eng.txt"
wget "http://www.everyayah.com/data/Husary_128kbps/000_versebyverse.zip"
unzip -d Husary 000_versebyverse.zip
wget "http://www.everyayah.com/data/quranpngs/000_images.zip"
unzip -d quran_images 000_images.zip
```

This gets the Qur'an in an English rendition by
[Imam Ahmed Raza Khan](https://en.wikipedia.org/wiki/Ahmed_Raza_Khan_Barelvi),
the [Tafsir al-Jalalayn](http://www.altafsir.com/Al-Jalalayn.asp), audio
recitation by
[Shaykh Mahmoud Khalil al-Husary](https://en.wikipedia.org/wiki/Mahmoud_Khalil_Al-Hussary)
and the Quranic text in images.

You could use other data files, like
[other translations](http://tanzil.net/trans/) or
[audio recitations](http://www.everyayah.com/data/status.php). These choices are
currently hardcoded in the bot, so
[file an issue](https://github.com/rahiel/BismillahBot/issues/new) if you'd like
to use different data.

If all went fine you can now run the bot with `python bismillah.py`.

## Updating

The bot (and dependencies) can be updated by running the following in its
directory:

```bash
git pull
pip install -U python-telegram-bot redis hiredis ujson
```

# License

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
