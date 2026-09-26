PROGRAM HEXDUMP; (*$A+,R-*)

(* This program will output a hex dump af any disk file. Each	*)
(* line shows the address of the first byte of the line, then	*)
(* 16 bytes in hex, and then the same bytes in ASCII, if they	*)
(* are printable. On runninווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווg the program, you must specify the	*)
(* name of the disk file to be dumped, and the name of the disk	*)
(* file or logical device (CON:, LST:, etc.), which is to reci-	*)
(* eve the dump.						*)

LABEL EXIT;

TYPE
  SECTOR = ARRAY[0..7,0..15] OFוווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווו BYTE;
  HEXSTRING = STRING[4];
  FILENAME = STRING[14];

VAR
  ADDRESS,L,P,I,J: INTEGER;
  CH: CHAR;
  INNAME,OUTNAME: FILENAME;
  BUFFER: SECTOR;
  INFILE: FILE;
  OUTFILE: TEXT;

FUNCTION HEX(NUMBER,DIGITS: INTEGER): HEXSTRING;
CONST
  HEXווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווDIGIT: ARRAY[0..15] OF CHAR = '0123456789ABCDEF';
VAR
  D: INTEGER;
  H: HEXSTRING;
BEGIN
  H[0]:=CHR(DIGITS);
  FOR D:=DIGITS DOWNTO 1 DO
  BEGIN
    H[D]:=HEXDIGIT[NUMBER AND 15];
    NUMBER:=NUMBER SHR 4;
  END;
  HEX:=H;
END;

BEGIN
  WRוווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווו