PROGRAM QSORT; (*R-*)

(* This program demonstrates the quicksort algorithm, which	*)
(* provides an extremely effecient method of sorting arrays in	*)
(* memory. The program generates a list of 1000 random numbers	*)
(* between 0 and 29999, and then ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееsorts them using the QUICKSORT	*)
(* procedure. Finally, the sorted list is output on the screen.	*)
(* Note that stack and range checks are turned off (through the	*)
(* compiler directive above) to optimize execution speed.	*)

CONST
  MAX = 1000;ееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееее

TYPE
  INDEX = 1..MAX;
  ITEM = INTEGER;
  LIST = ARRAY[INDEX] OF ITEM;

VAR
  DATA: LIST;
  I: INTEGER;

(* QUICKSORT sorts elements in the array A with indices between	*)
(* LO and HI (both inclusive). Note that the QUICKSORT proce-	*)
(* dееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееееure provides only an "interface" to the program. The actual	*)
(* processing takes place in the SORT procedure, which executes	