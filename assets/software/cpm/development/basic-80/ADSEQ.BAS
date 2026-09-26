10 PRINT "Gegevens van oud bestand schrijven naar tijdelijk bestand "
20 OPEN "I",#1,"DATA"
30 OPEN "O",#2,"KOPIE"
40 WHILE NOT EOF(1)
50 LINE INPUT #1,REGEL$
60 PRINT REGEL$
70 PRINT #2,REGEL$
80 WEND
90 CLOSE #1
100 PRINT :PRINT "Verwijder oud bווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווestand"
110 KILL "DATA"
120 PRINT "Voeg nieuwe gegevens toe aan 'kopie' bestand"
130 PRINT "Zoals in 'WRSEQ.BAS' "
140 PRINT
150 A=1
160 WHILE NAAM$ <> "KLAAR" AND A <=20
170 PRINT A ;"stop met 'KLAAR'"
180 INPUT "NAAM   " ;NAAM$
190 IF NAAM$ ="KLוווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווו