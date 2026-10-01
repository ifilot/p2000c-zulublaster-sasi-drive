; SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
; SPDX-License-Identifier: GPL-3.0-or-later

; Small disk-backed CP/M guide. Text pages remain in CPMHELP.TXT so extending
; the guide does not increase the transient program's executable size.
        org 0100h

start:
        ld de,file_fcb
        ld c,15
        call 5
        inc a
        jr z,open_failed

        ld a,128
        ld (dma_index),a

page_loop:
        call clear_screen
        call show_page
        push af
        call position_prompt
        pop af
        or a
        jr nz,last_page

        ld de,next_prompt
        ld c,9
        call 5
next_key:
        call read_key
        cp 'q'
        jr z,exit_to_menu
        cp 'Q'
        jr z,exit_to_menu
        cp 13
        jr z,page_loop
        cp ' '
        jr z,page_loop
        jr next_key

last_page:
        ld de,last_prompt
        ld c,9
        call 5
        call read_key

exit_to_menu:
        jp 0

open_failed:
        call clear_screen
        ld de,error_message
        ld c,9
        call 5
        call read_key
        ret

; Display bytes until a form feed starts the next page or the file ends.
; Returns A=0 when another page follows, A=1 at the end of the document.
show_page:
        call read_byte
        jr c,page_finished
        cp 12
        jr z,page_continues
        call put_character
        jr show_page

page_continues:
        xor a
        ret

page_finished:
        ld a,1
        ret

; Read one byte through CP/M sequential records. Carry means EOF or Ctrl-Z.
read_byte:
        ld a,(dma_index)
        cp 128
        jr c,read_cached
        ld de,file_fcb
        ld c,20
        call 5
        or a
        jr nz,read_finished
        xor a
        ld (dma_index),a

read_cached:
        ld a,(dma_index)
        ld e,a
        inc a
        ld (dma_index),a
        ld d,0
        ld hl,dma_buffer
        add hl,de
        ld a,(hl)
        cp 26
        jr z,read_finished
        or a
        ret

read_finished:
        scf
        ret

put_character:
        ld e,a
        ld c,2
        jp 5

clear_screen:
        ld a,12
        call put_character
        ret

; Place navigation on the second-last row of the 80x24 display.
position_prompt:
        ld a,27
        call put_character
        ld a,'Y'
        call put_character
        ld a,54
        call put_character
        ld a,34
        call put_character
        ret

read_key:
        ld c,6
        ld e,255
        call 5
        or a
        jr z,read_key
        ret

next_prompt:
        db 'ENTER/SPATIE volgende pagina   Q terug naar Navigator$'
last_prompt:
        db 'Einde van de uitleg - druk op een toets voor Navigator$'
error_message:
        db 12,'Kan D:CPMHELP.TXT niet openen.',13,10
        db 'Druk op een toets om terug te keren.$'

file_fcb:
        db 4,'CPMHELP ','TXT'
        defs 24,0
dma_index:
        db 128
; Reuse CP/M's standard DMA buffer so no disk state remains to restore.
dma_buffer: equ 0080h
