0       ON ERROR GOTO 65000
10 ' LPRINT CHR$(27)"3" CHR$(24);:REM (LiSp)
15  '    LPRINT CHR$(27);"2";
20 ' '   LPRINT CHR$(27)":" CHR$(0) CHR$(0)         CHR$(0);
30'      LPRINT CHR$(27)"%" CHR$(1) CHR$(0);
40 '     LPRINT CHR$(27)"&" CHR$(0)       
208     DATA 7,7
209     DATA 231,7
210     DATA 7,231
211     DATA 231,231
212     DATA 31,7
213     DATA 255,7
214     DATA 31,231
215     DATA 255,231
216     DATA 7,31
217     DATA 231,31
218     DATA 7,255
219     DATA 231,255
220     DAT         CHR$(160) CHR$(223);
45 REM  PRINT CHR$(4) CHR$(3) CHR$(1)              CHR$(131)"Laden Grafics" SPC(26):
        PRINT CHR$(131)"ASCII code :" CHR$(2);
50      FOR Z=160 TO 223:                           PRINT CHR$(4) CHR$(4) CHR$(14)Z:  
   A 31,31
221     DATA 255,31
222     DATA 31,255
223     DATA 255,255                                                             
65000   IF ERR=64                                THEN    END                     
        ELSE    IF ERR=80                    LPRINT CHR$(139);:                       READ I:                         
         LPRINT CHR$(I) CHR$(0) CHR$(I)             CHR$(0) CHR$(I) CHR$(0);:        
         READ I:                                  LPRINT CHR$(I) CHR$(0) CHR$(I)    
                    THEN    RESUME1         
                ELSE    ON ERR OR GOTO 0:                           END
65432   'P2000gg
65433   'Vieuw DATA graFiX
65434   'Joep Willemsen
       CHR$(0) CHR$(I);:                       NEXT
60      LPRINT CHR$(27)"j" CHR$(20)
65 REM     POKE&H60A2,3
70      PRINT CHR$(4) CHR$(3) CHR$(1)              CHR$(131)                       
        "GraFiX geladen van 160-223":           PRINT CH           ELSE    ON ERR OR GOTO 0:                           END
65432   'P2000gg
65433   'Vieuw DATA graFiX
65434   'Joep Willemsen
R$(131)"Printer type 3  "
        :END
160     DATA 0,0
161     DATA 224,0
162     DATA 0,224
163     DATA 224,224
164     DATA 24,0
165     DATA 248,0
166     DATA 24,224
167     DATA 248,224
168     DATA 0,24
169     DATA 224,24
170     DATA ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее0,248
171     DATA 224,248
172     DATA 24,24
173     DATA 248,24
174     DATA 24,248
175     DATA 248,248
176     DATA 7,0
177     DATA 231,0
178     DATA 7,224
179     DATA 231,224
180     DATA 31,0
181     DATA 255,0
182     DATA 31,224
183