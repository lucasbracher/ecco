# Copyright 2011, 2017, Lucas Bracher
# Code licensed under LGPL v3.0
# Grammar and ecco! Language licensed under Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0) 

from __future__ import division
from decimal import *
from math import floor, ceil, log, e, sin, pi
from os.path import exists
from pathlib import Path
from ply.lex import lex
from ply.yacc import yacc
from tabulate import tabulate

import re
import platform
if platform.system() == 'Windows':
    import pyreadline
else:
    import readline
import string
import sys
import time

from pyo import Server, Fader, Sine
#s = Server(nchnls=1, audio='jack').boot()
#s = Server(nchnls=2, audio='pulseaudio').boot()
s = Server(nchnls=2).boot()
s.start()

class Lexer(object):
    tokens = [ 'NOTE', 'IS', 'OF', 'FLOAT', 'FRACTION', 'INTEGER', 'HERTZ', 
        'INTERVAL_NUMBER', 'INTERVAL_QUALITY', 'ABOVEBELOW', 'PLUSMINUS', 
        'COMMA_TYPE', 'COMMA', 'CENT', 'DROP', 'COMPARE', 
        'GENERATE', 'BASE', 'TRANSPOSE', 'UPDOWN', 'PLAY', 'TO', 'RPAREN',
        'LPAREN', 'LOAD', 'SAVE', 'FILENAME', 'PRINT', 'ON', 'OFF', 'END_STMT' ]

    t_ignore           = ' \t'
    t_NOTE             = r'([A-G]b+|[A-G]\#*|[X-Z])'
    t_IS               = r'\bis\b'
    t_OF               = r'\bof\b'
    def t_FLOAT(self, t):
        r'\b([0-9]+\.([0-9]+\b)?|\.[0-9]+)\b'
        t.value = float(t.value)
        return t

    def t_FRACTION(self, t):
        r'\b[0-9]+/[0-9]+\b'
        t.value = int(t.value.split('/')[0]) / int(t.value.split('/')[1])
        return t
        
    def t_INTEGER(self, t):
        r'\b[0-9]+\b'
        t.value = int(t.value)
        return t
        
    t_HERTZ            = r'\bhertz\b'
    t_INTERVAL_NUMBER  = r'\b(third|fourth|fifth|sixth|octave|unison)s?\b'
    t_INTERVAL_QUALITY = r'(major|minor|perfect)' 
    t_ABOVEBELOW       = r'\b(above|below)\b'
    t_PLUSMINUS        = r'\b(plus|minus)\b'
    t_COMMA_TYPE       = r'\b(syntonic|pythagorean)\b'
    t_COMMA            = r'\bcommas?\b'
    #t_BPS              = r'\bbps\b' # In a furure version
    t_CENT             = r'\bcents?\b'
    t_DROP             = r'\bdrop\b'
    t_COMPARE          = r'\bcompare\b'
    t_GENERATE         = r'\bgenerate\b'
    t_BASE             = r'\bbase\b'
    t_TRANSPOSE        = r'\btranspose\b'
    t_UPDOWN           = r'\b(up|down)\b'
    t_PLAY             = r'\bplay\b'
    t_TO               = r'\bto\b'
    #t_RPAREN           = r'\b\)\b' # In a future version
    #t_LPAREN           = r'\b\(\b' # In a future version
    t_RPAREN           = r'\)'
    t_LPAREN           = r'\('    
    t_LOAD             = r'\bload\b'
    t_SAVE             = r'\bsave\b'
    t_FILENAME         = r'(\S+)+\.ecco'
    t_PRINT            = r'\bprint\b'
    t_ON               = r'\bon\b'
    t_OFF              = r'\boff\b'
    t_END_STMT         = r';'

    def t_error(self, t):
        print("Unknown token: %s" % t)
        #raise Exception(t)


