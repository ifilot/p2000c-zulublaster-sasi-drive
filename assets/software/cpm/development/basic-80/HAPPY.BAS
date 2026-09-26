0 REM HAPPY-SOFT
10 REM ***** PAS AAN ****
11 REM ! NO-CHANGE !
99 REM Versie maart 1984
100 FOR X=1 TO 30 :PRINT:NEXT:PRINT "HAPPY SOFT":PRINT:PRINT:PRINT"Aanpassingsroutine":PRINT:PRINT:PRINT:INPUT "Programmanaam:   ";F$:ON ERROR GOTO 110:NAME F$ AS ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееF$:IF EX=58 THEN 120 ELSE PRINT "Fout tijdens zoeken programma !":GOTO 100
110 EX=ERR:RESUME NEXT
120 LINEINPUT "Versie-datum: ";D$ :FL=0
130 ON ERROR GOT 0:OPEN "I",1,F$:LINE INPUT #1,R$:IF INSTR(R$,"REM HAPPY-SOFT")=0 THEN PRINT "Geen REM HAPPY-SOFT iееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееn eerste regel !":PRINT "Soms niet met 'A' ge-SAVED ??":GOTO 500 ELSE OPEN "0",2,"NIEUWSTE DAT."
140 IF EOF(1) THEN 500 ELSE LINE INPUT #1,R$
150 SP=INSTR(R$," "):PRINT CHR$(13)LEFT$(R$,SP);
160 IF INSTR(R$,"11 ")=1 THEN IF INSTR(R$,"NO-CHANGE") THEN PRееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее