PROGRAM CROSSREF; (*$R-*)

(* This program will generate a cross reference map of any	*)
(* COMPAS Pascal program, i.e. a map that lists all identifiers	*)
(* used within the program as well as the line numbers of all	*)
(* lines that contain referencSTRING','THEN','TO','TYPE','UNTIL',
    'VAR','WHILE','WITH');

TYPE

(* Identifier types. The maximum length is 64 characters.	*)

  IDENTPTR = ^IDENT;
  IDENT = STRING[64];

(* Line record types. Each line record contains the number of a	*)
(*es to the identifiers. Optional-	*)
(* ly, a source listing with line numbers may be output.	*)

(* On processing the input file, all identifiers are extracted	*)
(* and compared with the reserved words of COMPAS Pascal. If an	*)
(* identifier is not  line, within which a given identifier is referenced, and a	*)
(* pointer to the next line record.				*)

  LINERECPTR = ^LINEREC;
  LINEREC = RECORD
	      NUMBER: INTEGER;
	      NEXT: LINERECPTR;
	    END;

(* Identifier record types. Each idena reserved word, it is entered into a	*)
(* binary tree. Each entry in the binary tree contains a poin-	*)
(* ter to the identifier, and a left node and a right node	*)
(* pointer to subsequent entries (or NIL if no entries follow).	*)
(* Furthermore, tifier record contains a	*)
(* pointer to the identifier string, a pointer to the first and	*)
(* the last line record in the reference chain, and a left node	*)
(* and a right node pointer to subsequent entries in the binary	*)
(* tree.							*)

  an entry contains a pointer to the first re-	*)
(* cord in a line number reference chain, and a pointer to the	*)
(* last record in that chain. When an identifier is entered	*)
(* into the tree for the first time, the program allocates both	*)
(* a newIDENTRECPTR = ^IDENTREC;
  IDENTREC = RECORD
	       ID: IDENTPTR;
	       FIRSTLINE,LASTLINE: LINERECPTR;
	       LEFT,RIGHT: IDENTRECPTR;
	     END;

(* Source line type. The maximum length of a source line is 127	*)
(* characters.							*)

   identifier record and a line number reference record.	*)
(* Subsequent references to that identifier will then expand	*)
(* the line number reference chain, provided that the line num-	*)
(* ber is not the same as that of the last reference.		*)

(* SOURCELINE = STRING[127];

(* Reserved word table pointers type. Each element points to	*)
(* the first reserved word, that starts with the character gi-	*)
(* ven by the index.						*)

  RWORDTP = ARRAY['A'..'Z'] OF INTEGER;

VAR

(* Global varWhen all lines have been processed, the program traverses	*)
(* the binary tree, printing all identifiers along with the	*)
(* numbers of the lines within which they are referenced.	*)

CONST

(* Various constants.						*)

  MAXDOTS = 50;		(* Max iables.						*)

  LINENUMBER,		(* Current line number *)
  NOFIDENTS,		(* Number of identifiers processed *)
  POS,			(* Position within current line *)
  LINELEN: INTEGER;	(* Length of current line *)
  CH: CHAR;		(* Current character *)
  LISTINGnumber of dots per line on CRT *)
  NOFRWORDS = 44;	(* Number of reserved words *)
  FORMFEED = ^L;	(* Form-feed character *)

(* Table of reserved words.					*)

  RWORDS: ARRAY[1..NOFRWORDS] OF STRING[9] = (
    'AND','ARRAY','AT','BEGIN','CASE',',		(* True if source listing requested *)
  ERROR: BOOLEAN;	(* Error flag *)
  LINE: SOURCELINE;	(* Current source line *)
  IDTREE: IDENTRECPTR;	(* Root of cross reference tree *)
  FIRSTRWORD: RWORDTP;	(* Pointers to reserved word table *)
  INFILE,CODE','CONST','DIV','DO',
    'DOWNTO','ELSE','END','EXOR','EXTERNAL','FILE','FOR','FORWARD',
    'FUNCTION','GOTO','IF','IN','LABEL','MOD','NIL','NOT','OF',
    'OR','OTHERWISE','PACKED','PROCEDURE','PROGRAM','RECORD',
    'REPEAT','SET','SHL','SHR','		(* Input file *)
  OUTFILE: TEXT;	(* Output file *)

(*$A+*)

(* FREEMEM returns the number of bytes available on the heap.	*)
(* The result type is real to allow for values outside the in-	*)
(* teger range.							*)

FUNCTION FREEMEM: REAL;
BEGIN
  IF MEMAVAIL>0 THEN
  FREEMEM:=MEMAVAIL ELSE
  FREEMEM:=65536.0-MEMAVAIL;
END;

(* NEXTCH reads the next character from the input file into CH.	*)
(* If a source listing was requested, NEXTCH lists input lines	*)
(* to the output file as they'' THEN OUTNAME:='LST:';
  ASSIGN(OUTFILE,OUTNAME); (*$I-*) REWRITE(OUTFILE) (*$I+*);
  IF IORES>0 THEN
  BEGIN
    WRITELN('OUTPUT FILE ERROR');
    ERROR:=TRUE; GOTO EXIT;
  END;
  LISTING:=(LISTYN='Y') OR (LISTYN='y');
  IDTREE:=NIL;
  I:=1;
  are read. Otherwise, a dot is	*)
(* printed on the console for each line read. A ^Z character is	*)
(* returned on reaching the end of the input file.		*)

PROCEDURE NEXTCH;
VAR
  P,T: INTEGER;
BEGIN
  IF (POS<=LINELEN) THEN
  BEGIN
    CH:=LINE FOR CH:='A' TO 'Z' DO
  BEGIN
    FIRSTRWORD[CH]:=I; MATCH:=TRUE;
    WHILE (I<=NOFRWORDS) AND MATCH DO
    BEGIN
      MATCH:=RWORDS[I][1]=CH; IF MATCH THEN I:=I+1;
    END;
  END;
  LINENUMBER:=0; NOFIDENTS:=0;
  POS:=1; LINELEN:=0; NEXTCH;
  [POS]; POS:=POS+1;
    IF (CH>='a') AND (CH<='z') THEN CH:=CHR(ORD(CH)-32);
  END ELSE
  IF NOT EOF(INFILE) THEN
  BEGIN
    READLN(INFILE,LINE); LINENUMBER:=LINENUMBER+1;
    IF LISTING THEN
    BEGIN
      WRITE(OUTFILE,'<',LINENUMBER:5,'> ');
 EXIT:
END;

(* PROCESSFILE processes the input file, creating a cross refe-	*)
(* rence binary tree.						*)

PROCEDURE PROCESSFILE;
VAR
  IFREE: REAL;

(* GETSYMBOL reads the next symbol from the input file. If the	*)
(* symbol is an identifier     T:=8;
      FOR P:=1 TO LEN(LINE) DO
      IF LINE[P]<>^I THEN
      BEGIN
	WRITE(OUTFILE,LINE[P]); T:=T-1; IF T=0 THEN T:=8;
      END ELSE
      BEGIN
	WRITE(OUTFILE,'':T); T:=8;
      END;
      WRITELN(OUTFILE);
    END ELSE
    BEGIN
, it is processed using PROCESSIDENT	*)
(* below.							*)

PROCEDURE GETSYMBOL;
CONST
  ALPHANUMS: SET OF '0'..'Z' = ['0'..'9','A'..'Z'];
  HEXDIGITS: SET OF '0'..'F' = ['0'..'9','A'..'F'];

(* PROCESSIDENT reads an identifier and enters it into t      WRITE('.');
      IF LINENUMBER MOD MAXDOTS=0 THEN WRITELN;
    END;
    LINELEN:=LEN(LINE); POS:=1; CH:=' ';
  END ELSE
  CH:=^Z;
END;

(* INITIALIZE is used to initialize input and output files and	*)
(* all global variables.					*)

PROhe	*)
(* cross reference binary tree, provided that it is not a re-	*)
(* served word.							*)

PROCEDURE PROCESSIDENT;
VAR
  I,MAX: INTEGER;
  NOTFOUND: BOOLEAN;
  NEWID: IDENT;
  X: LINERECPTR;

(*$A-*)

(* ENTERID enters NEWID into the croCEDURE INITIALIZE;
LABEL EXIT;
VAR
  I: INTEGER;
  MATCH: BOOLEAN;
  INNAME,OUTNAME: STRING[14];
  LISTYN: STRING[1];
BEGIN
  ERROR:=FALSE;
  WRITELN;
  WRITELN('    COMPAS PASCAL CROSS REFERENCE GENERATOR');
  WRITELN;
  WRITELN('             ss reference binary tree.	*)
(* Note that an identifier record is allocated only if the	*)
(* identifier is not already within the tree. Also note the use	*)
(* of the ALLOCATE procedure to allocate only the required num-	*)
(* ber of bytes for the ide     Version 1.1');
  WRITELN;
  WRITELN('             Copyright (C) 1983 by');
  WRITELN('           Poly-Data microcenter ApS');
  WRITELN;
  WRITELN;
  WRITE('Input file name? '); READLN(INNAME);
  WRITE('Output file name (default printer)? '); Rntifier instead of the full maximum	*)
(* length.							*)

PROCEDURE ENTERID(VAR ROOT: IDENTRECPTR);
BEGIN
  IF ROOT=NIL THEN
  BEGIN
    NOFIDENTS:=NOFIDENTS+1;
    NEW(ROOT);
    WITH ROOT^ DO
    BEGIN
      ALLOCATE(ID,LEN(NEWID)+1); ID^:=NEADLN(OUTNAME);
  WRITE('Print source listing (Y/N)? '); READLN(LISTYN);
  WRITELN;
  ASSIGN(INFILE,INNAME); (*$I-*) RESET(INFILE) (*$I+*);
  IF IORES>0 THEN
  BEGIN
    WRITELN('INPUT FILE ERROR');
    ERROR:=TRUE; GOTO EXIT;
  END;
  IF OUTNAME=EWID;
      NEW(FIRSTLINE);
      FIRSTLINE^.NUMBER:=LINENUMBER; FIRSTLINE^.NEXT:=NIL;
      LASTLINE:=FIRSTLINE;
      LEFT:=NIL; RIGHT:=NIL;
    END;
  END ELSE
  IF NEWID<ROOT^.ID^ THEN ENTERID(ROOT^.LEFT) ELSE
  IF NEWID>ROOT^.ID^ THEN ENTERID(ROOT^.RIGHT) ELSE
  WITH ROOT^ DO
  BEGIN
    IF LINENUMBER<>LASTLINE^.NUMBER THEN
    BEGIN
      NEW(X); X^.NUMBER:=LINENUMBER; X^.NEXT:=NIL;
      LASTLINE^.NEXT:=X;
      LASTLINE:=X;
    END;
  END;
END;

BEGIN (*PROCESSIDENT*)
  IF CH='_)
(* which they are referenced.					*)

PROCEDURE TRAVERSE(ROOT: IDENTRECPTR);
BEGIN
  IF ROOT<>NIL THEN
  BEGIN
    TRAVERSE(ROOT^.LEFT);
    WITH ROOT^ DO
    BEGIN
      WRITE(OUTFILE,ID^);
      X:=FIRSTLINE; N:=1;
      REPEAT
	IF N MOD 8' THEN
  BEGIN
    I:=NOFRWORDS; MAX:=NOFRWORDS;
  END ELSE
  BEGIN
    I:=FIRSTRWORD[CH];
    IF CH<'Z' THEN MAX:=FIRSTRWORD[SUCC(CH)] ELSE MAX:=NOFRWORDS;
  END;
  NEWID:='';
  REPEAT
    NEWID:=NEWID+CH; NEXTCH;
  UNTIL NOT(CH IN ALPHANUMS);=1 THEN WRITELN(OUTFILE);
	WRITE(OUTFILE,X^.NUMBER:8); X:=X^.NEXT; N:=N+1;
      UNTIL X=NIL;
      WRITELN(OUTFILE);
    END;
    TRAVERSE(ROOT^.RIGHT);
  END;
END;

BEGIN (*PRINTXREF*)
  TRAVERSE(IDTREE); WRITE(OUTFILE,FORMFEED);
END;

(* Ma
  NOTFOUND:=TRUE;
  WHILE (I<MAX) AND NOTFOUND DO
  BEGIN
    NOTFOUND:=NEWID<>RWORDS[I]; I:=I+1;
  END;
  IF NOTFOUND THEN ENTERID(IDTREE);
END;

BEGIN (*GETSYMBOL*)
  CASE CH OF
    'A'..'Z','_':
      PROCESSIDENT;
    '''':
      REPEAT
in program.						*)

BEGIN
  INITIALIZE;
  IF NOT ERROR THEN PROCESSFILE;
  IF NOT ERROR THEN PRINTXREF;
END.
D;
    TRAVERSE(ROOT^.RIGHT);
  END;
END;

BEGIN (*PRINTXREF*)
  TRAVERSE(IDTREE); WRITE(OUTFILE,FORMFEED);
END;

(* Ma	REPEAT NEXTCH UNTIL (CH='''') OR (CH=^Z);
	NEXTCH;
      UNTIL CH<>'''';
    '$':
      REPEAT NEXTCH UNTIL NOT(CH IN HEXDIGITS);
    '{':
      BEGIN
	REPEAT NEXTCH UNTIL (CH='}') OR (CH=^Z);
	NEXTCH;
      END;
    '(':
      BEGIN
	NEXTCH;ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее
	IF CH='*' THEN
	BEGIN
	  REPEAT
	    REPEAT NEXTCH UNTIL (CH='*') OR (CH=^Z);
	    NEXTCH;
	  UNTIL (CH=')') OR (CH=^Z);
	  NEXTCH;
	END;
      END;
  OTHERWISE
    NEXTCH;
  END;
END;

BEGIN (*PROCESSFILE*)
  IFREE:=FREEMEM;
  WHILE (CH<ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее>^Z) AND (FREEMEM>100.0) DO GETSYMBOL;
  IF NOT LISTING THEN
  BEGIN
    IF (LINENUMBER MOD MAXDOTS<>0) THEN WRITELN;
    WR