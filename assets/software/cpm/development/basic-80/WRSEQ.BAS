10 A=1
20 OPEN "O",#1,"DATA"
30 WHILE NAAM$ <> "KLAAR" AND A <= 15
40 PRINT A ; "stop met 'KLAAR'"
50 INPUT "NAAM ";NAAM$
60 IF NAAM$ = "KLAAR" THEN 120 
70 INPUT "ADRES ";ADRES$
80 INPUT "PLAATS ";PLAATS$
90 PRINT #1,NAAM$;",";ADRES$;",";PLAATS$
ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее