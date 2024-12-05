// Gramàtica per expressions senzilles
grammar hm;

root : type_decl* expr?             // l'etiqueta ja és root
     ;

type_decl : (NAT|SYM|VAR) '::' typ  ;

typ  : TYPE '->' typ           #typeApl
     | TYPE                   #typePlain
     ;

expr : '(' expr ')'           #parentesis
     | expr expr              #aplicacio
     | '\\' VAR '->' expr     #abstraccio
     | NAT                    #nat
     | VAR                    #var
     | SYM                    #sym
     ;

TYPE : [A-Z]+ ;
VAR : [a-z] ;
NAT : [0-9]+ ;
SYM : '(' [+\-*/] ')' ;
WS  : [ \t\n\r]+ -> skip ;