; Small hardware/transfer boundary; the menu, parser and launch preparation are C.
SECTION code_user
PUBLIC _idle_tick, _chain_program
EXTERN _launch_fcb, _launch_records

_idle_tick:
    ld bc,1538
idle_loop:
    dec bc
    ld a,b
    or c
    jr nz,idle_loop
    ret

_chain_program:
    ; Scratch lies in the discarded CCP, 512 bytes below BDOS. The current
    ; C stack is above it; no return to C is possible after the first read.
    ld hl,(6)
    ld de,-512
    add hl,de
    push hl
    ex de,hl
    ld hl,loader
    ld bc,loader_end-loader
    ldir
    ; FCB at scratch+128, clear of the relocated code and top-of-TPA stack.
    pop hl
    push hl
    ld de,128
    add hl,de
    push hl
    ex de,hl
    ld hl,_launch_fcb
    ld bc,36
    ldir
    pop bc
    pop ix
    ld hl,(_launch_records)
    ld de,0100h
    ld sp,(6)
    jp (ix)

; Position independent: only relative local jumps, BDOS and fixed entry points.
loader:
    push hl
    push de
    push bc
    ld c,26
    call 5
    pop de
    push de
    ld c,20
    call 5
    pop bc
    pop de
    pop hl
    or a
    jr nz,load_error
    dec hl
    ld a,h
    or l
    jr z,loaded
    push hl
    ld hl,128
    add hl,de
    ex de,hl
    pop hl
    jr loader
loaded:
    ld c,26
    ld de,0080h
    call 5
    ld hl,0
    push hl
    ; CP/M's usual entry A contains the validity flags for the default FCBs.
    ld a,(4)
    and 15
    ld c,a
    xor a
    jp 0100h
load_error:
    ; A partial program must never execute. Warm boot reloads the CCP.
    ld c,2
    ld e,'!'
    call 5
    jp 0
loader_end:
ASSERT loader_end-loader <= 128
