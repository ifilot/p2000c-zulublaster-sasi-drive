0 ' INLEES: Laden v/d 'Inlees-routine'
1 '          via de printeruitgang.
2 ' Versie: 1.1NL Aug'83  PJMR/PTIS (C)
4 ONERRORGOTO6:GOTO10
6 RESUME
10 CLEAR 500:DEFINTA-Z:DEFSNGS:DEFSTRC:CS=CHR$(12):CR=CHR$(129):CG=CHR$(131):CD=
CHR$(132):CB=CHR$(134):ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееCH=CHR$(141):CA=CHR$(157):CZ=CHR$(156):PRINTCS;CB;CA;CD;C
H"INLEES-Programma    "CHR$(140)"Versie 1.1NL":PRINT:PRINT
12 PRINTCB"Dit is een P2000 met ";:GH=PEEK(24668):IFGH=1THENPRINT"16";ELSEIFGH=2
THENPRINT"32";ELSEPRINT"48";
14 PRINT"K geheugen.":PRIееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееNT:PRINTCB"Dat biedt de volgende mogelijkheden:":PRINT:
RESTORE100:CX="":CP=CHR$(13)+CHR$(17)
16 READKZ:IFKZ=0THEN18ELSEREADKG,CK,KA:IFKG>GHTHEN16ELSECX=CX+MID$(STR$(KZ),2):C
P=CP+STRING$(2,17):PRINTCG;CA;CR;:PRINTUSING"#  ";KZ;:PRINTCZ;CG;CK:PRINT:GOTOееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее16
18 PRINT:PRINTCB"Welke mogelijkheid? ";:POKE24588,0
20 KS=INSTR(CX,CHR$(INP(""))):IFKS=0THEN20ELSEKS=VAL(MID$(CX,KS,1)):PRINTKS;CP;:
RESTORE100
22 READKZ,KG,CK,KA:IFKZ=KSTHEN24ELSEIFKG>GHTHEN22ELSEPRINT:PRINT:GOTO22
24 PRINTCB;CA;CD;CHR$(4)CHR$(22)ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее