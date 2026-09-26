start    org       100h           ;start adres programma
BDOS     equ       05h            ;start adres BDOS
DC4      equ       14h            ;ascii char. 'DC4'
DC2      equ       12h            ;ascii char. 'DC2'
ESC      equ       1bh            ;as        ;ja , dan naar 'ppmode'
         cpi       'E'            ;input = 'E' ?
         jnz       lspace         ;nee , dan naar 'lspace'
ppmode   mvi       e,ESC
         call      prchar         ;'ESC' naar printer
         mvi       e,69
       cii char. 'ESC'
SO       equ       0eh            ;ascii char. 'SO'
SI       equ       0fh            ;ascii char. 'SI'
CR       equ       0dh            ;ascii char. 'CR'
LF       equ       0ah            ;ascii char. 'LF'
preset   mvi       e,DC4     call      prchar         ;char "E" naar printer
lspace   call      crlf
         lxi       d,msg4
         call      prstr          ;display msg4 op scherm
         call      rechar         ;read char van keyboardŠ         cpi       '8'            ;       ;printer op default waarden  
         call      prchar
         mvi       e,DC2
         call      prchar
         mvi       e,ESC 
         call      prchar
         mvi       e,50           ;=2
         call      prchar
         mvi      input = '8' ?
         jnz       endp           ;nee , dan naar 'endp'
         mvi       e,ESC
         call      prchar         ;'ESC' naar printer
         mvi       e,48
         call      prchar         ;char "0" naar printer
endp     call       e,ESC              
         call      prchar
         mvi       e,70           ;=F
         call      prchar
header   lxi       d,msg1          
         call      prstr          ;display msg1 op scherm
         call      crlf
         lxi       dcrlf
         lxi       d,msg5
         call      prstr          ;display msg5 op scherm
         ret                      ;terug naar CP/M
crlf     mvi       c,02h          ;CR + LF naar scherm
         mvi       e,CR                
         call  ,msg2                            
         call      prstr          ;display msg2 op scherm
         call      rechar         ;read char van keyboard
condens  cpi       'c'            ;input = 'c' ?
         jz        cprint         ;ja , dan naar 'cpr    BDOS
         mvi       c,02h
         mvi       e,LF                 
         call      BDOS
         ret
prchar   mvi       c,05h          ;BDOS functie print char.
         call      BDOS
         ret
prstr    mvi       c,09h          ;BDOSint'
         cpi       'C'            ;input = 'C' ?
         jnz       wide           ;nee , dan naar 'wide'
cprint   mvi       e,SI
         call      prchar         ;'SI' naar printer
wide     cpi       'w'            ;input = 'w' ?
         jz   functie print string
         call      BDOS
         ret
rechar   mvi       c,01h          ;BDOS functie read character
         call      BDOS
         ret
msg1     db        '--> PRINIT  [1.1] <--$'
msg2     db        'PRINIT> character type: C(      wprint         ;ja , dan naar 'wprint'
         cpi       'W'            ;input = 'W' ?
         jnz       pmode          ;nee , dan naar 'pmode'       
wprint   mvi       e,SO
         call      prchar         ;'SI' naar printer
pmode    call  ondensed, N(ormal ,W(ide $'
msg3     db        'PRINIT> print mode    : N(ormal , E(mphasized  $'
msg4     db        'PRINIT> line spacing  : 6(lpi, 8(lpi  $'
msg5     db        '--> PRINIT   END  <--$'
einde    end       100h
    crlf
         lxi       d,msg3                         
         call      prstr          ;display msg3 op scherm
         call      rechar         ;read char van keyboard
         cpi       'e'            ;input = 'e' ?
         jz        ppmode 