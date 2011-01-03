.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

||| : after : base.administracion_del_sistema |||

Búsqueda de texto
=================

Si utiliza el cliente Koo, podrá buscar la información del sistema mediante la búsqueda de texto, es decir tal y como lo haría con Google, en un único punto centralizado podrá acceder a productos, empresas, casos del CRM, adjuntos o cualquier otro documento del sistema que contenga las palabras que está buscando.

Para poder sacar provecho de esta funcionalidad, deberá configurar previamente qué campos del sistema quiere añadir al índice (es de decir, en qué campos se va a buscar). Para ello puede dirigirse a /// m: full_text_search.fts_full_text_index_menu /// e ir añadiendo los campos que desee. Verá que además del campo debe establecer una prioridad puesto que el sistema además le permite decir, por ejemplo, que si las palabras buscadas aparecen en el nombre de una empresa y en unas notas de un adjunto, la empresa deberá tener más importáncia y por tanto, mostrarse antes.

/// v: full_text_search.fts_full_text_index_form ///

Una vez haya añadido los campos que desee confgurar, deberá dirigirse a /// m: full_text_search.menu_fts_wizard /// y seleccionar el idioma con el que va a buscar. Una vez el proceso haya terminado, podrá buscar sobre los datos del sistema y a medida que vaya introduciendo datos podrá ir buscándolos inmediatamente.
