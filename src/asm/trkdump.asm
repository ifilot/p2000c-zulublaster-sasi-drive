; TRKDUMP B[:]|C[:] -- capture P2000C 640K floppy boot tracks to A:COBOARD.TRK.
; z80asm syntax, CP/M 2.2. Run under the reference SASI A:/floppy B:/C: system.
; All source I/O uses BIOS READ; there is no BIOS WRITE call in this program.
; Capture both reserved 4K tracks before making any output file. BIOS sector
; numbers are visited in ascending order, bypassing the filesystem skew.
; Write a temporary file, close, reopen, compare all bytes, then rename.

        org 0100h
buffer: equ 4000h
verify_buffer: equ 6000h

start:
        ld (entry_sp),sp
        ld de,banner
        call print
        ; Parse before BDOS directory searches overwrite the command tail.
        ld a,(0080h)
        or a
        jp z,usage
        ld b,a
        ld hl,0081h
skip_space:
        ld a,(hl)
        cp ' '
        jp nz,parse_drive
        inc hl
        djnz skip_space
        jp usage
parse_drive:
        and 0dfh
        cp 'B'
        jp z,source_ok
        cp 'C'
        jp nz,usage
source_ok:
        sub 'A'
        ld (source_drive),a
        inc hl
        dec b
        jp z,parsed
        ld a,(hl)
        cp ':'
        jp nz,trailing
        inc hl
        dec b
        jp z,parsed
trailing:
        ld a,(hl)
        cp ' '
        jp nz,usage
        inc hl
        djnz trailing
parsed:
        ld c,25
        call 5
        ld (original_drive),a
        ld c,32
        ld e,255
        call 5
        or a
        jp nz,user_error
        ld hl,(0006h)
        ld de,6200h
        or a
        sbc hl,de
        jp c,memory_error
        ; BIOS table offsets are relative to WBOOT at the address in 0001h.
        ld hl,(0001h)
        ld de,24
        add hl,de
        ld (bios_select+1),hl
        ld de,3
        add hl,de
        ld (bios_track+1),hl
        add hl,de
        ld (bios_sector+1),hl
        add hl,de
        ld (bios_dma+1),hl
        add hl,de
        ld (bios_read+1),hl
        ld de,9
        add hl,de
        ld (bios_translate+1),hl
        ; A: must be the split SASI boot partition, not a booted floppy.
        ld c,14
        ld e,0
        call 5
        ld c,31
        call 5
        ld de,hard_dpb
        call compare_dpb
        jp nz,hard_error
        ld de,final_fcb
        call exists
        jp nz,exists_error
        ld de,file_fcb
        call exists
        jp nz,temp_exists_error
        ld de,reading
        call print
        ld a,(source_drive)
        ld c,a
        ld e,0
        call bios_select
        ld a,h
        or l
        jp z,select_error
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (translation),de
        ld de,9
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ld de,floppy_dpb
        call compare_dpb
        jp nz,geometry_error
        ; SECTRAN must describe a permutation of either 0..31 or 1..32.
        ; This check rejects sector encodings we cannot interpret as raw order.
        ld hl,visited
        ld b,33
        xor a
clear_visited:
        ld (hl),a
        inc hl
        djnz clear_visited
        ld (logical_sector),a
translation_loop:
        ld a,(logical_sector)
        ld c,a
        ld b,0
        ld de,(translation)
        call bios_translate
        ld a,h
        or a
        jp nz,translation_error
        ld a,l
        cp 33
        jp nc,translation_error
        ld de,visited
        add hl,de
        ld a,(hl)
        or a
        jp nz,translation_error
        inc (hl)
        ld a,(logical_sector)
        inc a
        ld (logical_sector),a
        cp 32
        jp nz,translation_loop
        ld a,(visited)
        xor 1
        ld (first_sector),a
        ; With 32 distinct values in 0..32, a valid range omits one endpoint.
        ld b,a
        ld a,(visited+32)
        cp b
        jp nz,translation_error
        xor a
        ld (track_number),a
        ld (logical_sector),a
        ld hl,buffer
        ld (buffer_pointer),hl
read_loop:
        ld a,(track_number)
        ld c,a
        ld b,0
        call bios_track
        ld a,(first_sector)
        ld b,a
        ld a,(logical_sector)
        add a,b
        ld c,a
        ld b,0
        call bios_sector
        ld bc,(buffer_pointer)
        call bios_dma
        call bios_read
        or a
        jp nz,read_error
        ld hl,(buffer_pointer)
        ld de,128
        add hl,de
        ld (buffer_pointer),hl
        ld a,(logical_sector)
        inc a
        cp 32
        jp z,next_track
        ld (logical_sector),a
        jp read_loop
next_track:
        xor a
        ld (logical_sector),a
        ld a,(track_number)
        inc a
        ld (track_number),a
        cp 2
        jp nz,read_loop
        call restore_a
        ld de,writing
        call print
        call reset_file
        ld de,file_fcb
        ld c,22
        call 5
        cp 255
        jp z,create_error
        ld hl,buffer
        ld (buffer_pointer),hl
        ld a,64
        ld (records_left),a
write_loop:
        ld de,(buffer_pointer)
        ld c,26
        call 5
        ld de,file_fcb
        ld c,21
        call 5
        or a
        jp nz,write_error
        call advance_record
        jp nz,write_loop
        ld de,file_fcb
        ld c,16
        call 5
        cp 255
        jp z,write_error
        ld de,verifying
        call print
        call reset_file
        ld de,file_fcb
        ld c,15
        call 5
        cp 255
        jp z,verify_error
        ld hl,buffer
        ld (buffer_pointer),hl
        ld a,64
        ld (records_left),a
verify_loop:
        ld de,verify_buffer
        ld c,26
        call 5
        ld de,file_fcb
        ld c,20
        call 5
        or a
        jp nz,verify_error
        ld hl,(buffer_pointer)
        ld de,verify_buffer
        ld b,128
compare_record:
        ld a,(de)
        cp (hl)
        jp nz,verify_error
        inc hl
        inc de
        djnz compare_record
        call advance_record
        jp nz,verify_loop
        ld de,file_fcb
        ld c,20
        call 5
        cp 1
        jp nz,verify_error
        ld de,file_fcb
        ld c,16
        call 5
        cp 255
        jp z,verify_error
        ; Rename only the verified temporary file. Neither name is overwritten.
        ld de,final_fcb
        call exists
        jp nz,rename_error
        ld de,rename_fcb
        ld c,23
        call 5
        cp 255
        jp z,rename_error
        ld de,success
        call print
        jp finish

compare_dpb:
        ld b,15
compare_dpb_byte:
        ld a,(de)
        cp (hl)
        ret nz
        inc de
        inc hl
        djnz compare_dpb_byte
        ret
exists:
        ld c,17
        call 5
        cp 255
        ret
reset_file:
        ld hl,file_fcb+12
        ld b,24
        xor a
reset_byte:
        ld (hl),a
        inc hl
        djnz reset_byte
        ret
advance_record:
        ld hl,(buffer_pointer)
        ld de,128
        add hl,de
        ld (buffer_pointer),hl
        ld a,(records_left)
        dec a
        ld (records_left),a
        ret
restore_a:
        ld c,0
        ld e,1
        call bios_select
        ld bc,0080h
        call bios_dma
        ld de,0080h
        ld c,26
        call 5
        ret
finish:
        ld de,0080h
        ld c,26
        call 5
        ld a,(original_drive)
        ld e,a
        ld c,14
        call 5
exit:
        ld sp,(entry_sp)
        ret
usage:
        ld de,usage_text
        call print
        jp exit
user_error:
        ld de,user_text
        call print
        jp exit
memory_error:
        ld de,memory_text
        call print
        jp exit
hard_error:
        ld de,hard_text
        jp plain_error
exists_error:
        ld de,exists_text
        jp plain_error
temp_exists_error:
        ld de,temp_exists_text
        jp plain_error
select_error:
        ld de,select_text
        jp source_error
geometry_error:
        ld de,geometry_text
        jp source_error
translation_error:
        ld de,translation_text
        jp source_error
read_error:
        call restore_a
        ld de,read_text
        call print
        ld a,(track_number)
        call hex_byte
        ld de,sector_text
        call print
        ld a,(logical_sector)
        ld b,a
        ld a,(first_sector)
        add a,b
        call hex_byte
        ld de,no_output_text
        jp plain_error
source_error:
        push de
        call restore_a
        pop de
        jp plain_error
create_error:
        ld de,create_text
        jp plain_error
write_error:
        ld de,write_text
        jp cleanup_error
verify_error:
        ld de,verify_text
cleanup_error:
        push de
        ld de,file_fcb
        ld c,16
        call 5
        call reset_file
        ld de,file_fcb
        ld c,19
        call 5
        pop de
        jp plain_error
rename_error:
        ld de,rename_text
plain_error:
        call print
        jp finish
hex_byte:
        push af
        rrca
        rrca
        rrca
        rrca
        call hex_digit
        pop af
hex_digit:
        and 15
        add a,'0'
        cp ':'
        jp c,hex_print
        add a,7
hex_print:
        ld e,a
        ld c,2
        call 5
        ret
print:
        ld c,9
        call 5
        ret
bios_select:
        jp 0
bios_track:
        jp 0
bios_sector:
        jp 0
bios_dma:
        jp 0
bios_read:
        jp 0
bios_translate:
        jp 0
hard_dpb:
        dw 32
        db 5,31,1
        dw 1221,255
        db 0c0h,0
        dw 0,2
floppy_dpb:
        dw 32
        db 5,31,3
        dw 157,127
        db 080h,0
        dw 32,2
final_fcb:
        db 1,'COBOARD ','TRK'
        defs 24,0
file_fcb:
        db 1,'COBOARD ','TMP'
        defs 24,0
rename_fcb:
        db 1,'COBOARD ','TMP'
        defs 4,0
        db 1,'COBOARD ','TRK'
        defs 4,0
entry_sp:
        dw 0
original_drive:
        db 0
source_drive:
        db 0
translation:
        dw 0
first_sector:
        db 0
logical_sector:
        db 0
track_number:
        db 0
buffer_pointer:
        dw 0
records_left:
        db 0
visited:
        defs 33,0
banner:
        db 13,10,'TRKDUMP - P2000C floppy system-track capture',13,10,'$'
usage_text:
        db 'Usage: TRKDUMP B:  (floppy 1) or TRKDUMP C:  (floppy 2)',13,10
        db 'Boot from SASI. Output: A:COBOARD.TRK. Existing files are kept.',13,10,'$'
user_text:
        db 'Run USER 0 before TRKDUMP.',13,10,'$'
memory_text:
        db 'Not enough transient memory for the 8K capture buffer.',13,10,'$'
hard_text:
        db 'A: is not the expected split SASI boot drive. Boot from SASI first.',13,10,'$'
exists_text:
        db 'A:COBOARD.TRK already exists. Rename or copy it before another capture.',13,10,'$'
temp_exists_text:
        db 'A:COBOARD.TMP already exists. Preserve or remove it before retrying.',13,10,'$'
reading:
        db 'Reading floppy system tracks into memory...',13,10,'$'
select_text:
        db 'Cannot select source floppy. No output created.',13,10,'$'
geometry_text:
        db 'Unsupported floppy BIOS geometry (expected Philips 640K). No output created.',13,10,'$'
translation_text:
        db 'Unsupported BIOS sector translation. No output created.',13,10,'$'
read_text:
        db 'Floppy read failed at track (hex) $'
sector_text:
        db ', BIOS sector (hex) $'
no_output_text:
        db '. No output created.',13,10,'$'
writing:
        db 'Writing A:COBOARD.TMP...',13,10,'$'
verifying:
        db 'Reading back and comparing all 8192 bytes...',13,10,'$'
create_text:
        db 'Cannot create A:COBOARD.TMP. Check free directory space.',13,10,'$'
write_text:
        db 'Write/close failed. Capture not published; temporary cleanup attempted.',13,10,'$'
verify_text:
        db 'Read-back verification failed. Capture not published; cleanup attempted.',13,10,'$'
rename_text:
        db 'Rename failed. Verified capture remains in A:COBOARD.TMP.',13,10,'$'
success:
        db 'SUCCESS: A:COBOARD.TRK contains 8192 verified bytes.',13,10
        db 'Bring the SD card hard-drive image back for extraction.',13,10,'$'
