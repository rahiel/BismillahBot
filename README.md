# BismillahBot

بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيْمِ

BismillahBot is a bot on Telegram to explore the Holy Qur'an.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Usage](#usage)
- [Installation](#installation)
    - [Data files](#data-files)
    - [Updating](#updating)
- [License](#license)

<!-- markdown-toc end -->

# Usage

Use the bot by messaging [Bismillahbot][] on [Telegram][]. For every verse the
bot has an English translation from [Imam Ahmad Raza][], audio recitation
by [Shaykh Mahmoud Khalil al-Husary][], and exegesis (tafsir)
from [Tafsir al-Jalalayn][]. The translation and tafsir are available anywhere
on Telegram via [inline mode][], just start a text with `@BismillahBot` (for
example, type `@BismillahBot 1:1` in any chat). A conversation looks like:
![example]

Also see [AudioQuranBot][], a bot that sends audio files of complete surahs.

[BismillahBot]: https://telegram.me/BismillahBot
[Telegram]: https://telegram.org/
[Imam Ahmad Raza]: https://en.wikipedia.org/wiki/Ahmed_Raza_Khan_Barelvi
[Shaykh Mahmoud Khalil al-Husary]: https://en.wikipedia.org/wiki/Mahmoud_Khalil_Al-Hussary
[Tafsir al-Jalalayn]: http://www.altafsir.com/Al-Jalalayn.asp
[inline mode]: https://telegram.org/blog/inline-bots
[example]: https://i.imgur.com/kITXcHz.png "Example conversation"
[AudioQuranBot]: https://github.com/rahiel/AudioQuranBot

# Installation

You can run your own instance of BismillahBot. First you need to request a
[bot username and token](https://core.telegram.org/bots#3-how-do-i-create-a-bot).
You also need a Unix-like system to run the bot on. BismillahBot is running on a
Debian server. The following gets the code, and installs the dependencies on
Debian/Ubuntu in a virtualenv:

```bash
sudo apt install redis-server git python3-pip python3-dev virtualenv
git clone https://github.com/rahiel/BismillahBot.git
cd BismillahBot/
virtualenv -p python3 venv
. venv/bin/activate
pip install -r requirements.txt --upgrade
```

In the same directory you should define a `secret.py` with the token you got
from the [BotFather](https://telegram.me/botfather):

```python
TOKEN = "<your-token-here>"
```

Disable group chats for the bot by sending the BotFather the `/setjoingroups`
command and customize the bot further.

## Data files

The bot serves Quranic data collected from several projects. These are necessary
for the bot to function. Run the following in the bot's directory to get the
data:

```bash
wget "http://tanzil.net/trans/en.ahmedraza"
wget "http://tanzil.net/res/text/metadata/quran-data.xml"
wget "http://www.altafsir.com/Books/Al_Jalalain_Eng.pdf"
pdftotext -nopgbrk Al_Jalalain_Eng.pdf
wget "http://www.everyayah.com/data/Husary_128kbps/000_versebyverse.zip"
unzip -d Husary 000_versebyverse.zip
wget "http://www.everyayah.com/data/quranpngs/000_images.zip"
unzip -d quran_images 000_images.zip
```

We do some post-processing on the images. First we remove the empty area's from
the edges with [ImageMagick](https://www.imagemagick.org/script/index.php) and
[GNU parallel](https://www.gnu.org/software/parallel/):
``` shell
cd quran_images/
parallel "echo {}; convert {} -trim {}" ::: *.png
```
Then we optimize the images with [pngout](http://www.jonof.id.au/kenutils):
``` shell
parallel "pngout {}" ::: *.png
```

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
. venv/bin/activate
pip install -r requirements.txt -U
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
