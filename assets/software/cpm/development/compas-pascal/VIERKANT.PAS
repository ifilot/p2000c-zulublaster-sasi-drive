PROGRAM vierkant (input,output);
 VAR i, zijde :integer;
 
PROCEDURE lijn (z:integer);
 VAR i :integer;
 BEGIN
  for i:=1 to z do write(@208,@208);
  writeln
END; {lijn}
 
PROCEDURE middenstuk(z:integer);
 VAR i :integer;
  
PROCEDURE regel(z:ווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווווinteger);
VAR i :integer;
 BEGIN
  write (@250);
  for i :=1 to z*2-2 do write (' ');
  writeln(@250)
 END;{regel}

BEGIN
  for I:=1 to z-2 do regel(z)
END; {middenstuk}

BEGIN {Hoofdprogramma}
 writeln ('Tekenen van een vierkant ');
 writeln