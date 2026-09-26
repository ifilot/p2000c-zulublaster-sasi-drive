1 ' SCREEN HANDLER ACTIVATOR DEMONSTRATION PROGRAM
2 ' COPYRIGHT (c) PHILIPS 1983
4 ' AUTHOR : P.   SCHWARZ   PHILIPS MAG PERCO
5 ' DATE WRITTEN : 13 JUNE 1982 (P2500), 10TH OCTOBER 1983 (P2000C)
6 ' STATUS DATE  : 12TH OCTOBER 1983
7 ' ************** QZ1%+6,QZ20%
520 POKE QZ1%+7,QZ21%:POKE QZ1%+8,QZ20%
550 QI%=USR2(QI%)			' Call routine for numeric entries
570 QZ5%=PEEK(QZ1%+9)			' Return code from Screen Handler
580 IF QZ5%=10 THEN GOSUB 950:GOTO 130	' For HELP. Delete this line if not used. **************************************************************
8 F$="A:SH.L"
9 GOSUB 11560				'Get Load address for Screen Handler
10 CLEAR ,SLAD!-1,512			' CLEAR must be done first in the prog.
11 REM ON ERROR GOTO 9000			' Error trapping routine
12 GOTO
720 QI%=0
721 IF QRK%(QI%)=QZ5% GOTO 725
722 QI%=QI%+1:IF QI%<=QLRK% GOTO 721
725 QRET%=QI%
730 PRINT CHR$(&H1B);"C";FNS(24,1);CHR$(&H1B);"K";:RETURN
795 '
796 '                    **********************
797 '                    * KEY INPUT ROUTIN 1000
13 '
14 '                     *************
15 '                     * T I T L E *
16 '                     *************
17 '
20 PRINT CHR$(12);ATT$;"pSCREEN HANDLER ACTIVATOR DEMONSTRATION PROGRAM                        Vers. 1.1";OFF$
22 REES *
798 '                    **********************
799 '
800 QA$=" ":GOSUB 820				' Key Input, any character
802 GOTO 824
804 QA$="Y":GOSUB 820				' Key Input, (default = Y)
806 IF QA$="N" OR QA$="n" THEN QA$="N" ELSE QA$="Y"
808 GOTO 824
810 QA$TURN
93 '
94 '              ****************************
95 '              * SCREEN HANDLER ACTIVATOR *
96 '              ****************************
97 '
100 PRINT FND$(24,1,MES$);		' User guidance on line 24. Remove if not needed *******
120 POKE="0":GOSUB 820				' Key Input, Numeric
811 IF QA%=13 THEN QA$="0"
812 QA%=ASC(QA$)-48:IF QA%<0 OR QA%>9 GOTO 810	' Return QA% with entered no.
814 GOTO 824
816 QA$=INPUT$(1):IF ASC(QA$)<>13 GOTO 816	' Key Input, only <CR>
818 GOTO 824
820 PRINT QA$;C QZ1%,1				' Set params (lines 120-520)
130 POKE QZ1%+1,VAL(MID$(QPOS$,5,2)):POKE QZ1%+2,VAL(MID$(QPOS$,1,2)):POKE QZ1%+3,VAL(MID$(QPOS$,3,2))
140 QZ2%=VAL(MID$(QPOS$,7,1)):POKE QZ1%+4,QZ2%
160 POKE QZ1%+10,0
170 QZ9%=VAL(MID$(QPOS$,8,1))
190 FOR QZ20HR$(&H15);:QA$=INPUT$(1)
821 QA%=ASC(QA$)
822 RETURN
824 IF QA%>31 THEN PRINT QA$				' Don't print control char.
825 RETURN
833 '
834 '                    ************************
835 '                    * CLEAR SCREEN ROUTINE *
836 '             %=1 TO QZ9%
200 POKE QZ1%+QZ20%+9,VAL(MID$(QKEY$,3*QZ20%-2,3))
220 NEXT
230 POKE QZ1%+QZ20%+9,0
240 ON (QZ2% MOD 5)+1 GOTO 250,250,420,440,460
250 QZ3=VARPTR(QDA$):QZ3=QZ3-65536!*(QZ3<32767)
270 QZ20%=INT(QZ3/256):QZ21%=QZ3-QZ20%*256
290 POKE QZ1%+5       ************************
837 '
840 PRINT FNS(FLIN,1);:FOR Q=FLIN+(NUM-1) TO FLIN STEP -1
842 PRINT FNS(Q,1);ESC$;"K";
844 NEXT Q
846 RETURN
853 '
854 '                    ************************
855 '                    * PRINT SCREEN ROUTI,QZ21%:POKE QZ1%+6,QZ20%
320 QZ3=VARPTR(QZA$):QZ3=QZ3-65536!*(QZ3<32767)
330 QZ20%=INT(QZ3/256):QZ21%=QZ3-QZ20%*256
350 POKE QZ1%+7,QZ21%:POKE QZ1%+8,QZ20%
370 QI%=USR2(QI%)			' Call the routine (Alpha-num)
380 QZ20%=PEEK(QZ1%+1)			' Length of exit stNE *
856 '                    ************************
857 '
860 FLIN=(FLIN-1)*80:HIB=INT(FLIN/256):LOB=FLIN-HIB*256:POKE QZ1%+34,LOB:POKE QZ1%+35,HIB
862 POKE QZ1%+36,NUM:POKE QZ1%+37,0
864 QI%=USR3(QI%)
866 QRET%=PEEK(QZ1%+37):RETURN
893 '
894 ' ring
400 QDA$=LEFT$(QZA$,QZ20%)
410 GOTO 570
420 QZ3=VARPTR(QDI%):GOTO 480
440 QZ3=VARPTR(QDS!):GOTO 480
460 QZ3=VARPTR(QDD#):POKE QZ1%+19,QD%
480 QZ3=QZ3-65536!*(QZ3<32767)
490 QZ20%=INT(QZ3/256)
500 QZ21%=QZ3-QZ20%*256
510 POKE QZ1%+5,QZ21%:POKE                   ************************
895 '                    * INFO SCREEN HANDLING *
896 '                    ************************
897 '
900 PRINT CHR$(12);FNS(1,1);ATT$+"p";:PRINT USING "SCREEN HANDLER ACTIVATOR INFO SCREEN NUMBER : ##                               ";PREC;:PRINT OFF$;
908 GET 1,1:REC=CVI(MID$(QL$,2*PREC+1,2)):LREC=CVI(MID$(QL$,2*(PREC+1)+1,2))-1
910 PRINT FNS(2,1);
912 FOR I=REC TO LREC
914 GET 1,I
916 PRINT LEFT$(QL$,INSTR(QL$,CHR$(13))-1)
918 NEXT I
920 PRINT OFF$HT$(Q1$,1))
2155 MES$="Type HELP KEY for info, CURSOR LEFT for previous field, UP for first field."
2160 ON (A MOD 5)+1 GOTO 2170,2180,2190,2200,2202
2170 M$="QDA$  = ":QDA$="0123456789":QPOS$="07091000"           ' Numeric ASCII
2175 GOTO 2220
2180 M;CHR$(7);FNS(24,1);"Continue <CR>, ESC to stop: ";:GOSUB 800
940 RETURN
943 '
944 '                    ********
945 '                    * HELP *
946 '                    ********
947 '
950 PRINT FNS(23,1);MH$;FNS(23,68);"Type <CR> : ";:GOSUB 816
9$="QDA$  = ":QDA$="ANY TEXT":QPOS$="07093010"             ' Alphanumeric
2185 GOTO 2220
2190 M$="QDI%  = ":QDI%=1234:QPOS$="07090420"                   ' Integer
2195 GOTO 2220
2200 M$="QDS!  = ":QDS!=1234.56:QPOS$="07090930"                ' Single Pr60 PRINT FNS(23,1);ESC$;"K";		' Clear line
970 RETURN
993 '
994 '                    ***********
995 '                    * M E N U *
996 '                    ***********
997 '
1000 GOSUB 10000 			' Initialisation Procedures
1001 PRINT"Do you need ec.
2201 GOTO 2220
2202 MH$="Read INFO Screen no. 8 / QD%":PRINT FNS(5,40);"QD% =":QDI%=2:QPOS$="05460120":GOSUB 100:QD%=QDI%
2203 ON QRET% GOTO 2150,2150
2204 IF QD%<1 OR QD%>6 THEN PRINT CHR$(7);:GOTO 2202
2210 PREC=7:M$="QDD#  = ":QDD#=.123456:QPOSgeneral information on this program Y/N : ";:GOSUB 804:IF QA$="N" GOTO 1010
1002 PREC=11:GOSUB 900:IF QA%=27 GOTO 1010
1003 PREC=12:GOSUB 900
1010 GOSUB 20
1020 PRINT FNS(4,13);"0 Exit to Command mode"
1030 PRINT FNS(6,13);"1 Screen Handler Activator"$="07091540"         ' Double Prec.
2220 MH$="Read INFO Screen no. 7 / "+LEFT$(M$,4)
2222 PRINT FND$(7,1,M$):GOSUB 100:ON QRET% GOTO 2150,2150
2230 IF K=0 GOTO 2260
2235 MH$="Read INFO Screen no. 5 / QKEY$":Q2$=QDA$:QDA$="111222333444555666"
2240 QPOS
1040 PRINT FNS(8,13);"2 Clear Screen Routine"
1050 PRINT FNS(10,13);"3 Print Screen Routine"
1100 PRINT FNS(4,1);"Select : ";:GOSUB 810
1110 IF QA%>3 THEN PRINT CHR$(7);:GOTO 1100
1120 IF QA%=0 THEN PRINT CHR$(12);INV$;"End of program";OFF$:CLEAR ,PE$="0909"+RIGHT$("0"+STR$(K*3),2)+"00":PRINT FND$(9,1,"QKEY$ = "):GOSUB 100:ON QRET% GOTO 2160,2150:QKEY$=QDA$
2250 QDA$=Q2$
2260 MH$="HELP message would be displayed here"
2265 PREC=8:PRINT FNS(11,1);"RESULTS WILL NOW APPEAR !":MES$="":QPOS$=Q1$:GOSUB 1EK(6)+256*PEEK(7)-1,512:END				' Reset memory
1130 ON QA% GOTO 1900,3000,4000
1893 '
1894 '              *********************************
1895 '              * DEMO SCREEN HANDLER ACTIVATOR *
1896 '              *********************************
18900
2270 FLIN=11:NUM=1:GOSUB 840			' Clear Line
2280 PRINT FNS(11,1);"RESULTS (Return Parameters): "
2290 PRINT"QPOS$ = ";QPOS$
2300 ON (A MOD 5)+1 GOTO 2310,2310,2320,2330,2340
2310 PRINT"QDA$ =>";QDA$;"<"
2315 GOTO 2350
2320 PRINT"QDI% =";QDI%:GOTO7 '
1900 PRINT FNS(14,1);"Do you want to read the INFO screens Y/N: ";:GOSUB 804:IF QA$="N" GOTO 2130
2000 PREC=1
2005 GOSUB 900:IF QA%=27 OR PREC=8 GOTO 2130
2020 PREC=PREC+1:GOTO 2005
2130 GOSUB 20
2140 PRINT"Now try using the screen handler."
214 2350
2330 PRINT"QDS! =";QDS!:GOTO 2350
2340 PRINT"QDD# =";QDD#
2350 PRINT"QRET% =";QRET%
2360 PRINT FNS(22,1);OFF$;"Type <CR> to continue : ";OFF$;:GOSUB 800
2380 GOTO 2130
2993 '
2994 '           *********************
2995 '           * DEMO CLEA6 MES$="Type HELP KEY for info, CURSOR LEFT or UP to return to the menu"
2147 MH$="Read INFO Screen no. 7 / QPOS$"
2150 QPOS$="05090800":QDA$="10203010":PRINT FND$(5,1,"QPOS$ = ");:GOSUB 100:ON QRET% GOTO 1010,1010:Q1$=QDA$:A=VAL(MID$(Q1$,7,1)):K=VAL(RIGR SCREEN *
2996 '           *********************
2997 '
3000 PREC=10:GOSUB 900
3005 GOSUB 20
3010 PRINT"Demonstration CLEAR SCREEN Routine"
3020 F=0:GOSUB 4040
3022 IF QRET%<>0 GOTO 1010
3025 FOR I=1 TO 5000:NEXT
3030 PRINT FNS(13,1);"Continue <CR> : ";:GOSUB 816
3050 GOTO 3005
3993 '
3994 '           *********************
3995 '           * DEMO PRINT SCREEN *
3996 '           *********************
3997 '
4000 PREC=9:GOSUB 900
4010 PREC=10:GOSUB 900
4020 GOSUB 20
4030 PRINT"Demonstratio*************************
9990 '             * INITIALISATION PROCEDURES *
9991 '		   *****************************
9992 '
10000 DEFINT A-Z:DEFSTR S:DEFSNG Q
10010 '                 *************
10020 '			* CONSTANTS *
10030 '                 *****n PRINT SCREEN Routine"
4035 GOTO 4138
4040 MES$="Type HELP KEY for info, CURSOR LEFT to return to the menu"
4045 MH$="Enter : First line between 1 and 24"
4050 PRINT FNS(7,1);"FLIN =":QDI%=0:QPOS$="07080220":GOSUB 100:ON QRET% GOTO 4136,4136:FLIN=QDI%********
10032 ' NOTE : The items defined below are marked in which routines they are
10033 '        used. GEN.=general use
10034 '              SCRH=used in Screen HAndler Activator Routine
10035 '              PRSC=For Print Screen routine
10036 '  
4060 IF FLIN<1 OR FLIN>24 THEN ERROR 101
4065 MES$="Type HELP KEY for info, CURSOR LEFT or UP for previous field"
4066 MH$="Enter : Number of lines between 1 and 24"
4070 PRINT FNS(9,1);"NUM  =":QDI%=1:QPOS$="09080220":GOSUB 100:ON QRET% GOTO 4050,413            CLSC=Used in Clear Screen routine
10037 '              INFO=Required for Info Screens
10038 '        If the one of the routines is not rewuired, then the relating
10039 '        items can be deleted from below.
10040 ESC$=CHR$(&H1B)			' ESC6:NUM=QDI%
4080 IF (FLIN-1)+NUM>24 OR NUM<1 THEN ERROR 102
4100 FOR I=1 TO 24
4110 PRINT FNS(I,1) USING "(                                  line ##                                    )";I;
4120 NEXT
4130 IF F=1 THEN GOSUB 860 ELSE GOSUB 840
4136 RETUAPE code (GEN.)
10050 ATT$=ESC$+"0"			' Screen attributes (GEN.)
10060 INV$=ATT$+"P"			' inverse video (GEN.)
10070 LOW$=ATT$+"A" 			' low intensity (GEN.)
10080 UND$=ATT$+CHR$(&H60)		' Underline     (GEN.)
10090 OFF$=ATT$+CHR$(&H40) 		' turn off set RN
4138 F=1:GOSUB 4040
4139 IF QRET%<>0 GOTO 1010
4140 IF F<>1 THEN 4160 ELSE PRINT FNS(11,1);"Return code QRET% =";QRET%
4150 IF QRET%<>0 THEN ERROR 103
4160 PRINT FNS(15,1);"Continue <CR>: ";:GOSUB 816
4180 GOTO 4020
8993 '
8994 '              **attributes (GEN.)
10120 DEF FNS(X,Y)=CHR$(&H1B)+"Y"+CHR$((X-1)+&H20)+CHR$((Y-1)+&H20):							' cursor control   (GEN.)
10130 DEF FND$(X,Y,Z$)=CHR$(&H1B)+"0"+"A"+CHR$(&H1B)+"Y"+CHR$((X-1)+&H20)+CHR$((Y-1)+&H20)+Z$+CHR$(&H1B)+"0"+CHR$(&H40)	' Message displ***************************
8995 '              * ERROR TRAPPING SUBROUTINE *
8996 '              *****************************
8997 '
9000 IF ERR=101 THEN QEM$="First line. Enter a value between 1 and 24":GOSUB 9200:RESUME 4050
9010 IF ERR=102 THEN Qay function (SCRH)
10150 QDI%=0 				' Integer parameter      (SCRH)
10160 QDS!=0				' Single Prec. parameter (SCRH)
10170 QDD#=0				' Double Prec. parameter (SCRH)
10180 QDA$=" "				' String param.          (SCRH)
10190 ' Set default value for number EM$="Number of lines. Enter a value between 1 and"+STR$(25-FLIN):GOSUB 9200:RESUME 4070
9020 IF ERR=103 THEN QEM$="Turn printer on-line":GOSUB 9200:RESUME 4160
9030 IF ERR=200 THEN QEM$="Screen Handler Load error. Retry ":GOSUB 9200:RESUME 10160
9190 QEof decimal digits required in your program
10200 ' here (QD%=value) !
10210 QD%=2 				' Number of decimal digits (SCRH)
10220 QZA$=STRING$(80,32) 		' maximum input/output length SH (SCRH)
10230 QZ3%=0:QZ5%=0:QZ9%=0:QZ20%=0:QZ21%=0 	' Internal SH ParameM$="Error"+STR$(ERR)+STR$(ERL)+" - Abort program. ":GOSUB 9200:QA=0:RESUME 1120
9200 PRINT CHR$(7);FNS(23,1);ATT$;"B";QEM$;FNS(23,64);OFF$;"Continue <CR> : ";
9210 GOSUB 816
9220 PRINT FNS(23,1);ESC$;"K";
9230 RETURN
9980 STOP
9989 '             ****ters (SCRH)
10240 FLIN=0:NUM=0			' Print Screen parameters   (PRSC/CLSC)
10300 WIDTH 255				' set width of screen (default = 80)
10305 ' Lines 10310-10330 --> SCRH
10310 RESTORE 12000 			' DATA statements
10320 READ QLRK%			' Number of return keys -1 in table QRK%
10322 DIM QRK%(QLRK%)			' Return key table. QRET%=element nr.
10324 FOR QI%=0 TO QLRK%
10328 READ QRK%(QI%)			' Set exit byte (7 bit)
10330 NEXT
10335 ' Next two lines for INFO
10350 OPEN "R",1,"A:SHACT.MES",87	' Messages for INFO Scree$+MID$(F$,I,1):NEXT
11410 GOTO 11460
11420 FOR I=FRST% TO PT%-1:F1$=F1$+MID$(F$,I,1):NEXT
11430 FOR I=1 TO 8-LEN(F1$):F1$=F1$+" ":NEXT
11440 FOR I=PT%+1 TO LEN(F$):F1$=F1$+MID$(F$,I,1):NEXT
11460 FOR I=1 TO 11-LEN(F1$):F1$=F1$+" ":NEXT
11480 POKE &H5ns
10360 FIELD 1,87 AS QL$
11040 '
11050 '           *********************************
11060 '           * LOADER ROUTINE SCREEN HANDLER *
11070 '           *********************************
11080 '
11090 ' Demonstration of how to use the machine coC,DRV%: FOR X=1 TO 11:POKE &H5C+X,ASC(MID$(F1$,X,1)): NEXT
11490 UP$="":X$="E50E0F115C00CD0500FEFF2849C5D5AF327C000E1A118000CD05000E14115C00CD0500D1218000C1B700003A7C00FE01200DED5B80002A820019E5C12186007E1278BA200479BB280B23137CFE0120EFC5D518BF3E00E177237de loader 
11100 F$="A:SH.L"
11110 GOSUB 11560				' Open file, get memory params
11120 PRINT CHR$(12) USING "Loader for SCREEN HANDLER to &H";HEX$(SLAD!)
11130 GOSUB 11360
11140 IF F%<>0 THEN ERROR 200			' Routine not loaded
11150 DEF USR2=SENT!:DEF 70E10115C00CD0500C9"
11500 FOR X=1 TO LEN(X$) STEP 2:UP$=UP$+CHR$(VAL("&H"+MID$(X$,X,2))):NEXT
11510 X!=VARPTR(UP$):UP!=PEEK(X!+1)+256*PEEK(X!+2)
11515 UP!=UP!+65536!*(UP!>32767)
11530 CALL UP!(F%)			' Call the machine code loader
11540 X$="":UP$="":RUSR3=SENT!+6		' Initialise Routines
11152 QZ1%=SLAD!+65536!*(SLAD!>32767) 	' Start of parameter block SH
11154 POKE QZ1%+17,ASC(".")		' Set decimal delimeter
11155 POKE QZ1%+18,ASC(",")		' Set numeric separator
11156 POKE QZ1%+20,&H60			' Set screen atETURN		' Erase the strings used in the routine
11550 ' --------------------------------------------------------------------
11560 F$="A:SH.L":N!=PEEK(1)+256*PEEK(2)+500:N=INT(N!/1000):V$=MID$(STR$(N),2)
11565 V$=MID$(STR$(N),2,2): F$=F$+V$
11570 OPEN "tribute
11158 PRINT CHR$(12):FOR I=1 TO 50:PRINT:NEXT
11160 RETURN					' Return to program flow
11180 :
11190 ' MACHINE CODE LOADER P2000C
11200 '
11210 ' NOTE: BEFORE LOADING OF ASSEMBLY ROUTINES AN APPROPRIATE CLEAR
11220 '       STATEMENT SHOULD R",2,F$:GET 2,1
11580 Q=VARPTR(#2)
11590 SLAD!=CVI(CHR$(PEEK(Q))+CHR$(PEEK(Q+1)))	' Load address of routine
11600 SL!=CVI(CHR$(PEEK(Q+2))+CHR$(PEEK(Q+3)))	' Length of routine
11610 SENT!=CVI(CHR$(PEEK(Q+4))+CHR$(PEEK(Q+5))) ' Routine entry address
116BE EXECUTED (SEE EXAMPLE ABOVE);
11230 '       CP/M FILE NAME IS NOT SYNTAX CHECKED;
11240 '
11250 ' ENTRY PARAMETER: F$= FILE NAME (CP/M NOTATION)
11260 '                  EXAMPLE: F$= "B:SH.L63"
11270 '                  FILE STRUCTURE: <HEADER> <MAC20 CLOSE #2
11630 RETURN
12000 DATA 9:				' Number of Keys - 1
12010 DATA 13:				' Carriage Return
12020 DATA 19:				' Cursor Left    (CTRL S)
12030 DATA 5:                           ' Cursor Up      (CTRL E)
12040 DATA 171:				' Arithmetic '+'
1205HINE CODE>
11280 '                  <HEADER>: 2 B. LOAD ADDR, 2 B. LENGTH OF FILE
11290 '                            2 B. START ADDR
11300 '
11310 ' EXIT PARAMETER:  F%= 0 LOAD OK
11320 '                    <>0 LOAD ERROR
11330 '
11340 ' -----------0 DATA 173:				' Arithmetic '-' 
12060 DATA 10:				' HELP           (CTRL J)
12070 DATA 21:                          ' UNDO           (CTRL U)
12080 DATA 24:                          ' Cursor Down    (CTRL X)
12090 DATA 127:	 			' (C)lear Key    
1209----------------------------------------------------------
11350 '
11360 F1$=""
11370 IF MID$(F$,2,1)=":" THEN DRV%=ASC(F$)-&H40:FRST%=3: ELSE DRV%=0:FRST%=1
11380 PT%=INSTR(FRST%,F$,".")
11390 IF PT%<>0 THEN 11420
11400 FOR I=FRST% TO LEN(F$):F1$=F12 DATA 4:				' Cursor Right   (CTRL D)
12100 ' Return Key Codes : The first DATA statement above is the number of
12110 '                    return keys minus one required in this program.
12120 '                    These key codes must also be defined in the sys-
12130 '                    tem using CONFIG. If any special return keys will
12140 '                    be used in the application (e.g. 'F1' or 'F2') then
12150 '                    these must be defined and added to the DATA list
12160 ' ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее