	PAGE	65
	.8080
;
;
;        NAME    B3780C          ;USER CONFIGURATION MODULE
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;                                                               ;
;       (C) 1982 MICRO-INTEGRATION PARAMETERS ARE TO BE     ;
;       CHANGED.                                                ;
;                                                               ;
;                                                               ;
;;;;;;;;;;;;;;;;;;;;;;;;;; INC. ALL RIGHTS RESERVED,    ;
;       NO PART OF THIS PROGRAM OR PUBLICATION MAY BE           ;
;       REPRODUCED, TRANSMITTED, TRANSCRIBED, STORED IN         ;
;       A RETRIEVAL SYSTEM, OR TRANSLATED INTO ANY LANGUAGE     ;
;       OR COMPUTER LA;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
TRUE    EQU     1
FALSE   EQU     0
M2770   EQU     4
M3780   EQU     2
M3741	EQU	6
M2780	EQU	0
MCPU    EQU     8
IN8251  EQU     2
Z80SIO  EQU     3
IN8274	EQU	3
CPM	EQU	5
BASEAD  EQU     100H        NGUAGE, IN ANY FORM OR BY ANY MEANS,      ;
;       ELECTRONIC, MECHANICAL, MAGNETIC, OPTICAL, CHEMICAL,    ;
;       MANUAL OR OTHERWISE, WITHOUT THE PRIOR WRITTEN          ;
;       PERMISSION OF:                                          ;
;             ;BASE ADDRESS FOR THIS MODULE
;        ORG     BASEAD          ;ORG TO MODULE START ADDRESS
        JMP     USDTIN          ;USART DATA INPUT
        JMP     USDTOT          ;USART DATA OUTPUT
        JMP     USSTIN          ;USART STATUS INPUT
              MICRO-INTEGRATION INC.                    ;
;                     63 MAPLE STREET                           ;
;                     FRIENDSVILLE, MD. 21531                   ;
;                     USA , EARTH                               ;      JMP     USSTOT          ;USART STATUS OUTPUT
        JMP     TMCTOT          ;TIMER CONTROL OUTPUT
        JMP     TMDTIN          ;TIMER DATA INPUT
        JMP     TMDTOT          ;TIMER DATA OUTPUT
        JMP     RTMODE          ;RETURN DEVICE
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
;                   PHILIPS P2000C-MODIFICATION                 ;
;       PREPARED BY G.HILLEBRECHT, TELECOM LABOR WIEN - DC      ;
;       DATE:  16. AUGUST 1984      V5.0 / SER# =  MODE
        JMP     RTCMPR          ;RETURN COMPRESS DEFAULT
        JMP     RTCMTB          ;RETURN COMMAND TABLE ADDRESS
        JMP     RTXLAT          ;RETURN TRANSLATE TABLE ADDRESS
        JMP     RTFLEX          ;RETURN NOTRANSLATE FILE EXTENSPC XXXXX      ;
;       AFFECTED MODULS:                      PRINTER, SIO      ;
;                                                               ;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
;
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;IONS
        JMP     RTRTSA          ;RETURN REQUEST TO SEND ASSERT MODE
        JMP     RTSCBR          ;RETURN BAUD RATE CLOCK SET VALUE
        JMP     LSTDRV          ;LIST CHAR ROUTINE
	JMP     SETIO		;SET I/O DEVICE BYTE
	JMP	SETCPU		;ADJUST TIM;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;                                                               ;
;                           BISYNC 80/3780                      ;
;                     USER CONFIGURATION MODULE                 ;
;                ING FOR CPU SPEED
        JMP     RTCNTM          ;RETURN CONSOLE TIMING VALUE
SUPPTR:	DW	STARTUP         ;START UP FILE NAME POINTERS
	JMP	FSTEXT		;
	JMP	EXTEXT		;
	JMP	INEXT		;
	JMP	OUTEXT		;
	JMP	INTEXT		;
	JMP	RTSEXT		;
	JMP	RSTEXT		;
	JMP	XM                                               ;
;		      VERSION 5.0  (1982)			;
;                                                               ;
;       THIS MODULE MUST BE CHANGED IF THE LINK'S INITIAL       ;
;       I/O PORT ADDRESSES OR RUN TIMETEXT		;
	JMP	RCVEXT		;
	JMP	DTREXT		;
	JMP	RECVXT		; RECEIVE FILE EXIT ROUTINE
;
;       THE FOLLOWING EQUATE STATEMENTS MAY BE CHANGED
;       TO RECONFIGURE THE LINK'S FACTORY SUPPLIED PARAMETERS FOR --
;
;               -       2780, 3780, 2770, 3741, OR CPU INITIAL STARTUP MODE
;               -       8251 USART, 8274 MPSC, OR SIO SERIAL PORT USE
;               -       CPU CLOCK SPEED
;               -       CONSOLE TERMINAL BAUD RATE
;               -       LIST DEVICE DRIVER ROUTINE
;     ;BEING USED.
;                               ;SUPPLIED ADDRESS OF 81H.
;
CPUSPD  EQU     04H		;CHANGE THIS STATEMENT TO REFLECT
;                               ;THE CPU CLOCK SPEED IN MEGA-HERTZ
;
CONSPD  EQU     9600            ;CHANGE THIS STATEM            -       RJE COMMAND IDENTIFIER
;               -       TRANSLATE TABLES
;               -       FILENAME EXTENSIONS
;               -       3780 BLANK COMPRESSION
;               -       SELF CLOCKING BAUD RATE
;
DEVICE  EQU     M3780    ENT TO REFLECT
;                               ;THE MICROCOMPUTER CONSOLE TERMINAL
;                               ;BAUD RATE.
;
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;									 ;
;	THE FOLLOWING IS THE ROUTINE       ;CHANGE THIS STATEMENT TO 'M2780'
;                               ;TO CHANGE THE INITIAL STARTUP
;                               ;DEVICE MODE TO 2780 MODE OR TO
;                               ;'MCPU' TO CHANGE THE INITIAL
;				;STARTUP DEVICE M USED TO WRITE DATA TO THE LIST      ;
;	DEVICE (PRINTER) .  IF THE CP/M BIOS ROUTINE IS MODIFIED TO NOT  ;
;	WAIT ON THE PRINTER, THEN THIS ROUTINE MAY BE LEFT AS A CP/M     ;
;       CALL.  IF THE CP/M BIOS ROUTINE IS NOT MODIFIED THEN CHANGE THIS ;
ODE TO CPU
;				;OR M2770 FOR 2770 MODE OR M3741
;				;FOR 3741 STARTUP MODE.
;                               ;                                  
;                               ;LEAVE THIS STATEMENT AS-IS TO HAVE
;                               ;THE ;       ROUTINE TO WRITE DATA TO THE PRINTER WITHOUT WAITING ON PRINTER  ;
;       READY, PER THE USER MANUAL. SEE APPENDIX E FOR MORE DETAIL.      ;
;									 ;
;       HERE STARTS THE PHILIPS P2000C SPECIFIC MODIFICATION             ;
;;;;;;;;;;;;;;INITIAL STARTUP MODE REMAIN
;                               ;3780 MODE.
;
IODEV   EQU     Z80SIO          ;CHANGE THIS STATEMENT TO 'Z80SIO'
;                               ;FOR USE WITH A Z-80 SIO I/O DEVICE.
;				;CHANGE THIS STATEMENT TO
;				;'IN;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
;
	.Z80
LSTDRV	EQU	$
	LD	HL,(NEXT1)
	JP	(HL)
;
PRTAB	EQU	0FFACH
USART3	EQU	14H
;****************************************************************
; PUT CHARACTER AND GENERATED CHARACT8274' IF AN INTEL
;				;8274 MPSC DEVICE IS USED
;				;
;				;LEAVE THIS STATEMENT AS-IS IF
;				;THE LINK IS RUNNING ON AN INTEL
;				;8251 I/O DEVICE.
;
USDATA  EQU     28H             ;CHANGE THIS STATEMENT TO REFLECT
;                          ERS INTO LOCAL BUFFER
; AND SET ENTRY POINTER TO CLEAR BUFFER ROUTINE
;****************************************************************
FILLBUF	EQU	$
	PUSH	HL
	PUSH	DE
	;
	;SET RETRY COUNTER TO INITIAL VALUE
	;
	LD	HL,(MAXTRY)
	LD	(ACTTRY),HL
	;     ;THE I/O DEVICE DATA PORT ADDRESS
;                               ;ON THE Z-80 SIO, 8274 MPSC, OR
;				;8251 USART BASED I/O BOARD
;                               ;BEING USED.
;                               ;SUPPLIED ADDRESS OF 80H.
;
USSTAT  E
	LD	A,E
	AND	7FH		;STRIP PARITY BIT FROM CHARACTER
	LD	C,A
	CALL	LSTTAB		;PRINTER TABLE CODE
	LD	HL,CLRBUF
	LD	(NEXT1),HL
	POP	DE
	POP	HL
	LD	C,E
	RET
;**************************************************************
; CLEAR BUFFER BY PRINTING CQU     29H             ;CHANGE THIS STATEMENT TO REFLECT
;                               ;THE I/O DEVICE STATUS PORT ADDRESS
;                               ;ON THE Z-80 SIO, 8274 MPSC, OR
;				;8251 USART BASED I/O BOARD
;                             HARACTERS ONE AT A TIME
; ENTRY POINTER IS ONLY RESET WHEN ALL CHARACTERS PRINTED
;**************************************************************
CLRBUF	EQU	$
	PUSH	HL
	PUSH	DE
	;
	; DECREASE RETRY COUNTER AND TEST FOR ZERO
	; PRINT ERROR MESSAGE WHEN ZERO
	;
	LD	HL,(ACTTRY)
	DEC	HL
	LD	(ACTTRY),HL
	LD	A,H
	OR	L
	JR	NZ,$2
	CALL	SNDERR		;SEND ERROR MESSAGE TO CONSOLE
$2:	CALL	LISTAT
	JR	Z,RETRY 
	LD	HL,(OUTPTR)
	PUSH	HL
	LD	A,(HL)
	LD	DE,(BUFPTR)
	SBC	HL,DE
	JR	NZ,$1
	;
	LD	HL,BUFFE BUFFER
	; THE BUFFER WILL BE EMPTIED BY CLRBUF CODE ON NEXT CALL BY BIS3270
	LD	HL,(BUFPTR)
	LD	(HL),C
	INC	HL
	LD	(BUFPTR),HL
	RET
;
;******************************************************************
; DATA ASSOCIATED WITH PRINTER ROUTINE
; NOR
	LD	(BUFPTR),HL
	LD	(OUTPTR),HL
	;
	LD	HL,FILLBUF
	LD	(NEXT1),HL	;RESET ENTRY POINTER SO THAT NEXT CHAR IS
	POP	HL
	POP	DE		;ACCEPTED INTO BUFFER FOR PRINTING
	POP	HL
	LD	C,0
	RET
	;
$1:	OUT	(USART3),A
	POP	HL
	INC	HL
	LD	(OUTPTR),HL
	;
TE LOCAL BUFFER OF 20H CHARACTERS USED BY PRINTER TABLE CODE
; THIS BUFFER IS USED FOR CHARACTER EXPANSION, THEREFORE A RESTRICTION
; IS THAT NO MORE THAN 32 CHARACTERS CAN BE GENERATED OUT OF THE
; PRINTER TABLE FOR EACH INPUT CHARACTER
;*************	;SET RETRY COUNTER BACK TO INITIAL VALUE AS A CHARACTER
	;HAS JUST BEEN PRINTED CORRECTLY
	;
	LD	HL,(MAXTRY)
	LD	(ACTTRY),HL
	;
RETRY:	POP	DE
	POP	HL
	LD	C,E
	RET
;
;***************************************************************
; ROUTINE TO *****************************************************
WORK1:	DB	0
WORK2:	DB	0
BUFFER: DS	20H
BUFPTR: DW	BUFFER
OUTPTR: DW	BUFFER
MAXTRY:	DW	32000
ACTTRY:	DW	0
ERRMSG:	DEFB	0DH,0AH,07,'*** ERROR ON PRINTER ** RETRY COUNT EXCEEDED'
	DEFB	0DH,0AH,'$'SEND PRINTER TIMEOUT ERROR MESSAGE TO CONSOLE
;
;***************************************************************
SNDERR:	PUSH	BC
	LD	C,09H	;DISPLAY STRING
	LD	DE,ERRMSG
	CALL	CPM
	POP	BC
	RET
;
;
;************************************************
;
;*******************************************************************
; ROUTINE TO READ PRINTER STATUS DIRECTLY FROM 8251 HARDWARE
;
;*******************************************************************
LISTAT: IN	A,(USART3+1)
	AND	85H
	SUB	85H
	***************
; PRINTER TABLE CODE, ESSENTIALLY A COPY OF THAT CODE IN ROM
; WHICH IS USED BY CPM, EXCEPT THAT THE ERROR HANDLING HAS BEEN
; REMOVED
;***************************************************************
LSTTAB: LD	HL,(PRTAB)
	LD	A,H
	ORJR	Z,RETFF
	SUB	A
	RET
RETFF:	OR	0FFH
	RET
;
NEXT1:	DW	FILLBUF
;
	.8080
;
;
;
;
;
;
;       THE FOLLOWING TABLE DEFINES THE HASP AND POWER CONSOLE
;       COMMAND IDENTIFIERS AND THE STRINGS TO BE SUBSTITUTED
;       FOR THE IDENTIFIER WHE	L
	JR	Z,PR1
	LD	A,1
	LD	(WORK2),A	;NUM OF REPL CHARS
PRT1:	LD	A,(HL)		;NUM OF LEVELS
	LD	E,A
	INC	HL
	INC	E
	LD	A,(WORK2)
	DEC	A
	LD	B,A
	JR	Z,PRT2
	LD	A,(HL)
	INC	HL
	LD	(WORK1),A
;
PRT2:	INC	B
	LD	A,B
	CP	E
	JR	C,PRT4
	LD	A,(WORK2)
N TRANSMITTING A CONSOLE COMMAND.
;       THE IDENTIFIERS AND/OR THE STRINGS MAY BE MODIFIED TO CAUSE
;       TRANSMISSION OF ANY STRING FOR ANY IDENTIFIER.
;
;       TABLE FORMAT :
;               1 BYTE IDENTIFIER LENGTH
;               N BYTES OF 	INC	A
	LD	(WORK2),A
	CP	3
	JR	NZ,PRT1
;
	LD	A,C
	CP	0A0H
	JR	C,PRTC
	LD	C,20H
;
PRTC:	PUSH	HL
	CALL	PR1
	POP	HL
	RET
;
PRT4:	LD	A,(HL)
	LD	D,A
	INC	HL
PRT5:	LD	A,D
	AND	A
	JR	Z,PRT2
	LD	A,(HL)
	DEC	D
	INC	HL
	CP	C
	JR	NZ,PRT8
PRTIDENTIFIER
;               2 BYTE ADDRESS OF SUBSTITUTE STRING
;
;               END OF TABLE DELIMITED BY A LENGTH BYTE
;               WITH A VALUE OF ZERO.
;
;       SUBSTITUTE STRING FORMAT:
;               1 BYTE STRING LENGTH
;               6:	LD	A,(HL)
	LD	C,A
	INC	HL
	CALL	PRTC
	DJNZ	PRT7
	AND	A
	RET
;
PRT7:	LD	A,(WORK2)
	CP	2
	LD	A,(WORK1)
	LD	C,A
	CALL	Z,PRTC
	JR	PRT6
;
PRT8:	LD	A,B
PRT9:	INC	HL
	DEC	D
	DEC	A
	JR	NZ,PRT9
	JR	PRT5
