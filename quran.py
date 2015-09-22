# -*- coding: utf-8 -*-
import re
from random import randint


def parse_quran_trans():
    quran = []
    surah = []
    s = 1

    def process_verse(verse):
        """Add verse and replace for Arabic ligatures (salawat)"""
        return (verse.strip()
                .replace("– peace and blessings be upon him", 'ﷺ‎'))

    with open("en.ahmedraza", 'r') as f:
        for line in f.readlines():
            if line == '\n': continue
            if line[:3] == "#==": break
            verse = line.split('|')
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
    quran = []
    surah = []
    s, v = 1, 1
    in_verse = False
    verse = []

    def add_verse(verse, surah):
        surah.append(' '.join(verse))

    def add_line(line, verse):
        """Add line and replace for Arabic ligatures (salawat)"""
        verse.append(line.strip().replace("(s)", 'ﷺ‎'))

    with open("Al_Jalalain_Eng.txt", 'r') as f:
        for line in f.readlines():
            if line == '\n': continue
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


class Quran(object):
    surah_lengths = [0, 7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6]
    # [0] for normal numbering

    def __init__(self, data):
        if data == "translation":
            self.text = parse_quran_trans()
        elif data == "tafsir":
            self.text = parse_quran_tafsir()

    def getSurah(self, surah):
        """Get surah by number."""
        return self.text[surah - 1]

    def getAyah(self, surah, ayah):
        """Get verse by surah and ayah numbers."""
        return self.text[surah - 1][ayah - 1] + " (%d:%d)" % (surah, ayah)

    def getAyahs(self, surah, a, b):
        """Get range of Ayahs as tuple """
        return ' '.join(self.text[surah - 1][a - 1:b]) + " (%d:%d-%d)" % (surah, a, b)

    @classmethod
    def getRandomAyah(cls):
        surah = randint(1, 114)
        ayah = randint(1, Quran.surah_lengths[surah])
        return surah, ayah

    @classmethod
    def getNextAyah(cls, s, a):
        length = Quran.surah_lengths[s]
        if a == length:
            s = s + 1 if s < 114 else 1
            a = 1
        else:
            a += 1
        return s, a

    @classmethod
    def getPreviousAyah(cls, s, a):
        if a == 1:
            s = s - 1 if s > 1 else 114
            a = 1
        else:
            a -= 1
        return s, a
