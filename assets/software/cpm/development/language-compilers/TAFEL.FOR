C	FORTRAN VOORBEELDPROGRAMMA
C	TAFELS VAN 1 T/M 9
C
	DIMENSION IRES(10)
C	RUIMTE RESEVERING VOOR EEN
C	LIJST VAN 10 GETALLEN
	WRITE (5,100)
100	FORMAT(' ***** TAFELS *****')
C
C	VORMT HOOFDPROGRAMMALUS
	DO 10  I=1,10
C
	DO 20  J=1,10
	IRES(J)=ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееI*J
C	VULT DE LIJST MET DE TAFEL VAN 1
C
20	CONTINUE
	WRITE (5,101) (IRES(J),J=1,10)
C	TOONT EEN TAFEL OP DE TERMINAL
C
1