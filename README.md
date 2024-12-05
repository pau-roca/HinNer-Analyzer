# Analitzador HinNer

## Requisits
El projecte fa servir certes llibreries que haurien d'estar instal·lades abans d'executar-lo.
- streamlit
- graphviz
- pandas

El projecte inclou els fitxers hm.py i hm.g4. Per generar la resta de fitxers feu servir la següent comanda:
- antlr4 -Dlanguage=Python3 -no-listener -visitor hm.g4
Un cop tenim tots els fitxers, podem executar l'aplicació streamlit amb aquesta altra comanda:
- streamlit run hm.py

En cas que l'operand als tipus algebraics | no funcioni, hi ha una manera alterantiva de declarar els tipus just a sobre, comentants i amb un header #CASA. Aquesta alternativa requereix l'import 'from typing import Union' que també està comentat a dalt de tot.

## Format de l'entrada
Hi ha un camp de text gran on s'introduiran primer les declaracions de tipus i després l'expressió que s'ha d'avaluar.
Els tipus els podem escriure cada un en una línia nova amb el format següent:
- element :: tipus
Per exemple, per declarar que el nombre 2 és un natural, farem servir:
- 2 :: N
I per dir que (+) pren dos naturals i en retorna un altre, farem servir:
- (+) :: N -> N -> N
Els tipus no poden incloure parèntesis, les constants als tipus han de començar amb majúscula.

L'expressió s'ha d'introduir a la línia després dels tipus, en notació prefixa en l'estil següent:
- \x -> \y -> (+) x y

## Estructura del codi
El codi té dos tipus algebraics.
El primer és el Type que té la forma:
- Type = Constant | Variable | Application
On Constant i Variable són classes amb un únic atribut string i Application és una classe amb dos atributs, esq i dre, Type.

Després tenim l'arbre de la forma:
- Arbre = Node | Buit
On Buit és una classe que només té un pass i Node és una classe amb un atribut str, un atribut Type, i dos atributs, esq i dre, Arbre.

Després tenim unes quantes classes:
- TreeVisitor: visita l'arbre de la gramatica per crear un arbre del tipus algebraic, a més a més crea la taula de simbols.
- AST_Labler: visita l'arbre the tipus algebraic i assigna els tipus i, si no en tenen, els n'assigna un nou del tipus t0, t1...
- AST_Infering: visita un arbre amb etiquetes ja posades i n'infereix els tipus dels nodes.
- python2graphviz: converteix un arbre de python en un arbre de la classe graphviz per imprimir per pantalla amb streamlit.

Despres hi ha un parell de funcions per qualitat de vida i el codi principal, que fa instanciant objectes de les classes anteriors per fer-ne servir les seves funcions i imprimir tot el que es demana.