program disp;
var 	kar:char;
	i,j : integer;
begin
	repeat
		write	('enter a key ');
		read	(kbd,kar);
		writeln	(' : kar=',kar,' = ',ord(kar));
	until kar = 'X';
end.