class Audio():
    #def __init__(self):

    def playScale(self, lista):
        for fr in lista:
            f = Fader(fadein=0.1, fadeout=0.1, dur=1, mul=.5)
            osc = Sine(freq=fr, mul=f).out()
            f.play()
            time.sleep(1)

    def playChord(self, lista):
        f = Fader(fadein=0.1, fadeout=0.1, dur=3, mul=.5)
        m = []
        for fr in lista:
            m.append(Sine(freq=fr, mul=f).out())
        f.play()
        time.sleep(3)


class Statements():
    def __init__(self):
        self.statements = []

    def add(self, stmt):
        self.statements.append(stmt)

    def drop(self):
        self.statements = []

    def list(self):
        return self.statements


class Parser():
    def __init__(self, statements):
        self.starting = "definition"
        self.d = dict()
        self.statements = statements
        self.print = True

    def freqprim(self):
        return sorted(self.d.items(), key=lambda x : x[1][1])[0][1][0]

    def log2(self, i):
        return log(i)/log(2)

    def insere(self, nota, freq):
        if (len(self.d) == 0) or (len(self.d) == 1 and nota in self.d):
            self.d[nota] = [freq, 0.0]
            #self.freqprim = freq
        else:
            if nota in self.d and self.d[nota][1] == 0.0:
                print("Can't change base note.")
            else:
                f = freq / (2 ** floor(self.log2( freq / self.freqprim() )))
                c = self.log2( f / self.freqprim() ) * 1200
                self.d[nota] = [f, c]

    def dev_cent(self, cent):
        getcontext().prec = 3
        fl = floor(cent/100) * 100
        ce = ceil(cent/100) * 100
        #print("%f cents, %f floor, %f ceil" % (cent, fl, ce))
        if abs(cent) < 1e-5 or abs(cent-fl) < 1e-5:
            return 0.0
        else:
            if (cent - fl) < (ce - cent):
                return cent-fl
            else:
                return cent-ce


    def lista(self):
        if self.print:
            data = []
            for k, v in sorted(self.d.items(), key=lambda x : x[1][1]):
                data.append([k, v[0], v[1], self.dev_cent(v[1])])
            #print(data)
            print(tabulate(data, headers=["Note","Hertz", "Cents", "Deviation"]))



    def make_soundfile(self, freq, data_size, fname):
        print("Suspended.")
        return

        frate = 11025.0
        amp = 8000.0

        sine_list = []
        for x in range(data_size):
            ##sine_list.append(sin(2.0 * pi * freq * (x / frate)))
            sine_list.append((sin(2.0 * pi * freq * (x / frate)) / 2.0) + (sin(2.0 * pi * freq * 1.5 * (x / frate)) / 2.0))
        wav_file = wave.open(fname + ".wav", "w")
        wav_file.setparams((1, 2, int(frate), data_size, "NONE", "not compressed"))
        print("Generating %s..." % fname)
        for s in sine_list:
            wav_file.writeframes(struct.pack('h', int(s * amp / 2)))
        wav_file.close()
    
    def p_definition(self, p): #define note by frequency
        """definition : NOTE IS INTEGER HERTZ END_STMT
                    |   NOTE IS FLOAT HERTZ END_STMT"""
        self.insere(p[1], p[3])
        self.lista()

    def p_definitions2(self, p): #define note by other note and hertz deviation
        """definition : NOTE IS NOTE PLUSMINUS INTEGER HERTZ END_STMT
                    |   NOTE IS NOTE PLUSMINUS FLOAT HERTZ END_STMT"""
        self.insere(p[1], self.d[p[3]][0] + self.parse_plusminus(p[4], p[5]))
        self.lista()

    def p_definitions3(self, p): #define note by other note and fraction of comma
        "definition : NOTE IS NOTE PLUSMINUS FRACTION OF COMMA_TYPE COMMA END_STMT"
        self.insere(p[1], self.d[p[3]][0] * (2 ** (self.parse_plusminus(p[4], p[5] * self.parse_comma(p[7])) /1200)))
        self.lista()

    def p_definitions4(self, p): #define note by other note and integer,float comma
        """definition : NOTE IS NOTE PLUSMINUS INTEGER COMMA_TYPE COMMA END_STMT
                    |   NOTE IS NOTE PLUSMINUS FLOAT COMMA_TYPE COMMA END_STMT"""
        self.insere(p[1], self.d[p[3]][0] * (2 ** (self.parse_plusminus(p[4], p[5] * self.parse_comma(p[6])) /1200)))
        self.lista()

    def p_definitions5(self, p): #define note by other and cents
        """definition : NOTE IS NOTE PLUSMINUS INTEGER CENT END_STMT
                    |   NOTE IS NOTE PLUSMINUS FLOAT CENT END_STMT"""
        self.insere(p[1], self.d[p[3]][0] * (2 ** (self.parse_plusminus(p[4], p[5]) /1200)))
        self.lista()

    def p_definitions6(self, p): #define note by pure interval
        "definition : NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE END_STMT"
        self.insere(p[1], self.d[p[7]][0] * (self.parse_interval(p[4], p[5], p[6]) ** p[3]))
        self.lista()

    def p_definitions7(self, p): #define note by pure interval and hertz deviation
        """definition : NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS INTEGER HERTZ END_STMT
                    |   NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS FLOAT HERTZ END_STMT"""
        self.insere(p[1], (self.d[p[7]][0] * (self.parse_interval(p[4], p[5], p[6]) ** p[3])) + self.parse_plusminus(p[8], p[9]))
        self.lista()

    def p_definitions8(self, p): #define note by pure interval and fraction of a comma
        """definition : NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS FLOAT OF COMMA_TYPE COMMA END_STMT
                    |   NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS FRACTION OF COMMA_TYPE COMMA END_STMT"""
        self.insere(p[1], self.d[p[7]][0] * (self.parse_interval(p[4], p[5], p[6]) ** p[3]) * (2 ** (self.parse_plusminus(p[8], p[9] * self.parse_comma(p[11])) /1200)))
        self.lista()

    def p_definitions9(self, p): #define note by pure interval and integer comma
        "definition : NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS INTEGER COMMA_TYPE COMMA END_STMT"
        self.insere(p[1], self.d[p[7]][0] * (self.parse_interval(p[4], p[5], p[6]) ** p[3]) * (2 ** (self.parse_plusminus(p[8], p[9] * self.parse_comma(p[10])) /1200)))
        self.lista()

    def p_definitions10(self, p): #define note by pure interval and cents
        """definition : NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS FLOAT CENT END_STMT
                    |   NOTE IS INTEGER INTERVAL_QUALITY INTERVAL_NUMBER ABOVEBELOW NOTE PLUSMINUS INTEGER CENT END_STMT"""
        self.insere(p[1], self.d[p[7]][0] * (self.parse_interval(p[4], p[5], p[6]) ** p[3]) * (2 ** (self.parse_plusminus(p[8], p[9]) /1200)))
        #self.insere(p[1], p[3] * self.parse_interval(p[4], p[5], p[6]) * self.d[p[7]][0] * (2 ** (self.parse_plusminus(p[8], p[9]) /1200)))
        self.lista()

    def p_definitions11(self, p): #define note by cent #deprecated
        """definition : NOTE IS INTEGER CENT ABOVEBELOW NOTE END_STMT
                    |   NOTE IS FLOAT CENT ABOVEBELOW NOTE END_STMT"""
        self.insere(p[1], self.d[p[6]][0] * (2 ** (self.parse_cents(p[3], p[5]) /1200)))
        self.lista()

    def p_definitions12(self, p): #drop all definitions
        "definition : DROP END_STMT"
        self.d.clear()
        self.statements.drop()
        self.lista()

    def p_definitions13(self, p): #
        "definition : DROP NOTE END_STMT"
        if self.d[p[2]][1] == 0:
            print("Cannot drop base note.")
        else:
            self.d.__delitem__(p[2])
            self.lista()

    def p_definitions14(self, p):
        "definition : COMPARE NOTE NOTE END_STMT"
        dif_cents = abs(self.d[p[2]][1] - self.d[p[3]][1])
        t = [0, 0, float("+inf")]
        for a in range(1, 15):
            for b in range(1, 15):
                if abs(self.d[p[2]][0]*a - self.d[p[3]][0]*b) < t[2]:
                    t[2] = abs(self.d[p[2]][0]*a - self.d[p[3]][0]*b)
                    t[0] = a
                    t[1] = b
        print("  %s %.3f hertz and %s %.3f hertz are %.3f (%.3f) cents apart, beat at %.1f hertz at %d harmonic and %d harmonic" % 
                (p[2], self.d[p[2]][0], p[3], self.d[p[3]][0], dif_cents, 1200-dif_cents, t[2], t[0], t[1]))

    def p_definitions15(self, p):
        "definition : GENERATE END_STMT"
        for k, v in self.d.items():
            #daniweb 263775
            self.make_soundfile(v[0], 11025, k)

    def p_definitions16(self, p):
        "definition : NOTE IS BASE END_STMT"
        #self.freqprim = self.d[p[1]][0]
        dif_cents = self.d[p[1]][1]
        for k, v in self.d.items():
            #to com preguica de pensar, refatorar depois
            self.d[k] = [self.d[k][0], self.d[k][1] - dif_cents]
            if self.d[k][1] < 0:
                self.d[k] = [self.d[k][0] * 2, self.d[k][1]]
            if self.d[k][1] >= 1200:
                self.d[k] = [self.d[k][0] / 2, self.d[k][1]]    
            self.d[k] = [self.d[k][0], self.d[k][1] % 1200]
        self.lista()

    def p_definitions17(self, p):
        """definition : TRANSPOSE INTEGER CENT UPDOWN END_STMT
                    |   TRANSPOSE FLOAT CENT UPDOWN END_STMT"""
        #print(type(self.d))
        for k, v in self.d.items():
            self.d[k] = [self.d[k][0] * (2 ** (self.parse_cents(p[2], p[4])/1200)), self.d[k][1]]
            #if self.d[k][1] == 0.0:
            #    self.freqprim = self.d[k][0]
        self.lista()

    def p_definitions18(self, p):
        """definition : TRANSPOSE NOTE TO INTEGER HERTZ END_STMT
                    |   TRANSPOSE NOTE TO FLOAT HERTZ END_STMT"""
        const = p[4] / self.d[p[2]][0]
        for k, v in self.d.items():
            self.d[k] = [self.d[k][0] * const, self.d[k][1]]
            #if self.d[k][1] == 0.0:
                #self.freqprim = self.d[k][0]
        self.lista()

    def p_definitions19(self, p):
        "definition : PLAY END_STMT"
        lista = []
        for k, v in sorted(self.d.items(), key=lambda x : x[1][1]):
            lista.append(v[0])
        #map(lambda x: a[x:x+1], range(len(a)))
        audio.playScale(lista)

    def p_definitions20(self, p):
        "definition : PLAY notes END_STMT"
        lista = []
        errorlist = False
        #map(lambda x: a[x:x+1], range(len(a)))
        for a in p[2]:
            if a in self.d:
                lista.append(self.d[a][0])
            else:
                raise Exception("%s not found" % a)
                errorlist = True
        if not errorlist:
            audio.playChord(lista)

    def p_definitions21(self, p):
        "definition : PLAY groupnotes END_STMT"
        #codigo replicado. refatorar.
        lista = []
        errorlist = False
        for gr in p[2]:
            for a in gr:
                if a in self.d:
                    lista.append(self.d[a][0])
                else:
                    raise Exception("%s not found" % a)
                    errorlist = True
            if not errorlist:
                audio.playChord(lista)

    def p_definitions22(self, p):
        "definition : LOAD FILENAME END_STMT"
        my_file = Path(p[2])
        if my_file.is_file():
            file = open(p[2], "r")
            self.print = False
            for line in file.readlines():
                print(line.replace("\n", ""))
                parser.parse(line.replace("\n", ""))
            self.print = True
            print("")
            self.lista()
        else:
            print("File doesn't exist.")

    def p_definitions23(self, p):
        """definition : PRINT ON END_STMT
                      | PRINT OFF END_STMT"""
        if p[2] == "on":
            self.print = True
        elif p[2] == "off":
            self.print = False
        else:
            raise Exception("Unknown parameter")


    def p_definitions24(self, p):
        "definition : SAVE FILENAME END_STMT"
        if exists(p[2]):
            print("File already exists")
            return
        if not re.match(Lexer.t_FILENAME, p[2]):
            print("Filename must use regular characters and end with .ecco")
            return
        with open(p[2], 'w') as f:
            for l in self.statements.list():
                f.write(l+'\n') 

    #def p_error(self, p):
    #    "definition: statement | JUNK statement"
    #    print "error."

    def p_groupnotes(self, p):
        "groupnotes : LPAREN notes RPAREN"
        p[0] = (p[2],)

    def p_groupnotes2(self, p):
        "groupnotes : groupnotes LPAREN notes RPAREN"
        p[0] = p[1] + (p[3],)

    def p_notes(self, p):
        "notes : NOTE"
        p[0] = (p[1],)

    def p_notes2(self, p):
        "notes : notes NOTE"
        p[0] = p[1] + (p[2],)

    def parse_comma(self, cm):
        if cm == "syntonic":
            return 21.5062895967
        elif cm == "pythagorean":
            return 23.460010
        else:
            raise Exception("Unknown comma")
        
    def parse_cents(self, cn, ab):
        if ab == "above" or ab == "up":
            return cn
        elif ab == "below" or ab == "down":
            return -cn
        else:
            raise Exception("Unknown parameter")
        
    def parse_plusminus(self, pm, un):
        if pm == "plus":
            return un
        elif pm == "minus":
            return -un
        else:
            raise Exception("Unknown parameter")

    def parse_interval(self, quality, number, ab):
        if number == "octave" or number == "octaves":
            if quality == "":
                return 2
            else:
                raise Exception("Unknown octave interval")
        elif number == "unison" or number == "unisons":
            if quality == "":
                return 1
            else:
                raise Exception("Unknown unison interval")                
        elif number == "third" or number == "thirds":
            if quality == "major":
                prop = 5/4
            elif quality == "minor":
                prop = 6/5
            else:
                raise Exception("Unknown third interval")
        elif number == "fourth" or number == "fourths":
            if quality == "perfect":
                prop = 4/3
            else:
                raise Exception("Unknown fourth interval")
        elif number == "fifth" or number == "fifths":
            if quality == "perfect":
                prop = 3/2
            else:
                raise Exception("Unknown fifth interval")
        elif number == "sixth" or number == "sixths":
            if quality == "major":
                prop = 5/3
            elif quality == "minor":
                prop = 8/5
            else:
                raise Exception("Unknown sixth interval")
        else:
            raise Exception("Unknown number interval")
        if ab == "above":
            return prop
        elif ab == "below":
            return 1/prop
        else:
            raise Exception("Unknown interval operator")
            
    def p_error(self, p):
        print("Didn't get it.")
        #raise Exception(p)

    tokens = Lexer.tokens

if __name__ == '__main__':
    statements = Statements()
    lexer = lex(module=Lexer())
    parserclass = Parser(statements)
    parser = yacc(module=parserclass, write_tables=0)
    audio = Audio()
    while True:
        print("")
        try:
            stmt = input("ecco!> ")
            parser.parse(stmt)
            statements.add(stmt)
        except KeyboardInterrupt:
            print("\nLeaving...\n")
            sys.exit()
        except:
            pass

