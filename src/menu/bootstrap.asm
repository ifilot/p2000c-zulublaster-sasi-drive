; Tiny first-stage launcher for P2000C Navigator.
;
; CP/M must read a complete COM file before executing it. Keeping MENU.COM
; only two records makes this message appear almost immediately; the relocated loader
; then replaces it with the optimized MENU.BIN second stage.
        org 0100h

start:
        ld de,loading_message
        ld c,9
        call 5

        ; Relocate the destructive loader into the CCP workspace. MENU.BIN can
        ; then overwrite the complete transient program area from 0100h.
        ld hl,(6)
        ld de,-512
        add hl,de
        push hl
        ex de,hl
        ld hl,loader
        ld bc,loader_end-loader
        ldir

        pop hl
        push hl
        ld de,256
        add hl,de
        ex de,hl
        ld hl,menu_fcb
        ld bc,36
        ldir
        pop hl
        jp (hl)

loading_message:
        db 12,'Inladen menu...',13,10,'$'

menu_fcb:
        db 1,'MENU    ','BIN'
        defs 24

; Position independent after relocation: local control flow is relative and
; all other references are CP/M fixed addresses.
loader:
        push hl
        ld de,256
        add hl,de
        ex de,hl
        ld c,15
        call 5
        pop ix
        inc a
        jr z,load_error

        ld hl,0100h
load_next:
        push hl
        ex de,hl
        ld c,26
        call 5
        pop hl

        push hl
        push ix
        pop hl
        ld de,256
        add hl,de
        ex de,hl
        ld c,20
        call 5
        pop hl
        or a
        jr z,record_loaded
        dec a
        jr z,loaded
        jr load_error
record_loaded:
        ld de,128
        add hl,de
        jr load_next

loaded:
        ld de,0080h
        ld c,26
        call 5
        ld sp,(6)
        ld hl,0
        push hl
        ld a,(4)
        and 15
        ld c,a
        xor a
        jp 0100h

load_error:
        ld c,2
        ld e,'!'
        call 5
        jp 0
loader_end:
