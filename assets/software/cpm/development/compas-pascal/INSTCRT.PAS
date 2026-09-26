PROCEDURE CRT;
VAR
  CH: CHAR;

PROCEDURE EDITCRT;
CONST
  PA1: STR36 = 'A. Screen width (in characters)...: ';
  PB1: STR36 = 'B. Screen height (in lines).......: ';
  PC1: STR36 = 'C. GOTOXY lead-in sequence........: ';
  PD1: STR36 = 'D. GOTOXYEQUENCE. The character sequence sent prior to');
  WRITELN('the coordinates. The maximum length is 8.');
  WRITELN;
  WRITELN('GOTOXY SEPARATOR SEQUENCE. The character sequence sent between');
  WRITELN('the coordinates. The maximum length is 4.');
   separator sequence......: ';
  PE1: STR36 = 'E. GOTOXY terminator sequence.....: ';
  PF1: STR36 = 'F. Line before column (YES/NO)....: ';
  PG1: STR36 = 'G. Coordinate offset..............: ';
  PH1: STR36 = 'H. Coordinate format (0/2/3)......: ';
 WRITELN;
  WRITELN('GOTOXY TERMINATOR SEQUENCE. The character sequence sent after');
  WRITELN('the coordinates. The maximum length is 4.');
  WRITELN;
  WRITELN('LINE BEFORE COLUMN. This field should be set to YES if your');
  WRITELN('video display  PA2: STR36 = 'A. CLRHOM sequence................: ';
  PB2: STR36 = 'B. CLREOS sequence................: ';
  PC2: STR36 = 'C. CLREOL sequence................: ';
  PD2: STR36 = 'D. INSLIN sequence................: ';
  PE2: STR36 = 'E. DELLIN sequencrequires the line coordinate (Y) to be sent');
  WRITELN('before the column coordinate (X). Otherwise it should be set');
  WRITELN('to NO.');
  WRITELN;
  PRESSRETURN;
  WRITELN('COORDINATE OFFSET. This field defines the value (in decimal)');
  WRITe................: ';
  PF2: STR36 = 'F. RVSON sequence.................: ';
  PG2: STR36 = 'G. RVSOFF sequence................: ';
VAR
  SEC: INTEGER;
  CH,MC,FIRST,LAST: CHAR;

PROCEDURE HELPS;
BEGIN
  WRITELN('Character sequences are entered asELN('to be added to the coordinates before they are transmitted.');
  WRITELN('If the coordinate format (see below) is 0, then 32 is normally');
  WRITELN('used. If the coordinate format is 2 or 3, then 0 or 1 is nor-');
  WRITELN('mally used.');
  WRI sequences of hex values be-');
  WRITELN('tween 00 and FF. Each hex value must be separated from the sur-');
  WRITELN('rounding ones by at least one blank. To enter an empty sequence');
  WRITELN('simply enter a blank line.');
  WRITELN;
END;

PROTELN;
  WRITELN('COORDINATE FORMAT. A value of 0 in this field indicates that');
  WRITELN('the coordinates are to be transmitted as single bytes using');
  WRITELN('binary format. Other values (2 or 3) indicate that the coor-');
  WRITELN('dinates areCEDURE HELP1;
BEGIN
  WRITELN('All fields on this submenu must be filled in for COMPAS to ope-');
  WRITELN('rate correctly. Note however that if you install a user written');
  WRITELN('machine code driver for GOTOXY, fields C-H are ignored.');
  WRI to be transmitted as decimal character strings of');
  WRITELN('2 or 3 characters.');
  WRITELN;
  PRESSRETURN;
END;

PROCEDURE HELP2;
BEGIN
  HELPS;
  WRITELN('CLRHOM SEQUENCE. The function sequence which clears the screen');
  WRITELN('and retTELN;
  WRITELN('SCREEN WIDTH. This field defines the number of characters per');
  WRITELN('line on your video display. If the display scrolls when writing');
  WRITELN('a character to the bottom right character position, then specify');
  WRITELN('thurns the cursor to the top left corner. The maximum');
  WRITELN('is 8. This function sequence must be specified for COMPAS to');
  WRITELN('operate correctly');
  WRITELN;
  WRITELN('All of the following function sequences are optional. The maxi-');
e screen width less one.');
  WRITELN;
  WRITELN('SCREEN HEIGHT. This field defines the number of lines per screen');
  WRITELN('on your video display. Always specify the exact value.');
  WRITELN;
  HELPS;
  PRESSRETURN;
  WRITELN('GOTOXY LEAD-IN S  WRITELN('mum length is 8 for all sequences.');
  WRITELN;
  WRITELN('CLREOS SEQUENCE. The function sequence which clears all charac-');
  WRITELN('ter positions from the cursor to the end of the screen.');
  WRITELN;
  PRESSRETURN;
  WRITELN('CLREOL SEQUENCE. The function sequence which clears all charac-');
  WRITELN('ter positions from the cursor to the end of the current line.');
  WRITELN;
  WRITELN('INSLIN SEQUENCE. The function sequence which scrolls the current');
  WRITELN('line, and all    FIRST:='A'; LAST:=MC;
      END ELSE
      BEGIN
        FIRST:=CH; LAST:=CH;
      END;
      FOR CH:=FIRST TO LAST DO
      CASE SEC OF
	1: CASE CH OF
	     'A': BEGIN
		    WRITE(PA1); WIDTH:=READNUM(40,255);
		  END;
	     'B': BEGIN
		 lines below it, down, and clears the current line.');
  WRITELN;
  WRITELN('DELLIN SEQUENCE. The function sequence which deletes the current');
  WRITELN('line, and scrolls up all lines below it, with a blank line ap-');
  WRITELN('pearing at the bott    WRITE(PB1); HEIGHT:=READNUM(8,255);
		  END;
	     'C': BEGIN
		    WRITE(PC1); GXYLS:=READSEQ(8);
		  END;
	     'D': BEGIN
		    WRITE(PD1); GXYSS:=READSEQ(4);
		  END;
	     'E': BEGIN
		    WRITE(PE1); GXYTS:=READSEQ(4);
		  END;
	     'om. The maximum length is 8.');
  WRITELN;
  WRITELN('RVSON SEQUENCE. The function sequence which turns on reverse vi-');
  WRITELN('deo (or increased intensity). If this function is specified, the');
  WRITELN('editor will use it to highlight the statF': BEGIN
		    WRITE(PF1); COLB4LIN:=255-READYN;
		  END;
	     'G': BEGIN
		    WRITE(PG1); COOROFS:=READNUM(0,255);
		  END;
	     'H': BEGIN
		    WRITE(PH1); COORFMT:=READNUM(0,3);
		  END;
	     'Y': HELP1;
	   END;
	2: CASE CH OF
	     'us line.');
  WRITELN;
  WRITELN('RVSOFF SEQUENCE. The function sequence which turns off the at-');
  WRITELN('tribute activated by the sequence above.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*EDITCRT*)
  SEC:=1;
  WITH DATA DO
  REPEAT
    WA': BEGIN
		    WRITE(PA2); CLHS:=READSEQ(8);
		  END;
	     'B': BEGIN
		    WRITE(PB2); CESS:=READSEQ(8);
		  END;
	     'C': BEGIN
		    WRITE(PC2); CELS:=READSEQ(8);
		  END;
	     'D': BEGIN
		    WRITE(PD2); ILNS:=READSEQ(8);
		  END;
	  RITELN('CRT CONFIGURATION TABLE (SECTION ',SEC,'):');
    WRITELN;
    CASE SEC OF
      1: BEGIN
	   WRITELN(PA1,WIDTH);
	   WRITELN(PB1,HEIGHT);
	   WRITELN(PC1,HEXSEQ(GXYLS));
	   WRITELN(PD1,HEXSEQ(GXYSS));
	   WRITELN(PE1,HEXSEQ(GXYTS));
	      'E': BEGIN
		    WRITE(PE2); DLNS:=READSEQ(8);
		  END;
	     'F': BEGIN
		    WRITE(PF2); RONS:=READSEQ(8);
		  END;
	     'G': BEGIN
		    WRITE(PG2); ROFS:=READSEQ(8);
		  END;
	     'Y': HELP2;
	   END;
      END;
      IF CH IN ['A'..MCWRITELN(PF1,YESNO(255-COLB4LIN));
	   WRITELN(PG1,COOROFS);
	   WRITELN(PH1,COORFMT);
	 END;
      2: BEGIN
	   WRITELN(PA2,HEXSEQ(CLHS));
	   WRITELN(PB2,HEXSEQ(CESS));
	   WRITELN(PC2,HEXSEQ(CELS));
	   WRITELN(PD2,HEXSEQ(ILNS));
	   WRITELN(PE2] THEN WRITELN;
    END;
  UNTIL CH='X';
END;

PROCEDURE EDITUWD;
VAR
  CH: CHAR;

FUNCTION VECTOR(A: INTEGER): STR12;
BEGIN
  IF A=0 THEN VECTOR:='Unconfigured' ELSE VECTOR:=HEX(A,4);
END;

FUNCTION READVECT(OKZERO: BOOLEAN): INTEGER;
VAR
,HEXSEQ(DLNS));
	   WRITELN(PF2,HEXSEQ(RONS));
	   WRITELN(PG2,HEXSEQ(ROFS));
	 END;
    END;
    WRITELN;
    IF (SEC=1) AND (VGXY<>0) THEN
    BEGIN
      WRITELN('User written driver for GOTOXY.'); WRITELN;
    END;
    WRITELN('Press RETURN t  V,E: INTEGER;
  S: STR4;
BEGIN
  REPEAT
    BUFLEN:=4; READ(S);
    IF (S='') AND OKZERO THEN
    BEGIN
      V:=0; E:=0;
    END ELSE
    BEGIN
      VAL('$'+S,V,E);
      IF E=0 THEN IF (V<$1A5) OR (V>$3A4) THEN E:=1;
      IF E>0 THEN BACKo view more');
    WRITELN;
    IF SEC=1 THEN MC:='H' ELSE MC:='G';
    CH:=SELECT('Edit(A-'+MC+'), All(Z), Exit(X), Help(Y)',
    	       ['A'..MC,'Z','X','Y',^M]);
    IF CH=^M THEN SEC:=3-SEC ELSE
    BEGIN
      IF CH='Z' THEN
      BEGIN
    SP(LEN(S));
    END;
  UNTIL E=0;
  WRITELN; READVECT:=V;
END;

PROCEDURE EDITPATCH;
VAR
  CH: CHAR;
  I,J,C: INTEGER;

PROCEDURE MODIFYDATA;
VAR
  AD,D,E: INTEGER;
  S: STR4;
BEGIN
  WRITE('Start address: '); AD:=READVECT(FALSE)-$1A5; WRITELN;
  WITH DATA DO
  REPEAT
    WRITE(HEX(AD+$1A5,4),HEX(PATCH[AD],2):3,': ');
    REPEAT
      BUFLEN:=2; READ(S);
      IF (S<>'') AND (S<>'.') THEN
      BEGIN
	VAL('$'+S,D,E);
	IF E>0 THEN BACKSP(LEN(S)) ELSE PATCH[AD]:=D;
      END ELSE E:=dress.........: ';
  PC: STR36 = 'C. Console input address..........: ';
  PD: STR36 = 'D. Console output address.........: ';
  PE: STR36 = 'E. List output address............: ';
  PF: STR36 = 'F. Auxiliary output address.......: ';
  PG: STR36 = 'G0;
    UNTIL E=0;
    WRITELN; AD:=AD+1;
  UNTIL (S='.') OR (AD=512);
  WRITELN;
END;

PROCEDURE HELP;
BEGIN
  WRITELN('The user patch area is 512 bytes long and starts in memory at');
  WRITELN('address 1A5H. The patch area may actually be used . Auxiliary input address........: ';
VAR
  CH: CHAR;

PROCEDURE HELP;
BEGIN
  WRITELN('The user driver addresses define the entry points of the user');
  WRITELN('written terminal drivers within the user patch area. When a');
  WRITELN('GOTOXY drito store');
  WRITELN('anything, but normally it is used to install user written');
  WRITELN('drivers for terminals that do not support the GOTOXY function.');
  WRITELN('Furthermore, you may in this area install drivers to do the');
  WRITELN('basic ver address is defined (i.e. when the address is not');
  WRITELN('in its "unconfigured" state), it automatically overrides the');
  WRITELN('corresponding fields in the configuration table. When an I/O');
  WRITELN('driver is installed, it automaticallinputting and outputting of characters from and to I/O');
  WRITELN('devices.');
  WRITELN;
  WRITELN('When you select the M (modify) function from the menu, you must');
  WRITELN('first specify the start offset (in hex). This offset must of');
  WRITy overrides the correspon-');
  WRITELN('ding BIOS function call driver.');
  WRITELN;
  WRITELN('Before defining a driver address you should install the driver');
  WRITELN('in the user patch area (to do that, quit this menu, and use');
  WRITELN('fuELN('course be an offset within the patch area, i.e. an offset bet-');
  WRITELN('ween 1A5H and 3A4H. You are then allowed to view and/or modify');
  WRITELN('one byte at a time. To leave a byte unchanged, just enter a');
  WRITELN('blank line. To changnction 1 in the next menu).');
  WRITELN;
  WRITELN('To activate a driver, simply enter the address (in hex) of the');
  WRITELN('driver. To deactivate it again, enter a blank line instead of an');
  WRITELN('address.');
  WRITELN;
  PRESSRETURN;
ENe it to a new value, enter the value in hex.');
  WRITELN('To end, enter a period.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*EDITPATCH*)
  C:=0;
  WITH DATA DO
  REPEAT
    WRITELN('CONTENTS OF USER PATCH AREA:');
    WRITELN;
    FOR I:=C TO D;

BEGIN (*EDITADDR*)
  WITH DATA DO
  REPEAT
    WRITELN('USER WRITTEN DRIVER ADDRESSES:');
    WRITELN;
    WRITELN(PA,VECTOR(VGXY));
    WRITELN(PB,VECTOR(VLCS));
    WRITELN(PC,VECTOR(VLCI));
    WRITELN(PD,VECTOR(VLCO));
    WRITELN(PE,VECC+7 DO
    BEGIN
      WRITE(HEX(I*16+$1A5,4),' ');
      FOR J:=0 TO 15 DO WRITE(HEX(PATCH[I*16+J],2):3);
      WRITELN;
    END;
    WRITELN;
    WRITELN('Press RETURN to view more');
    WRITELN;
    CH:=SELECT('Modify(M), Exit(X), Help(Y)',['MTOR(VLLO));
    WRITELN(PF,VECTOR(VLAO));
    WRITELN(PG,VECTOR(VLAI));
    WRITELN;
    CH:=SELECT('Edit(A-G), Exit(X), Help(Y)',['A'..'G','X','Y']);
    CASE CH OF
      'A': BEGIN
	     WRITE(PA); VGXY:=READVECT(TRUE); WRITELN;
	   END;
      '','X','Y',^M]);
    CASE CH OF
      'M': MODIFYDATA;
      'Y': HELP;
      ^M: C:=(C+8) MOD 32;
    END;
  UNTIL CH='X';
END;

PROCEDURE EDITADDR;
CONST
  PA: STR36 = 'A. GOTOXY address.................: ';
  PB: STR36 = 'B. Console status adB': BEGIN
	     WRITE(PB); VLCS:=READVECT(TRUE); WRITELN;
	   END;
      'C': BEGIN
	     WRITE(PC); VLCI:=READVECT(TRUE); WRITELN;
	   END;
      'D': BEGIN
	     WRITE(PC); VLCO:=READVECT(TRUE); WRITELN;
	   END;
      'E': BEGIN
	     WRITE(PC); VLLO:=READVECT(TRUE); WRITELN;
	   END;
      'F': BEGIN
	     WRITE(PC); VLAO:=READVECT(TRUE); WRITELN;
	   END;
      'G': BEGIN
	     WRITE(PC); VLAI:=READVECT(TRUE); WRITELN;
	   END;
      'Y': HELP;
    END;
  UNTIL CH='X';
END;

PROClist output and auxiliary output drivers receive the character');
  WRITELN('to be output in E.');
  WRITELN;
  WRITELN('Once the code for a driver is installed, its corresponding ad-');
  WRITELN('dress vector should be set to the entry address using EDURE HELP;
BEGIN
  WRITELN('On some terminals the GOTOXY function is not available, and in');
  WRITELN('such cases this function must be supplied through a user writ-');
  WRITELN('ten driver. For the purpose of implementing a user written dri-');
 function 2');
  WRITELN('on this menu.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*EDITUWD*)
  WITH DATA DO
  REPEAT
    WRITELN('USER WRITTEN DRIVERS MENU:');
    WRITELN;
    WRITELN('1. Edit user patch area');
    WRITELN('2. Edit user driver WRITELN('ver, COMPAS provides a user patch area of 512 bytes, which is');
  WRITELN('not otherwise used by the system. The driver must be in Z-80');
  WRITELN('machine code, and to install it, you may use function 1 on this');
  WRITELN('menu. If a dri addresses');
    WRITELN;
    CH:=SELECT('Function(1-2), Exit(X), Help(Y)',['1'..'2','X','Y']);
    CASE CH OF
      '1': EDITPATCH;
      '2': EDITADDR;
      'Y': HELP;
    END;
  UNTIL CH='X';
END;

PROCEDURE HELP;
BEGIN
  WRITELN('Throughver is installed for GOTOXY, it automatically');
  WRITELN('overrides the data given in the configuration table for that');
  WRITELN('specific function.');
  WRITELN;
  WRITELN('Normally COMPAS uses BIOS function calls to do the basic input-');
  WRI function 1 on this menu you may view and/or modify the');
  WRITELN('CRT configuration table. The CRT configuration table defines');
  WRITELN('various informations about your terminal, e.g. the number of');
  WRITELN('characters per line and the numbeTELN('ting and outputting of characters from and to logical I/O devi-');
  WRITELN('ces (console, printer, and auxiliary). You may however write');
  WRITELN('your own basic I/O drivers if you prefer. The basic I/O system');
  WRITELN('of COMPAS constitr of lines per screen. Fur-');
  WRITELN('thermore, it defines the control sequences used to move the');
  WRITELN('cursor, clear the screen, etc.');
  WRITELN;
  WRITELN('Some computers and terminals do not support a position cursor');
  WRITELN('funues six drivers: Console status, console input,');
  WRITELN('console output, list output, auxiliary output and auxiliary in-');
  WRITELN('put, and when a driver is installed, it automatically overrides');
  WRITELN('the corresponding BIOS driver.');
ction, and in such cases a user written driver must be em-');
  WRITELN('ployed. Furthermore, some computers require user written I/O');
  WRITELN('drivers to perform the basic inputting and outputting of cha-');
  WRITELN('racters from and to logical I  WRITELN;
  PRESSRETURN;
  WRITELN('A user written driver may use all registers, and it must return');
  WRITELN('through a RET instruction. The GOTOXY driver receives (X,Y) in');
  WRITELN('(E,D), and the upper left corner corresponds to (E,D)=(0,0)./O devices. User written drivers');
  WRITELN('are written in Z-80 machine code, and they may be installed');
  WRITELN('using function 2 on this menu.');
  WRITELN;
  PRESSRETURN;
END;

BEGIN (*CRT*)
  REPEAT
    WRITELN('CRT CONFIGURATION MENU:' The');
  WRITELN('console status driver must return A=0FFH if a character is ready');
  WRITELN('and A=00H if not. The console input and auxiliary input drivers');
  WRITELN('must return the input character in A, and the console output,');
  WRITELN(');
    WRITELN;
    WRITELN('1. Edit CRT configuration table');
    WRITELN('2. Edit user written drivers');
    WRITELN;
    CH:=SELECT('Function(1-2), Exit(X), Help(Y)',['1'..'2','X','Y']);
    CASE CH OF
      '1': EDITCRT;
      '2': EDITUWD;
      'Y': HELP;
    END;
  UNTIL CH='X';
END;
