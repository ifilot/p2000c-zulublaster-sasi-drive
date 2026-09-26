; Directory guide for applications installed in D: user areas.
; Assemble with z80asm and run as D:README from user area zero.
        org 0100h
        ld de,message
        ld c,9
        call 5
        ret

message:
        db 12,'D: APPLICATIONS BY CP/M USER AREA',13,10,13,10
        db '  USER 0  README, P2EDIT and P2FILE',13,10
        db '  USER 1  Microsoft BASIC-80        start: MBASIC',13,10
        db '  USER 2  Microsoft COBOL           start: COBOL',13,10
        db '  USER 3  SuperCalc 2               start: SC2',13,10
        db 13,10
        db 'Example:',13,10
        db '  D:',13,10
        db '  USER 3',13,10
        db '  DIR',13,10
        db '  SC2',13,10,13,10
        db 'SC2: runtime and help only; no sample worksheets.',13,10
        db 'Type USER 0 to return to the default area.',13,10
        db 'Run D:README there to show this guide again.',13,10,'$'
