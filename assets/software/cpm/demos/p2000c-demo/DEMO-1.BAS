0 REM Demo-programma P2000-C scherm-besturing
10 DEF FNP$(X,Y)=CHR$(13)+CHR$(27)+"Y"+CHR$(31+X)+CHR$(31+Y)
11 DEF FNS$=CHR$(27)+"0"+CHR$((IN AND 1)+2*KN+16*NG+32*UN+32*(IN AND 2)):IN=2
12 DEF FNG$(X,Y,C$)=CHR$(13)+CHR$(27)+C$+CHR$(X MOD 256)+LEFT$(CHR$(aar door...":GOSUB 1000:GOSUB 1000:IN=2:PRINT FNS$;:FOR X=4 TO 240 STEP 10:PRINT FNG$(0,X,"m")FNG$(255,X,"M");:NEXT:GOSUB 1000:GOSUB 1000
300 PRINT G1$;:GOSUB 1310
310 PRINT FNP$(9,26)"Een vierkant...":GOSUB 1000:PRINT FNG$(10,10,"m")FNG$(10,235,"M")FNG$X\256),1+(GM<2 OR INSTR(GM$,C$)=0))+CHR$(Y MOD 256)+LEFT$(CHR$(Y\256),1+(INSTR(GM$,C$)=0)):GM$="UywFf":GM=0
100 SA$=CHR$(27):SU$=SA$+"c":SI$=SA$+"L":SD$=SA$+"l":SQ$=SA$+"R":SV$=SA$+"N":SW$=SA$+"O":SS$=SA$+"k":G0$=SA$+"4":SC$=CHR$(12):G1$=SC$+SA$+"5":G2$=S(500,235,"M"):PRINT FNG$(500,10,"M")FNG$(10,10,"M"):GOSUB 1000
320 PRINT FNP$(10,29)"en een":GOSUB 1000:PRINT FNG$(127,14,"m")FNG$(14,175,"M")FNG$(127,231,"M"):PRINT FNG$(496,175,"M")FNG$(127,14,"M"):GOSUB 1000:PRINT FNP$(11,29)"vlieger.":GOSUB 1000
330 C$+SA$+"3":SA$=SA$+"C":SR$=CHR$(13):SH$=CHR$(1)
200 NG=1:IN=2:PRINT SC$;FNS$;FNP$(1,1);SR$;:PRINT "   P H I L I P S    P 2 0 0 0 - C    Scherm-besturing    D E M O";:PRINT SPC(15);:NG=0:IN=1:PRINT FNS$:ST=0
205 PRINT FNP$(5,1)"We zetten de cursor uit..."PRINT G1$:GOSUB 1300
340 H=60:PRINT FNG$(127-H,0,"m")FNG$(127,238,"M")FNG$(127+H,0,"M")
350 X=6:WHILE X<238:PRINT FNG$(127-H+X/(238/H),X,"m")FNG$(127+H-X/(238/H),X,"M");:X=X+(240-X)/(238/H):WEND:GOSUB 1000
360 PRINT FNP$(4,2)"Waar blijft de trein ?":GOS:GOSUB 1000:PRINT SU$:GOSUB 1000:PRINT "Dit was ESC-c"
210 PRINT FNP$(10,1)"Laat deze regel 1 zakken...":GOSUB 1000:PRINT FNP$(10,1)SI$;:GOSUB 1000:PRINT "Dit was met de LI (ESC-L)":GOSUB 1000
220 PRINT FNP$(15,1)"laat deze regel 1 omhoog...":GOSUB 1000:UB 1000:GOSUB 1000:GOSUB 1000:PRINT FNP$(6,2)"Die komt vast niet meer !":GOSUB 1000
370 PRINT G1$:GOSUB 1300:
380 PRINT FNP$(9,28)"Een cirkel...":GOSUB 1000:H=60:PRINT FNG$(127,120+H,"m");:FOR X=0 TO 2*3.2 STEP .1:PRINT FNG$(127+H*SIN(X),120+H*COS(X),"M"PRINT FNP$(13,1)SD$;:GOSUB 1000:PRINT FNP$(15,1)"Dit was met de LD (ESC-l)":GOSUB 1000
234 PRINT FNP$(20,1)"Laat het scherm even draaien...":GOSUB 1000:FOR X= 1 TO 80:PRINT FNP$(2,1)SW$;:NEXT:GOSUB 1000:PRINT FNP$(20,1)"Dat was dan met ESC-0";:GOSUB 1000);:NEXT
390 PRINT FNP$(14,24)"Een halve cirkel...":GOSUB 1000:H=H+4.4:PRINT FNG$(127+H,120,"m");:FOR X=1.69 TO 4.71 STEP .1:PRINT FNG$(127+H*SIN(X),120+H*COS(X),"M");:NEXT:H=H-4.5:GOSUB 1000:PRINT FNP$(2,2)SS$
400 PRINT FNP$(19,19)"En wat leuke golfjes e
240 PRINT FNP$(19,1)SS$"En dan ook natuurlijk terug...":GOSUB 1000:PRINT SV$FNP$(2,1);:FOR X= 1 TO 80:PRINT " ";:NEXT:PRINT SQ$;:GOSUB 1000:PRINT FNP$(21,1)"En dat kan met ESC-N en ESC-R":GOSUB 1000
250 IF ST=0 THEN ST=1:GOSUB 1100:PRINT FNP$(5,1)"We zetrbij...";:FOR Y=-8 TO 0 STEP 4:PRINT FNG$(127-H,120+Y,"m");:FOR X=127-H TO 127+H STEP 2:PRINT FNG$(X,120+Y+5*SIN(X/(H/6.4)),"M");:NEXT:NEXT
410 H=H+4:PRINT FNG$(127-H,120,"m")FNG$(127-H,235,"M")FNG$(127+H,235,"M")FNG$(127+H,120,"M")
420 PRINT FNP$(19,18)ten de cursor weer aan...";:GOSUB 1000:PRINT SA$:GOSUB 1000:PRINT"Dat was ESC-C":GOTO 210
260 GOSUB 1200:PRINT FNP$(5,1)"Dan wat 'graphics'...":GOSUB 1000:PRINT SC$G1$FNP$(5,2)"Ook nu de cursor weer uit...";:GM=1:GOSUB 1000:PRINT SU$:GOSUB 1300
270 PRINTSS$"Nog wat sterretjes als show..."
430 H=H-15:X=5.2:GOSUB 440:X=5.44:GOSUB 440:X=2.2:GOSUB 440:X=2.42:GOSUB 440:GOSUB 1000:GOTO 450
440 Y=127+H*SIN(X):Z=120+H*COS(X):PRINT FNG$(Y,Z-8,"m")FNG$(Y,Z+8,"M");:PRINT FNG$(Y-6,Z,"m")FNG$(Y+6,Z,"M");:RETURN
450 FNP$(10,2)"Ter informatie:":PRINT " Het beeldscherm kan dan 21 regels van 64 karakters bevatten...":GOSUB 1000
280 PRINT FNP$(13,2)"Maar dan ook 511x252 of 255x252 punten...":GOSUB 1000
290 GOSUB 1000:GOSUB 1000:PRINT FNP$(18,25)"Niet erg mooi, streep m PRINT FNP$(4,18)SS$" E N  W A T  Z O U  H I E R ":PRINT FNP$(5,18)" N U  M O E T E N  S T A A N":GOSUB 1000
460 PRINT FNP$(19,10)"D i t  a l l e s   i s  k i n d e r s p e l"FNP$(20,19)"V o o r  d e  P 2 0 0 0 - C"
470 FOR X=12 TO 26:PRINT FNG$(30,X,"m")FNG$(220,X,"M");:PRINT FNG$(30,51-X,"m")FNG$(220,51-X,"M");:NEXT:GOSUB 1000:GOSUB 1000:GOSUB 1000
480 PRINT SA$G0$:GM=0:GOTO 200
1000 REM *** Wacht ***
1010 FOR X=1 TO 2000:NEXT:RETURN
1100 REM *** Maak beeld schoon ***
1110 PRINT FNP$(2,1)"En nu eenееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее leeg beeld...";:GOSUB 1000:PRINT FNP$(2,1);:FOR X=1 TO 23:PRINT SD$SR$;:NEXT:GOSUB 1000:RETURN
1200 REM *** Maak beeld schoon - 2
1210 PRINT FNP$(2,1)"En nu een leeg beeld...";:GOSUB 1000:FOR X=1 TO 23:PRINT SI$SR$;:NEXT:GOSUB 1000:RETURN
1300 REM ****ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее