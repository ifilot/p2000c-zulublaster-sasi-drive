PROGRAM INSTALL; (*$A+,C-,R-*)

LABEL EXIT;

CONST

  MAXTERM = 50;

TYPE

  STR2  = STRING[2];
  STR3  = STRING[3];
  STR4  = STRING[4];
  STR5  = STRING[5];
  STR8  = STRING[8];
  STR12 = STRING[12];
  STR16 = STRING[16];
  STR24 = STRIN INTEGER;
VAR
  N,P: INTEGER;
  OK: BOOLEAN;
  S: STR5;
BEGIN
  REPEAT
    BUFLEN:=5; READ(S);
    IF S='' THEN OK:=FALSE ELSE
    BEGIN
      VAL(S,N,P);
      OK:=(P=0) AND (N>=MIN) AND (N<=MAX);
    END;
    IF NOT OK THEN BACKSP(LEN(S));
G[24];
  STR31 = STRING[31];
  STR36 = STRING[36];
  STR48 = STRING[48];

  CHARSET = SET OF CHAR;

  TNAMSTR = STRING[31];

  DATAREC = RECORD
	      TERMNAME: TNAMSTR;
	      WIDTH,HEIGHT: BYTE;
	      GXYLS: STR8;
	      GXYSS,GXYTS: STR4;  UNTIL OK;
  WRITELN; READNUM:=N;
END;

FUNCTION READSEQ(MAXLEN: INTEGER): STR8;
CONST
  HEXDIGITS: SET OF '0'..'f' = ['0'..'9','A'..'F','a'..'f'];
VAR
  D,H,N,P: INTEGER;
  ERROR: BOOLEAN;
  SEQ: STR8;
  S: STR24;
BEGIN
  REPEAT
    BUFLEN:
	      COLB4LIN,COOROFS,COORFMT: BYTE;
	      CLHS,CESS,CELS,ILNS,DLNS,RONS,ROFS: STR8;
	      VGXY,VLCS,VLCI,VLCO,VLLO,VLAO,VLAI: INTEGER;
	      PATCH: ARRAY[0..511] OF BYTE;
	      BACKF,INSMF,AUTOF,TABSF: BYTE;
	      RDELAY: INTEGER;
	      ALT=23; READ(S); S:=S+^M;
    ERROR:=FALSE; P:=1; N:=0;
    REPEAT
      WHILE S[P]=' ' DO P:=P+1;
      IF (S[P] IN HEXDIGITS) AND (N<MAXLEN) THEN
      BEGIN
	H:=0;
	REPEAT
      	  IF S[P] IN ['0'..'9'] THEN D:=ORD(S[P])-48 ELSE
	  IF S[P] IN ['A'KEY: ARRAY[0..255] OF BYTE;
	    END;

VAR

  CF: FILE;
  TF: FILE OF TNAMSTR;
  DF: FILE OF DATAREC;
  CFN: STR16;
  DATA: DATAREC;
  TNAM: ARRAY[1..MAXTERM] OF STR31;
  B1: ARRAY[0..767] OF BYTE;
  B2: ARRAY[0..511] OF BYTE;
  I,B2S,B2A: INT..'F'] THEN D:=ORD(S[P])-55 ELSE
	  D:=ORD(S[P])-87;
          H:=H*16+D; P:=P+1;
	UNTIL NOT(S[P] IN HEXDIGITS);
        N:=N+1; SEQ[N]:=CHR(H);
      END;
      IF NOT(S[P] IN [^M,' ']) THEN ERROR:=TRUE;
    UNTIL (S[P]=^M) OR ERROR;
    IF ERROR EGER;
  CH: CHAR;

FUNCTION UPCASE(S: STR24): STR24;
VAR
  I: INTEGER;
  U: STR24;
BEGIN
  U:='';
  FOR I:=1 TO LEN(S) DO
  IF (S[I]>='a') AND (S[I]<='z') THEN
  U:=U+CHR(ORD(S[I])-32) ELSE U:=U+S[I];
  UPCASE:=U;
END;

FUNCTION HEX(NUMBER,DTHEN BACKSP(LEN(S)-1);
  UNTIL NOT ERROR;
  SEQ[0]:=CHR(N); WRITELN;
  READSEQ:=SEQ;
END;

FUNCTION READYN: INTEGER;
VAR
  S: STR4;
BEGIN
  REPEAT
    BUFLEN:=3; READ(S); S:=UPCASE(S);
    IF (S<>'YES') AND (S<>'NO') THEN BACKSP(LEN(S));
  UNTIGITS: INTEGER): STR4;
CONST
  HEXDIGITS: ARRAY[0..15] OF CHAR = '0123456789ABCDEF';
VAR
  D: INTEGER;
  H: STR4;
BEGIN
  H[0]:=CHR(DIGITS);
  FOR D:=DIGITS DOWNTO 1 DO
  BEGIN
    H[D]:=HEXDIGITS[NUMBER AND 15];
    NUMBER:=NUMBER SHR 4;
  ENDIL (S='YES') OR (S='NO');
  IF S='YES' THEN READYN:=255 ELSE READYN:=0;
  WRITELN;
END;

FUNCTION SELECT(PROMPT: STR48; OKCH: CHARSET): CHAR;
VAR
  CH: CHAR;
BEGIN
  WRITE(PROMPT,': ');
  REPEAT
    READ(KBD,CH);
    IF (CH>='a') AND (CH<='z') ;
  HEX:=H;
END;

FUNCTION HEXSEQ(SEQ: STR8): STR24;
VAR
  I: INTEGER;
  S: STR24;
BEGIN
  IF SEQ='' THEN HEXSEQ:='Unconfigured' ELSE
  BEGIN
    S:='';
    FOR I:=1 TO LEN(SEQ) DO S:=S+HEX(ORD(SEQ[I]),2)+' ';
    HEXSEQ:=COPY(S,1,LEN(S)-1);
THEN CH:=CHR(ORD(CH)-32);
  UNTIL CH IN OKCH;
  IF CH=^M THEN BACKSP(LEN(PROMPT)+2) ELSE
  BEGIN
    WRITELN(CH); WRITELN;
  END;
  SELECT:=CH;
END;

PROCEDURE PRESSRETURN;
VAR
  CH: CHAR;
BEGIN
  WRITE('Press RETURN...');
  REPEAT READ(KBD,C  END;
END;

FUNCTION YESNO(FLAG: INTEGER): STR4;
BEGIN
  IF FLAG<>0 THEN YESNO:='YES' ELSE YESNO:='NO';
END;

PROCEDURE BACKSP(N: INTEGER);
VAR
  I: INTEGER;
BEGIN
  FOR I:=1 TO N DO WRITE(^H' '^H);
END;

FUNCTION READNUM(MIN,MAX: INTEGER):H) UNTIL CH=^M;
  BACKSP(15);
END;

PROCEDURE RESETDISKS;
BEGIN
  BDOS(37,-1);
END;

PROCEDURE CONFIGURE;
VAR
  CH: CHAR;

(*$I INSTCRT.PAS*)

PROCEDURE KEYBOARD;
TYPE
  KEYREC = RECORD
             VAL: BYTE; STR: STR12;
           END;
CONST
  STDKEY: ARRAY[1..40] OF STR2 =
    (^J,^S,^D,^A,^F,^Q^S,^Q^D,^E,^X,^Q^E,^Q^X,^R,^C,^Q^R,^Q^C,
     @127,^G,^Q@127,^Q^Y,^T,^Y,^M,^I,^N,^V,^Z,^B,^W,^Q^F,^Q^A,
     ^L,^K^B,^K^K,^K^Y,^K^C,^K^V,^K^P,^K^H,^K^D,^K^X);
VAR
  C,I,N,M: INTEGER;
  C;
  WRITELN;
END;

PROCEDURE HELP;
BEGIN
  WRITELN('To be able to benefit fully from the special keys offered by');
  WRITELN('your terminal''s keyboard, COMPAS allows you to define alternate');
  WRITELN('keys to invoke selected editor functions. H,MC: CHAR;
  S: STR12;
  AKEY: ARRAY[1..40] OF KEYREC;

FUNCTION KEYSTR(CH: CHAR): STR3;
BEGIN
  CASE CH OF
    @32..@126,@128..@255: KEYSTR:='"'+CH+'"';
    @8: KEYSTR:='BS';
    @13: KEYSTR:='CR';
    @27: KEYSTR:='ESC';
    @127: KEYSTR:='DEA typical example of');
  WRITELN('alternate keys is defining your cursor arrows to do the same as');
  WRITELN('^S, ^D, ^E and ^X');
  WRITELN;
  WRITELN('To add an alternate key definition, you must first select the');
  WRITELN('function for which L';
  OTHERWISE
    KEYSTR:='^'+CHR(ORD(CH)+64);
  END;
END;

FUNCTION KEYSEQ(KS: STR12): STR48;
VAR
  I: INTEGER;
  S: STR48;
BEGIN
  S:='';
  FOR I:=1 TO LEN(KS) DO S:=S+KEYSTR(KS[I])+' ';
  KEYSEQ:=COPY(S,1,LEN(S)-1);
END;

PROCEDURE DELyou want to create an alternative. This you');
  WRITELN('do by entering the standard key sequence, i.e. the sequence lis-');
  WRITELN('ted in the manual. Once you have selected a function, you will');
  WRITELN('be prompted for an alternate key sequenAKEY(I: INTEGER);
VAR
  P: INTEGER;
BEGIN
  FOR P:=I+1 TO N DO AKEY[P-1]:=AKEY[P]; N:=N-1;
END;

PROCEDURE ADDAKEY;
VAR
  I,L: INTEGER;
  CH: CHAR;
  S: STR12;
BEGIN
  L:=0; FOR I:=1 TO N DO L:=L+LEN(AKEY[N].STR)+2;
  IF (N=40) OR (L>240) THEce, to which you must an-');
  WRITELN('swer by entering the alternate sequence. To end the alternate');
  WRITELN('sequence, press RETURN.');
  WRITELN;
  WRITELN('Note that it is actually possible to override the standard key');
  WRITELN('sequencesN
  WRITELN('No room for further definitions') ELSE
  BEGIN
    WRITE('Standard: ');
    REPEAT
      READ(KBD,CH);
      I:=1; WHILE (I<40) AND (CH<>STDKEY[I][1]) DO I:=I+1;
      IF STDKEY[I][1]=CH THEN
      BEGIN
        S:=CH; WRITE(KEYSEQ(CH. If you for instance define ^J to be an alternate key');
  WRITELN('for the ^X function, the original ^J function will become inac-');
  WRITELN('cessible unless you define an alternate sequence for it as well.');
  WRITELN;
  PRESSRETURN;
END;

BE),' '); L:=LEN(KEYSEQ(CH))+1;
        IF LEN(STDKEY[I])=2 THEN
        BEGIN
          READ(KBD,CH); S:=S+CH;
          I:=1; WHILE (I<40) AND (S<>STDKEY[I]) DO I:=I+1;
          IF S=STDKEY[I] THEN
          BEGIN
            S:=S+CH; WRITE(KEYSEQ(GIN (*KEYBOARD*)
  WITH DATA DO
  BEGIN
    I:=0; N:=0; C:=1;
    WHILE ALTKEY[I]<>0 DO
    BEGIN
      N:=N+1;
      MOVE(ALTKEY[I],AKEY[N],ALTKEY[I+1]+2);
      I:=I+ALTKEY[I+1]+2;
    END;
    REPEAT
      WRITELN('ALTERNATE KEY DEFINITIONS:'CH),' '); L:=L+LEN(KEYSEQ(CH))+1;
          END ELSE
          BEGIN
            S:=''; BACKSP(L);
          END;
        END;
      END ELSE S:='';
    UNTIL S<>'';
    WRITE('':9-L,'Alternate: ');
    S:='';
    REPEAT
      READ(KBD,CH);
   );
      WRITELN;
      IF N=0 THEN
      BEGIN
        WRITELN('No alternate keys defined'); WRITELN;
        CH:=SELECT('Add(Z), Exit(X), Help(Y)',['Z','X','Y']);
      END ELSE
      BEGIN
        IF C+9>N THEN M:=N-C ELSE M:=9;
        FOR I:=   IF (LEN(S)<12) AND (CH<>^M) THEN
      BEGIN
        IF LEN(S)>=1 THEN IF CH IN [^A..^Z] THEN CH:=CHR(ORD(CH)+64);
        WRITE(KEYSTR(CH),' '); S:=S+CH;
      END;
    UNTIL CH=^M;
    N:=N+1; AKEY[N].VAL:=I; AKEY[N].STR:=S;
    WRITELN;
  END0 TO M DO
        BEGIN
          S:=KEYSEQ(STDKEY[AKEY[C+I].VAL]);
          WRITE(CHR(I+65),'. Standard: ',S,'':9-LEN(S));
          WRITELN('Alternate: ',KEYSEQ(AKEY[C+I].STR));
        END;
        IF N>10 THEN
        BEGIN
          WRITELN; WRITELN('Press RETURN to view more');
        END;
        WRITELN;
        MC:=CHR(M+65);
        CH:=SELECT('Delete(A-'+MC+'), Add(Z), Exit(X), Help(Y)',
                   ['A'..MC,'Z','X','Y',^M]);
      END;
      CASE CH OF
        'A'..'J': Experiment to find a suitable value (typical values range');
  WRITELN('from 200 to 1000).');
  WRITELN;
  WRITELN('CONFIGURATION NAME. This field defines the name of the current');
  WRITELN('configuration (usually, it is the name of your computer). UDELAKEY(C+ORD(CH)-65);
        'Z': ADDAKEY;
        'Y': HELP;
        ^M: BEGIN
              C:=C+10; IF C>N THEN C:=1;
            END;
      END;
    UNTIL CH='X';
    I:=0;
    FOR N:=1 TO N DO
    BEGIN
      MOVE(AKEY[N],ALTKEY[I],LEN(AKp to');
  WRITELN('31 characters may be entered.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*MISC*)
  WITH DATA DO
  REPEAT
    WRITELN('MISCELLANEOUS DATA:');
    WRITELN;
    WRITELN(PA,YESNO(BACKF));
    WRITELN(PB,YESNO(INSMF));
    WRITELNEY[N].STR)+2);
      I:=I+LEN(AKEY[N].STR)+2;
    END;
    FILL(ALTKEY[I],256-I,0);
  END;
END;

PROCEDURE MISC;
CONST
  PA: STR36 = 'A. Use BAK files (YES/NO).........: ';
  PB: STR36 = 'B. Insert mode on (YES/NO)........: ';
  PC: STR36 = 'C. (PC,YESNO(AUTOF));
    WRITELN(PD,YESNO(TABSF));
    WRITELN(PE,RDELAY);
    WRITELN(PF,TERMNAME);
    WRITELN;
    CH:=SELECT('Edit(A-F), Exit(X), Help(Y)',['A'..'F','X','Y']);
    CASE CH OF
      'A': BEGIN
	     WRITE(PA); BACKF:=READYN; WRITELAuto-indent on (YES/NO)........: ';
  PD: STR36 = 'D. TABS mode on (YES/NO)..........: ';
  PE: STR36 = 'E. Replace prompt delay...........: ';
  PF: STR36 = 'F. Configuration name.............: ';
VAR
  CH: CHAR;

PROCEDURE HELP;
BEGIN
  WRITELN(N;
	   END;
      'B': BEGIN
	     WRITE(PB); INSMF:=READYN; WRITELN;
	   END;
      'C': BEGIN
	     WRITE(PC); AUTOF:=READYN; WRITELN;
	   END;
      'D': BEGIN
	     WRITE(PD); TABSF:=READYN; WRITELN;
	   END;
      'E': BEGIN
	     WRITE(PE'USE BAK FILES. This field must be either YES or NO. If it is');
  WRITELN('set to YES, duplicate files will have their type changed to');
  WRITELN('BAK when the SAVE command is used to save a file. Otherwise,');
  WRITELN('such files are simply delete); RDELAY:=READNUM(0,32767); WRITELN;
	   END;
      'F': BEGIN
	     WRITE(PF); BUFLEN:=31; READLN(TERMNAME); WRITELN;
	   END;
      'Y': HELP;
    END;
  UNTIL CH='X';
END;

PROCEDURE CLEAR;
BEGIN
  WRITE('Clear configuration data (YES/NO)? d.');
  WRITELN;
  WRITELN('INSERT MODE ON. This field defined the initial state of the');
  WRITELN('INSERT mode when COMPAS is cold-started. YES means on and NO');
  WRITELN('means off.');
  WRITELN;
  WRITELN('AUTO-INDENT ON. This field defines th');
  IF READYN<>0 THEN
  BEGIN
    FILL(DATA,SIZE(DATA),0);
    WITH DATA DO
    BEGIN
      WIDTH:=79; HEIGHT:=24; GXYLS:=@27'=';
      COOROFS:=32; CLHS:=@26; BACKF:=255;
      INSMF:=255; AUTOF:=255; RDELAY:=1000;
    END;
  END;
  WRITELN;e initial state of the');
  WRITELN('auto-indent tabulator when COMPAS is cold-started.');
  WRITELN;
  WRITELN('TABS MODE ON. This field defines the initial state of the TABS');
  WRITELN('mode when COMPAS is cold-started.');
  WRITELN;
  PRESSRETUR
END;

PROCEDURE HELP;
BEGIN
  WRITELN('To do a complete installation of COMPAS you should go through');
  WRITELN('all functions of this menu (the order in which you do it is of');
  WRITELN('no importance, as long as you make sure that all fields wN;
  WRITELN('REPLACE PROMPT DELAY. This field is used only by the find/re-');
  WRITELN('place function in the editor. It defines the delay used when mo-');
  WRITELN('ving the cursor alternately between the replace prompt and the');
  WRITELN('text. ithin');
  WRITELN('all menus have be inspected and modified if necessary).');
  WRITELN;
  WRITELN('CRT CONFIGURATION. This function is used to view and/or modify');
  WRITELN('the CRT configuration table and the user patch area.');
  WRITELN;
  WRITELN('KEYBOARD CONFIGURATION. This function is used to view and/or');
  WRITELN('modify alternate key definitions.');
  WRITELN;
  WRITELN('MISCELLANEOUS DATA. This function allows you to view and/or');
  WRITELN('modify various system informations.');RN;
END;

PROCEDURE SAVEH;
BEGIN
  WRITELN('To save the current configuration as a standard configuration,');
  WRITELN('use the RETURN key to move to a section that contains an empty');
  WRITELN('entry, and enter the letter of that entry. You may,
  WRITELN;
  WRITELN('CLEAR CONFIGURATION DATA. This function will initialize all con-');
  WRITELN('figuration data fields to some appropriate default values. If');
  WRITELN('you are about to install a new terminal, use this function be-');
  WRITE if you wish');
  WRITELN('save the current configuration on top of an existing configura-');
  WRITELN('tion, in which case that cofiguration is lost. Note that if the');
  WRITELN('terminal name of the configuration you save is empty, you will');
  WLN('fore the above ones - this will save you the trouble of manually');
  WRITELN('removing the existing values.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*CONFIGURE*)
  WITH DATA DO
  REPEAT
    WRITELN('MAIN CONFIGURATION MENU:');
    WRITELN;RITELN('not be able to load the configuration again.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*LSCONFIG*)
  CC:=1; DONE:=FALSE; IF LOAD THEN LS:='Load' ELSE LS:='Save';
  REPEAT
    WRITELN('STANDARD CONFIGURATIONS (MENU ',(CC+9) DIV 10,'):');
  
    WRITELN('1. CRT configuration');
    WRITELN('2. Keyboard configuration');
    WRITELN('3. Miscellaneous data');
    WRITELN('4. Clear configuration data');
    WRITELN;
    CH:=SELECT('Function(1-4), Exit(X), Help(Y)',['1'..'4','X','Y']);
    C  WRITELN;
    FOR I:=0 TO 9 DO
    WRITELN(CHR(I+65),'. ',TNAM[CC+I]);
    WRITELN;
    WRITELN('Press RETURN to view more');
    WRITELN;
    CH:=SELECT(LS+'(A-J), Exit(X), Help(Y)',['A'..'J','X','Y',^M]);
    CASE CH OF
      'A'..'J': BEGIN
		ASE CH OF
      '1': CRT;
      '2': KEYBOARD;
      '3': MISC;
      '4': CLEAR;
      'Y': HELP;
    END;
  UNTIL CH='X';
END;

PROCEDURE LSCONFIG(LOAD: BOOLEAN);
VAR
  I,C,CC: INTEGER;
  CH: CHAR;
  DONE: BOOLEAN;
  LS: STR4;

PROCEDURE  C:=CC+ORD(CH)-65; IF LOAD THEN LOADC ELSE SAVEC;
		END;
      'X': DONE:=TRUE;
      'Y': IF LOAD THEN LOADH ELSE SAVEH;
      ^M: BEGIN
	    CC:=CC+10; IF CC>MAXTERM THEN CC:=1;
	  END;
    END;
  UNTIL DONE;
END;

PROCEDURE GETDATA;
VAR
   LOADC;
VAR
  CH: CHAR;
BEGIN
  IF TNAM[C]<>'' THEN
  BEGIN
    SEEK(DF,C-1); READ(DF,DATA); DONE:=TRUE;
  END ELSE
  BEGIN
    WRITE('ERROR: Undefined configuration. Press RETURN...');
    REPEAT READ(KBD,CH) UNTIL CH=^M;
    BACKSP(47);
  ENDA: INTEGER;
BEGIN
  SEEK(CF,0); BLOCKREAD(CF,B1,6);
  A:=B1[1]+SWAP(B1[2])+3;
  B2S:=A DIV 128-2; B2A:=A MOD 128;
  SEEK(CF,B2S); BLOCKREAD(CF,B2,4);
  MOVE(B1[$20],DATA.TERMNAME,$285);
  MOVE(B2[B2A],DATA.BACKF,$106);
END;

PROCEDURE PUTDATA;
V;
END;

PROCEDURE SAVEC;
BEGIN
  SEEK(TF,C-1); WRITE(TF,DATA.TERMNAME);
  SEEK(DF,C-1); WRITE(DF,DATA);
  TNAM[C]:=DATA.TERMNAME; DONE:=TRUE;
END;

PROCEDURE LOADH;
BEGIN
  WRITELN('To load a standard configuration, simply press the letter de-'AR
  I: INTEGER;
BEGIN
  MOVE(DATA.TERMNAME,B1[$20],$285);
  MOVE(DATA.BACKF,B2[B2A],$106);
  SEEK(CF,0); BLOCKWRITE(CF,B1,6);
  SEEK(CF,B2S); BLOCKWRITE(CF,B2,4);
END;

PROCEDURE HELP;
BEGIN
  WRITELN('LOAD STANDARD CONFIGURATION. This function);
  WRITELN('noting that configuration. If none of the standard configura-');
  WRITELN('tions mentioned match your computer system, you will have to');
  WRITELN('install COMPAS manually (using function 2 on the main menu).');
  WRITELN;
  PRESSRETU is used to load a');
  WRITELN('standard configuration, i.e. to load all the parameters that');
  WRITELN('define a specific computer system. If your computer system is');
  WRITELN('among the standard configurations, then all you need to do to');
  WRITELN('install COMPAS is to load that configuration and exit. If it');
  WRITELN('is not, you must define your computer system manually, using');
  WRITELN('the function described below.');
  WRITELN;
  WRITELN('EDIT CONFIGURATION PARAMETERS. This fune INSTALL program cannot be run without these');
    WRITELN('files, so copy them onto your disk, and run INSTALL again.');
    GOTO EXIT;
  END;
  REPEAT
    WRITE('Input file name (RETURN for COMPAS.COM)? ');
    BUFLEN:=14; READLN(CFN); WRITELN;
ction is used to set up');
  WRITELN('new configurations and to edit an existing configuration. It');
  WRITELN('allows you to view and/or modify all parameters that define a');
  WRITELN('specific computer system. If your computer is not mentioned in')    IF CFN='' THEN CFN:='COMPAS.COM';
    ASSIGN(CF,CFN); (*$I-*) RESET(CF) (*$I+*);
    I:=IORES;
    IF I>0 THEN
    BEGIN
      WRITELN('That file does not exist. Please specify another file name.');
      WRITELN('You may insert another disk if y;
  WRITELN('the list of standard configurations (see above), you must use');
  WRITELN('this function to define it manually.');
  WRITELN;
  WRITELN('SAVE A STANDARD CONFIGURATION. This function is used to add');
  WRITELN('an entry to the list of stou wish.');
      WRITELN;
      RESETDISKS;
    END;
  UNTIL I=0;
  GETDATA;
  REPEAT
    WRITELN('COMPAS-80 INSTALL PROGRAM MAIN MENU:');
    WRITELN;
    WRITELN('1. Load a standard configuration');
    WRITELN('2. Edit configuration parameterandard configurations. Normally, you');
  WRITELN('will not need to use this function.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN
  WRITELN;
  WRITELN('              COMPAS-80 V3.02 INSTALL PROGRAM');
  WRITELN('                      CP/M-80 versions');
    WRITELN('3. Save a standard configuration');
    WRITELN;
    WRITE('CURRENT CONFIGURATION: ');
    IF DATA.TERMNAME<>'' THEN
    WRITELN(DATA.TERMNAME) ELSE WRITELN('No terminal selected');
    WRITELN;
    CH:=SELECT('Function(1-3), Exit(');
  WRITELN;
  WRITELN('                   Copyright (C) 1983 by');
  WRITELN('                 Poly-Data microcenter ApS');
  WRITELN;
  WRITELN;
  WRITELN('This program is used to view and/or modify the configuration');
  WRITELN('parameters of X), Help(Y)',['1'..'3','X','Y']);
    CASE CH OF
      '1': LSCONFIG(TRUE);
      '2': CONFIGURE;
      '3': LSCONFIG(FALSE);
      'Y': HELP;
    END;
  UNTIL CH='X';
  WRITE('Save configuration in ',CFN,' (YES/NO)? ');
  IF READYN<>0 THEN
  BEGCOMPAS. If you have bought an unconfigured copy');
  WRITELN('of COMPAS, you should use this program to define your computer');
  WRITELN('system before running COMPAS. If your copy is already set up');
  WRITELN('for a specific computer system, there iIN
    PUTDATA; CLOSE(CF);
  END;
  CLOSE(TF); CLOSE(DF);
  EXIT:
END.
;
      'Y': HELP;
    END;
  UNTIL CH='X';
  WRITE('Save configuration in ',CFN,' (YES/NO)? ');
  IF READYN<>0 THEN
  BEGs no need to run this');
  WRITELN('program, unless you wish to make changes to suit your indivi-');
  WRITELN('dual needs.');
  WRITELN;
  WRITE('Do you wish to proceed (YES/NO)? ');
  IF READYN=0 THEN GOTO EXIT;
  WRITELN;
  ASSIGN(TF,'INSTALL.TRMוווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווו