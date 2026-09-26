1 REM BASICODE 2 standaard inplementatie 21/4/83
2 REM                      door Henk Wevers
3 REM  Voor aanpassing aan computer/terminal
4 REM  zie basicode.doc file op deze diskette
5 REM initialisatie
6 REM Deze versie voor MBASIC 5.21 en hoger ! ( u bij het kopen tegen komt."3120 PRINT:PRINT"We laten eerst de mensen passeren"3130 PRINT"met wie u te maken krijgt."3140 GOSUB90003150 IFJ$="24" THENGOSUB80003160 PRINT:PRINT"De makelaar:"3170 PRINT:PRINT"De makelaar is een door de rechtbank"3180 met INKEY$)
7 PRINT CHR$(27);"*";CHR$(0);CHR$(0);CHR$(0);CHR$(26);:WIDTH(255)
10 GOTO 1000
19 REM regels 20-100 clear a, niet nodig voor mbasic
20 GOTO 1010
99 REM  regel 100-110 clear screen
100 PRINT CHR$(12):RETURN
109 REM regel 110 - 120 set curPRINT"beedigd functionaris."3190 PRINT"Hij adviseert en bemiddelt bij"3200 PRINT"koop en / of verkoop."3210 PRINT"Hij verricht taxaties en bemiddelt zo"3220 PRINT"nodig bij het aanvragen van subsidie"3230 PRINT"of gemeentegarantie en kan helpen bij"3sor op HO en VE
110 REM TERMINAL = 24 X 80 !
111 IF HO>79 THEN HO=79
112 IF VE>23 THEN VE=23
113 PRINT CHR$(27);"Y";CHR$(VE+32);CHR$(HO+32);
115 RETURN
119 REM regel 120-130 haal cursorpositie in HO en VE
120 IF HO > 79 THEN HO=80
121 IF VE > 23 TH240 PRINT"financiering en verzekering."3250 PRINT"Hij kent de plaatselijke woningsituatie"3260 PRINT"en weet hoe de prijzen ongeveer liggen."3270 GOSUB90003280 IFJ$="24" THENGOSUB80003290 PRINT:PRINT"De notaris:"3300 PRINT:PRINT"De notaris is een dooEN VE=23
122 REM  voor terminal 24 x 80
124 RETURN
200 IN$=INKEY$:RETURN
210 GOSUB 200:IF IN$="" THEN 210
211 RETURN
250 PRINT CHR$(7);:RETURN
260 RV=RND(1):RETURN
270 FR=FRE(2):RETURN
300 SR$=STR$(SR)
301 O7=LEN(SR$):IF O7=0 THEN RETURN
302 IF 