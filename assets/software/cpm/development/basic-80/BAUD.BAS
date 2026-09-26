10  REM Baudrate instelprogramma voor P2000C comm. poort
20 DATA 75,150,300,600,1200,2400,4800,9600,19200
30 DIM BAUD(8): DEFSTR P,I,E,C,W 
40 DEF  FNP(R,K)=CHR$(27)+"Y"+CHR$(32+R)+CHR$(32+K)
50 C=CHR$(27)+"C"          :W=CHR$(27)+"c"
60 I=CHR$(27)+"0         Gebruik voor deze bepaling de discs no 164, 167 of 168.
          
          Pipettor :
                    Monsterschijf positie 1         aquadest
                                          2 + 3     seronorm lipid
                          "+CHR$(80) :E=CHR$(27)+"0"+CHR$(64)
70 PRINT CHR$(12);W
80 PRINT FNP(0,10)I" P2000C  Baudrate insteling voor de Communicatiepoort "E
90 PRINT FNP(4,18)I" Keuze "E"       " I"  snelheid  "E
100 SETC = 0
110 IF PEEK(&HFFFE) <> &HFF THEN 130
120 IF PEEK                4         level I
                                          5         level II
                                          einde     precilip
          
                    Instelling :
            
                                 350 (&HD605) <> 0 THEN SETC=8-(LOG(PEEK(&HD605))/LOG(2)):GOTO 140
130 IF PEEK(&HFFFE) <> 0 THEN SETC=8-(LOG(PEEK(&HFFFE))/LOG(2))
140 FOR RATE  = 0  TO  8
150 READ BAUD(RATE) 
160 PRINT  FNP((RATE+6),20) RATE "    --> ";
170 IF RATE=SETC THEN PRINT I;
18ul
          
                                REAGENS VOLUME 
          
          
                                 05 ul           60 ul 
          
                                SAMPLE VOLUME   SAMPLE & DILUENT VOLUME
          
          
 0 PRINT USING "######";BAUD(RATE);: PRINT " Baud"E
190 NEXT
200 PRINT: PRINT
210 PRINT  FNP(18,20)"Veranderen  J/N ";
220 AN