;
PR1:	; ADD A CHARACTER TO THE LOCALN BYTES OF STRING
;
;
;
;
CMDTAB  EQU     $
        DB      1               ;IDENTIFIER LENGTH (MAX 255)
        DB      '$'             ;IDENTIFIER
        DW      HASPCM          ;ADDRESS OF STRING TO SUBSTITUTE
;                               ;FOR IDENTIFIER
        DB      1               ;IDENTIFIER LENGTH
        DB      '*'             ;IDENTIFIER
        DW      POWRCM          ;ADDRESS OF STRING TO SUBSTITUTE
;                               ;FOR IDENTIFIER
;
        DB      0        H,0D6H  ;48H-4FH
        DB      0D7H,0D8H,0D9H,0E2H,0E3H,0E4H,0E5H,0E6H  ;50H-57H
        DB      0E7H,0E8H,0E9H,0ADH,0E0H,0BDH,05FH,06DH  ;58H-5FH
        DB      079H,081H,082H,083H,084H,085H,086H,087H  ;60H-67H
        DB      088H,089H,091H,092H,0       ;END OF TABLE - DO NOT REMOVE THIS
;                               ;STATEMENT
;
HASPCM: DB      3               ;SUBSTITUTE STRING LINGTH
        DB      '/*$'           ;SUBSTITUTE STRING
;
POWRCM: DB      5               ;SUBSTITUTE STRING L93H,094H,095H,096H  ;68H-6FH
        DB      097H,098H,099H,0A2H,0A3H,0A4H,0A5H,0A6H  ;70H-77H
        DB      0A7H,0A8H,0A9H,08BH,06AH,09BH,0A1H,007H  ;78H-7FH
        DB      000H,001H,002H,003H,037H,02DH,02EH,02FH  ;80H-87H
        DB      016H,005HENGTH
        DB      '* .. '         ;SUBSTITETE STRING
;
;				;CHANGE FOLLOWING TWO STATEMENTS
;				;TO REFLECT THE LENGTH OF
;				;STRING (DO NOT INCLUDE THE LENGTH
;				;BYTE ITSELF) DEFINING THE
;				;START UP FILE NAME, IF
;				;NONE IS WANTE,025H,00BH,00CH,00DH,00EH,00FH  ;88H-8FH
        DB      010H,011H,012H,013H,03CH,03DH,032H,026H  ;90H-97H
        DB      018H,019H,03FH,027H,01CH,01DH,01EH,01FH  ;98H-9FH
        DB      040H,05AH,07FH,07BH,05BH,06CH,050H,07DH  ;A0H-A7H
        DB   D USE ZERO
;				FOR STRING LENGTH.
;
STARTUP:DB	0		;STRING LENGTH INCLUDING TERMINATORS
ST1:	DB	'STARTUP.BIS'	;FILE NAME STRING
	DB	0DH,0AH		;SCAN TERMINATOR (DO NOT REMOVE)
ST2:
;
;
;
;       THE FOLLOWING TWO TABLES ARE THE ASCII TO EBCDIC
;     04DH,05DH,05CH,04EH,06BH,060H,04BH,061H  ;A8H-AFH
        DB      0F0H,0F1H,0F2H,0F3H,0F4H,0F5H,0F6H,0F7H  ;B0H-B7H
        DB      0F8H,0F9H,07AH,05EH,04CH,07EH,06EH,06FH  ;B8H-BFH
        DB      07CH,0C1H,0C2H,0C3H,0C4H,0C5H,0C6H,0C7H  ;C0H-C7H
      AND EBCDIC TO ASCII TRANSLATE TABLES USED BY THE
;       LINK IN CODE CONVERSION.  THESE TABLES MAY BE
;       MODIFIED TO ALLOW TRANSLATION OF ANY CHARACTER TO
;       ANY OTHER CHARACTER, SO LONG AS LINE CONTROL
;       CHARACTERS ARE NOT TRANSM       DB      0C8H,0C9H,0D1H,0D2H,0D3H,0D4H,0D5H,0D6H  ;C8H-CFH
        DB      0D7H,0D8H,0D9H,0E2H,0E3H,0E4H,0E5H,0E6H  ;D0H-D7H
        DB      0E7H,0E8H,0E9H,0ADH,0E0H,0BDH,05FH,06DH  ;D8H-DFH
        DB      079H,081H,082H,083H,084H,085H,086H,087H ITTED IN NON-TRANSPARENT
;       MODE.
;
;
ASCEBC  EQU     $               ;ASCII TO EBCDIC TRANSLATE TABLE
;
        DB      000H,001H,002H,003H,037H,02DH,02EH,02FH	 ;00H-07H
        DB      016H,005H,025H,00BH,00CH,00DH,00EH,00FH  ;08H-0FH
       ;E0H-E7H
        DB      088H,089H,091H,092H,093H,094H,095H,096H  ;E8H-EFH
        DB      097H,098H,099H,0A2H,0A3H,0A4H,0A5H,0A6H  ;F0H-F7H
        DB      0A7H,0A8H,0A9H,08BH,06AH,09BH,0A1H,007H  ;F8H-FFH
;
EBCASC  EQU     $               ;EBCDIC T  DB      010H,011H,012H,013H,03CH,03DH,032H,026H  ;10H-17H
        DB      018H,019H,03FH,027H,01CH,01DH,01EH,01FH  ;18H-1FH
        DB      040H,05AH,07FH,07BH,05BH,06CH,050H,07DH  ;20H-27H
        DB      04DH,05DH,05CH,04EH,06BH,060H,04BH,061H  ;28HO ASCII TRANSLATE TABLE
;
        DB      000H,001H,002H,003H,000H,009H,000H,07FH  ;00H-07H
        DB      000H,000H,000H,00BH,00CH,00DH,00EH,00FH  ;08H-0FH
        DB      010H,011H,012H,013H,000H,00AH,008H,000H  ;10H-17H
        DB      018H,019H,0-2FH
        DB      0F0H,0F1H,0F2H,0F3H,0F4H,0F5H,0F6H,0F7H  ;30H-37H
        DB      0F8H,0F9H,07AH,05EH,04CH,07EH,06EH,06FH  ;38H-3FH
        DB      07CH,0C1H,0C2H,0C3H,0C4H,0C5H,0C6H,0C7H  ;40H-47H
        DB      0C8H,0C9H,0D1H,0D2H,0D3H,0D4H,0D500H,000H,01CH,01DH,01EH,01FH  ;18H-1FH
        DB      000H,000H,01CH,000H,000H,00AH,017H,01BH  ;20H-27H
        DB      000H,000H,000H,000H,000H,005H,006H,007H  ;28H-2FH
        DB      000H,000H,016H,000H,000H,01EH,000H,004H  ;30H-37H
        DB      000H,000H,000H,000H,014H,015H,000H,01AH  ;38H-3FH
        DB      020H,000H,000H,000H,000H,000H,000H,000H  ;40H-47H
        DB      000H,000H,000H,02EH,03CH,028H,02BH,021H  ;48H-4FH
        DB      026H,000H,000H,000H,000H,000H,000H,000H  ;50H-57H
   
	DB	4		;ENTRY LENGTH
        DB      '.OBJ'          ;.OBJ FILES ARE NOT TRANSLATED
        DW      0               ;REQUIRED TABLE ENTRY
        DB      4               ;ENTRY LENGTH
        DB      '.LNK'          ;.LNK FILES ARE NOT TRANSLATED
        DB      000H,000H,021H,024H,02AH,029H,03BH,05EH  ;58H-5FH
        DB      02DH,02FH,000H,000H,000H,000H,000H,000H  ;60H-67H
        DB      000H,000H,07CH,02CH,025H,05FH,03EH,03FH  ;68H-6FH
        DB      000H,000H,000H,000H,000H,000H,000H,000H  ;     DW      0               ;REQUIRED
        DB      4               ;ENTRY LENGTH
        DB      '.LIB'          ;.LIB FILES ARE NOT TRANSLATED
        DW      0               ;REQUIRED
        DB      4               ;ENTRY LENGTH
        DB     70H-77H
        DB      000H,060H,03AH,023H,040H,027H,03DH,022H  ;78H-7FH
        DB      000H,061H,062H,063H,064H,065H,066H,067H  ;80H-87H
        DB      068H,069H,000H,07BH,000H,000H,000H,000H  ;88H-8FH
        DB      000H,06AH,06BH,06CH,06DH,06EH, '.REL'          ;.REL FILES ARE NOT TRANSLATED
        DW      0               ;REQUIRED
        DB      4               ;ENTRY LENGTH
        DB      'NULL'          ;NULL EXTENSION FILES ARE NOT
;                               ;TRANSLATED.  NOTE THA06FH,070H  ;90H-97H
        DB      071H,072H,000H,07DH,000H,000H,000H,000H  ;98H-9FH
        DB      000H,07EH,073H,074H,075H,076H,077H,078H  ;A0H-A7H
        DB      079H,07AH,000H,000H,000H,05BH,000H,000H  ;A8H-AFH
        DB      030H,031H,032H,033T THE STRING
;                               ;'NULL' MEANS NO EXTENSION.
        DW      0               ;REQUIRED
;
        DB      0               ;END OF TABLE - REQUIRED
;
COMPRS  EQU     TRUE            ;CHANGE THIS STATEMENT TO 'FALSE'
;      H,034H,035H,036H,037H  ;B0H-B7H
        DB      038H,039H,000H,000H,000H,05DH,000H,05FH  ;B8H-BFH
        DB      000H,041H,042H,043H,044H,045H,046H,047H  ;C0H-C7H
        DB      048H,049H,000H,000H,000H,028H,02BH,02BH  ;C8H-CFH
        DB      000H,0                         ;TO DISABLE BLANK COMPRESSION IN
;                               ;3780 MODE.
;

BAUDRT  EQU     4800            ;CHANGE THIS STATEMENT TO REFLECT THE
;                               ;BAUD RATE DESIRED WHEN RUNNING THE
;      4AH,04BH,04CH,04DH,04EH,04FH,050H  ;D0H-D7H
        DB      051H,052H,000H,07DH,000H,029H,000H,000H  ;D8H-DFH
        DB      05CH,000H,053H,054H,055H,056H,057H,058H  ;E0H-E7H
        DB      059H,05AH,000H,000H,000H,000H,000H,000H  ;E8H-EFH
        DB                         ;LINK IN SELF-CLOCKING (DIRECT CONNECTED)
;                               ;CONFIGURATIONS.  POSSIBLE VALUES ARE
;                               ;1200, 2400, 4800, AND 9600,
;                               ;CORRESPONDING TO 1200,      030H,031H,032H,033H,034H,035H,036H,037H  ;F0H-F7H
        DB      038H,039H,000H,000H,000H,000H,000H,000H  ;F8H-FFH
;
;
;       THE FOLLOWING TABLE DEFINES THE FILENAME EXTENSIONS FOR
;       FILES THAT ARE NOT TO BE TRANSLATED TO AND FROM EBCDI 2400, 4800, AND
;                               ;9600 BAUD RESPECTIVELY.  THIS PARAMETER
;                               ;NEED NOT BE CHANGED IF THE LINK IS
;                               ;RUNNING WITH A MODEM OR MODEM
;                              C.
;       THE TABLE HAS THE SAME FORMAT AS THE RJE CONSOLE IDENTIFIER
;       TABLE SHOWN ABOVE.  THE TABLE MUST HAVE AT LEAST ONE ENTRY.
;
;
FILXTB: DB      4               ;ENTRY LENGTH
	DB	'.COM'		;.COM FILES ARE NOT TRANSLATED
	DW	0		;REQUIRED ;ELIMINATOR.
;
;
;
;
;       THE FOLLOWING ROUTINES MUST NOT BE USER MODIFIED.
;
;
USDTIN: IN      USDATA          ;GET USART BYTE
        RET                     ;BACK TO CALLER
USDTOT: OUT     USDATA          ;WRITE USART BYTE
        RET                     ;BACK TO CALLER
USSTIN: IN      USSTAT          ;GET USART STATUS
        RET                     ;BACK TO CALLER
USSTOT: OUT     USSTAT          ;WRITE USART COMMAND
        RET                     ;BACK TO CALLER
TMCTOT  EQU     $
JNZ     SETVAL          ;NO - ADD AGAIN
        RET                     ;YES - RETURN
;
;
TIMVAL: DW      00B7H           ;TIME CONSTANT
FSTEXT:	RET
EXTEXT:	RET
INEXT:	RET
OUTEXT:	RET
INTEXT:	RET
RTSEXT:	RET
RSTEXT:	RET
XMTEXT:	RET
RCVEXT:	RET        RET                     ;BACK TO CALLER
TMDTIN  EQU     $
        RET                     ;BACK TO CALLER
TMDTOT  EQU     $
        RET                     ;BACK TO CALLER
RTMODE: MVI     A,DEVICE        ;GET DEVICE MODE
        RET          
DTREXT: RET
RFILE	EQU	00H		; RECEIVE DEVICE IS A DISK FILE
RCONSL	EQU	01H		; RECEIVE DEVICE IS THE CONSOLE
RLIST	EQU	02H		; RECEIVE DEVICE IS THE PRINTER
;
;
RECVXT	EQU	$
	RET
;
        END
           ;BACK TO CALLER
RTCMPR: MVI     A,COMPRS        ;GET COMPRESS MODE
        RET                     ;BACK TO CALLER
RTCMTB: LXI     H,CMDTAB        ;GET CONSOLE COMMAND TABLE ADDRESS
        RET                     ;BACK TO CALLER
RTXLAT: LXSS ANY KEY TO CONTINUE";
4210 Q$=INKEY$:R=RND
4220 IF Q$="" THEN 4210
4230 GOSUB 4800 ' CLEAR MESSAGE AREA
4240 PRINT FNPRI$(12,40);"4 TO 5 IS A HAIRPIN CURVE 100 YARDS LONG"
4250 PRINT FNPRI$(13,47);"BREAKAWAY SPEED RANGE: 20-35 MPH"
4260 PRINT FNPRI     H,ASCEBC        ;GET TRANSLATE TABLE ADDRESS
        RET                     ;BACK TO CALLER
RTFLEX: LXI     H,FILXTB        ;GET NOTRANSLATE FILE EXTENSION TABLE
        RET                     ;BACK TO CALLER
RTRTSA: MVI     A,FALSE         ;GEI$(14,40);"5 TO 6 IS A STRAIGHTAWAY 300 YARDS LONG"
4270 PRINT FNPRI$(15,47);"IT ENDS AT POSITION 1900 YARDS"
4280 PRINT FNPRI$(16,47);"FROM THE GRID"
4290 PRINT FNPRI$(17,40);"6 TO 7 IS A SET OF CURVES, 500 YARDS LONG"
4300 PRINT FNPRI$(18,47);"THE SPT RTS ASSERT MODE BYTE
        RET                     ;BACK TO CALLER
RTSCBR: LXI     H,BAUDRT        ;GET BAUD RATE TIMER VALUE
        RET                     ;BACK TO CALLER
;
DATA    EQU     USDATA
STAT    EQU     USSTAT
;
RTCNTM  EQU     $
 EED RANGE IS 90-110 MPH"
4310 PRINT FNPRI$(19,40);"7 TO 8 IS FINAL STRAIGHTAWAY OF 400 YARDS"
4320 PRINT FNPRI$(20,47);"ENTERING LAST CURVE AT 2800 YARDS"
4330 PRINT FNPRI$(21,40);"8 TO 1 IS THE FINAL CURVE OF 400 YARDS"
4340 PRINT FNPRI$(22,47);"BREAK