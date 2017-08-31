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
import xml.etree.ElementTree as ET
from random import randint
from typing import Tuple


def parse_quran(filename: str):
    """Parse Quran text files (with ayah numbers) from http://tanzil.net."""
    quran = []
    surah = []
    s = 1

    def process_verse(verse: str):
        """Add verse and replace for Arabic ligatures (salawat)"""
        return (verse.strip()
                .replace("– peace and blessings be upon him", "ﷺ‎"))

    with open(filename, "r") as f:
        for line in f.readlines():
            if line == "\n":
                continue
            if line.startswith("#"):
                break
            verse = line.split("|")
            assert len(verse) == 3
            if int(verse[0]) == s:
                surah.append(process_verse(verse[2]))
            else:
                quran.append(surah)
                surah = [process_verse(verse[2])]
                s += 1
    quran.append(surah)
    assert sum([len(s) for s in quran]) == 6236, "Missing verses!"
    return quran


def parse_quran_tafsir():
    """Parse tafsir al-Jalalayn from http://www.altafsir.com/Al-Jalalayn.asp, after
    that PDF was processed with `pdftotext -nopgbrk Al_Jalalain_Eng.pdf`.
    """
    quran = []
    surah = []
    s, v = 1, 1
    in_verse = False
    verse = []

    def add_verse(verse, surah):
        surah.append(" ".join(verse))

    def add_line(line, verse):
        """Add line and replace for Arabic ligatures (salawat)"""
        verse.append(line.strip().replace("(s)", "ﷺ‎"))

    with open("Al_Jalalain_Eng.txt", "r") as f:
        for line in f.readlines():
            if line == "\n": continue
            if re.match("\d+\w*", line): continue
            elif line.startswith("[%d:%d]" % (s, v)):
                in_verse = True
            elif line.startswith("[%d:%d]" % (s, v + 1)):
                add_verse(verse, surah)
                verse = []
                v += 1
                in_verse = True
            elif line.startswith("[%d:1]" % (s + 1)):
                add_verse(verse, surah)
                verse = []
                quran.append(surah)
                surah = []
                s += 1
                v = 1
                in_verse = True
            elif (line.startswith("Medinese") or line.startswith("Meccan") or
                  line.startswith("[Consists") or  # [Consists end surah 5
                  line.startswith("Mecca, consisting") or  # end surah 73
                  line.startswith("This was revealed")):
                if s == 26 and v == 200:
                    # only line starting with "Meccan" that is part of a verse
                    add_line(line, verse)
                else:
                    in_verse = False
            elif in_verse:
                add_line(line, verse)
    add_verse(verse, surah)
    quran.append(surah)
    assert sum([len(s) for s in quran]) == 6236, "Missing verses!"
    return quran


class Quran:
    """Interface to get ayahs from the Quran."""
    surah_lengths = (7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6)

    surah_names = [s.attrib["tname"] for s in ET.parse("quran-data.xml").getroot().find("suras")]

    def __init__(self, data: str) -> None:
        if data == "arabic":
            self.text = parse_quran("quran-uthmani.txt")
        elif data == "translation":
            self.text = parse_quran("en.ahmedraza")
        elif data == "tafsir":
            self.text = parse_quran_tafsir()

    def get_surah(self, surah: int) -> str:
        """Get surah by number."""
        return self.text[surah - 1]

    def get_ayah(self, surah: int, ayah: int) -> str:
        """Get verse by surah and ayah numbers."""
        return self.text[surah - 1][ayah - 1] + " (%d:%d)" % (surah, ayah)

    def get_ayahs(self, surah: int, a: int, b: int) -> str:
        """Get range of Ayahs."""
        return " ".join(self.text[surah - 1][a - 1:b]) + " (%d:%d-%d)" % (surah, a, b)

    @staticmethod
    def get_random_ayah() -> Tuple[int, int]:
        surah = randint(1, 114)
        ayah = randint(1, Quran.get_surah_length(surah))
        return surah, ayah

    @staticmethod
    def get_next_ayah(s: int, a: int) -> Tuple[int, int]:
        length = Quran.get_surah_length(s)
        if a == length:
            s = s + 1 if s < 114 else 1
            a = 1
        else:
            a += 1
        return s, a

    @staticmethod
    def get_previous_ayah(s: int, a: int) -> Tuple[int, int]:
        if a == 1:
            s = s - 1 if s > 1 else 114
            a = Quran.get_surah_length(s)
        else:
            a -= 1
        return s, a

    @staticmethod
    def exists(s: int, a: int) -> bool:
        return 0 < s < 115 and 0 < a <= Quran.get_surah_length(s)

    @staticmethod
    def get_surah_length(surah: int) -> int:
        return Quran.surah_lengths[surah - 1]

    @staticmethod
    def get_surah_name(surah: int) -> str:
        return Quran.surah_names[surah - 1]


def make_index():
    """An index of the Surahs in the Quran, formatted to send over Telegram."""
    chapters = Quran.surah_names[:]
    # padding...
    for i in range(9):
        chapters[i] = " " + chapters[i] + " " * (14 - len(chapters[i]))
    for i in range(9, 58):
        chapters[i] += " " * (14 - len(chapters[i]))

    index = []
    left = range(1, 58)
    right = range(58, 115)
    for i, j in zip(left, right):
        index.append("/{} <code>{}</code>/{} {}"
                     .format(i, chapters[i - 1], j, chapters[j - 1]))
    return "\n".join(index)


def save_json(quran):
    """Save Quran to a json file."""
    import json

    with open("quran.json", "w") as f:
        json.dump(quran, f, ensure_ascii=False)
