PROGRAM TEST;
VAR I:INTEGER;
BEGIN
FOR I:=$F080 TO $F7FF DO I^:=CHR(0);
END.
