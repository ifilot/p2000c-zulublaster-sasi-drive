PROGRAM CALCULATOR; (*$R-*)

(* This program acts like a calculator - You type an expression	*)
(* and the program calculates its value. Each time the calcula-	*)
(* tor is ready to accept an input line, it prints an asterisk.	*)
(* You must then type=0; NEXTCHAR;
      IF CH IN ['+','-'] THEN
      BEGIN
	NEGEXP:=CH='-'; NEXTCHAR;
      END ELSE
      NEGEXP:=FALSE;
      WHILE CH IN ['0'..'9'] DO
      BEGIN
        EE:=EE*10+ORD(CH)-48;
	NEXTCHAR;
      END;
      IF NEGEXP THEN E:=E-EE E the expression and end it by pressing the	*)
(* RETURN key, and shortly after, the result is displayed. If	*)
(* the calculator finds an error, it displays a pointer, which	*)
(* points at the error. There are five different operators (^,	*)
(* *, /, LSE E:=E+EE;
    END;
    F:=F*PWRTEN(E);
  END ELSE
  IF CH='(' THEN
  BEGIN
    NEXTCHAR;
    F:=EXPRESSION;
    IF CH=')' THEN NEXTCHAR ELSE CH:=ERRCH;
  END ELSE
  IF CH='X' THEN
  BEGIN
    NEXTCHAR; F:=VALUE;
  END ELSE
  BEGIN
    FOU+, and -), and seven standard functions (ABS, SQRT,	*)
(* SIN, COS, ARCTAN, LN, and EXP). Parentheses within expres-	*)
(* sions are allowed. A special variable, called X, always	*)
(* holds the value of the last computation. To end the program,	*)
(* ND:=FALSE;
    FOR SF:=FABS TO FEXP DO
    IF NOT FOUND THEN
    BEGIN
      L:=LEN(STDFUN[SF]);
      IF COPY(EXPR,POS,L)=STDFUN[SF] THEN
      BEGIN
	POS:=POS+L-1; NEXTCHAR;
	F:=FACTOR;
	CASE SF OF
	  FABS: F:=ABS(F);
	  FSQRT: F:=SQRT(F);
	 type QUIT when the calculator prompts for an input line.	*)

CONST
  STRLEN = 48;
TYPE
  STR = STRING[STRLEN];
VAR
  E: INTEGER;
  R: REAL;
  S: STR;

PROCEDURE EVALUATE(VAR EXPR: STR; VAR VALUE: REAL; VAR ERRPOS: INTEGER);
CONST
  ERRCH = '?' FSIN: F:=SIN(F);
	  FCOS: F:=COS(F);
	  FARCTAN: F:=ARCTAN(F);
	  FLN: F:=LN(F);
	  FEXP: F:=EXP(F);
	END;
	FOUND:=TRUE;
      END;
    END;
    IF NOT FOUND THEN CH:=ERRCH;
  END;
  FACTOR:=F;
END (*FACTOR*);

BEGIN (*SIGNEDFACTOR*)
  IF C;
  EOFLINE = @13;
VAR
  POS: INTEGER;
  CH: CHAR;

PROCEDURE NEXTCHAR;
BEGIN
  REPEAT
    POS:=POS+1;
    IF POS<=LEN(EXPR) THEN
    CH:=EXPR[POS] ELSE
    CH:=EOFLINE;
  UNTIL CH<>' ';
END;

FUNCTION EXPRESSION: REAL;
VAR
  E: REAL;
  H='-' THEN
  BEGIN
    NEXTCHAR; SIGNEDFACTOR:=-FACTOR;
  END ELSE
  SIGNEDFACTOR:=FACTOR;
END (*SIGNEDFACTOR*);

BEGIN (*TERM*)
  T:=SIGNEDFACTOR;
  WHILE CH='^' DO
  BEGIN
    NEXTCHAR; T:=EXP(LN(T)*SIGNEDFACTOR);
  END;
  TERM:=T;
END (*TEOPR: CHAR;

FUNCTION SIMEXPR: REAL;
VAR
  S: REAL;
  OPR: CHAR;

FUNCTION TERM: REAL;
VAR
  T: REAL;

FUNCTION SIGNEDFACTOR: REAL;

FUNCTION FACTOR: REAL;
TYPE
  STDF = (FABS,FSQRT,FSIN,FCOS,FARCTAN,FLN,FEXP);
  STDFLIST = ARRAY[STDF] OF STRM*);

BEGIN (*SIMEXPR*)
  S:=TERM;
  WHILE CH IN ['*','/'] DO
  BEGIN
    OPR:=CH; NEXTCHAR;
    CASE OPR OF
      '*': S:=S*TERM;
      '/': S:=S/TERM;
    END;
  END;
  SIMEXPR:=S;
END (*SIMEXPR*);

BEGIN (*EXPRESSION*)
  E:=SIMEXPR;
  RING[6];
CONST
  STDFUN: STDFLIST = ('ABS','SQRT','SIN','COS','ARCTAN','LN','EXP');
VAR
  E,EE,L: INTEGER;
  DECPOINT,NEGEXP,FOUND: BOOLEAN;
  F: REAL;
  SF: STDF;
BEGIN
  IF CH IN ['0'..'9'] THEN
  BEGIN
    F:=0.0; E:=0; DECPOINT:=FALSE;
    WHILE CH IN ['+','-'] DO
  BEGIN
    OPR:=CH; NEXTCHAR;
    CASE OPR OF
      '+': E:=E+SIMEXPR;
      '-': E:=E-SIMEXPR;
    END;
  END;
  EXPRESSION:=E;
END (*EXPRESSION*);

BEGIN (*EVALUATE*)
  POS:=0; NEXTCHAR;
  VALUE:=EXPRESSION;
  IF CREPEAT
      F:=F*10.0+(ORD(CH)-48);
      IF DECPOINT THEN E:=E-1;
      NEXTCHAR;
      IF (CH='.') AND NOT DECPOINT THEN
      BEGIN
	DECPOINT:=TRUE; NEXTCHAR;
      END;
    UNTIL NOT(CH IN ['0'..'9']);
    IF CH='E' THEN
    BEGIN
      EE:H=EOFLINE THEN ERRPOS:=0 ELSE ERRPOS:=POS;
END (*EVALUATE*);

BEGIN (*CALCULATOR*)
  REPEAT
    WRITE('* '); BUFLEN:=STRLEN; READ(S);
    IF (S<>'') AND (S<>'QUIT') THEN
    BEGIN
      EVALUATE(S,R,E);
      IF E=0 THEN
      BEGIN
	WRITE(' =');
	IF R>=0.0 THEN WRITE(R:17) ELSE WRITE(R:18);
      END ELSE
      BEGIN
	WRITELN;
	WRITE('^ ERROR':E+8);
      END;
    END;
    WRITELN;
  UNTIL S='QUIT';
END (*CALCULATOR*).
