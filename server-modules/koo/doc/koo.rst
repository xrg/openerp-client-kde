.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

===========
Cliente Koo
===========

---------------------
Funcionamiento básico
---------------------

Distribución funcional de la ventana Principal
==============================================

	Al abrir la aplicación koo y después de introducir el usuario y contraseña, nos aparece la ventana principal siguiente:

	.. image:: images/ventana_principal.png

	Desde esta ventana podremos acceder a las diferentes funcionalidades de la aplicación. 

	Vamos a describir las zonas de esta pantalla principal.

Zona - `Funciones de menú`_
---------------------------

	.. image:: images/zona1_1.png

	Aquí podemos ver el usuario con el que estamos accediendo a la aplicación koo

..


	.. image:: images/zona1_2.png

	Aquí vemos accesos a opciones básicas, podemos observar que hay algunas opciones que están de color gris. Esto significa que no están disponibles en este momento, dependiendo de la sección que tengamos seleccionada (`Zona Módulos`_)


	.. _`Zona Módulos`:

Zona - Accesos genéricos
------------------------

	.. image:: images/zona5.png

	En esta zona podemos ver diferentes iconos con su descripción funcional debajo. Estos iconos podemos encontrarlos activos (en color) o desactivados (en gris), en función del módulo y objeto que tengamos seleccionado en ese momento.

	Importante remarcar, la funcionalidad de "Cambiar Vista", la cual nos permite en cualquier momento, modificar el modo de vista de los objetos que tengamos seleccionados en ese momento. Normalmente tenemos la vista en forma de lista, pero si clickamos nos aparece la vista en forma de formulario (es decir, veremos una ficha completa de los campos de un objeto)

Zona - Menú principal
---------------------

	.. image:: images/zona2.png

	En esta zona de la ventana aparecen los módulos de OpenERP que tenemos instalados. Si seleccionamos un módulo con el ratón, nos lo marcará de color azul (de esta forma sabremos en todo momemto el módulo que tenemos seleccionado) y se actualizará la `zona de selección`_ en forma de árbol con las distintas funcionalidades.


	.. _`zona de selección`:

Zona - Selección
----------------

	.. image:: images/zona3.png

	En esta zona de la ventana aparecen las distintas funcionalidades de cada módulo. Semuestran en forma de árbol con la siguiente simbología:

	+ Carpeta `+`
	
	.. image:: images/simbologia1.png

	indica que dentro contiene más funcionalidades. Si seleccionamos con un click el símbolo `+`, se desplegarán las funcionalidades de la carpeta, al igual que si hacemos doble click en el símbolo de la carpeta.

	+ Carpeta `-`
	
	.. image:: images/simbologia2.png
	
	indica que esta carpeta ya tiene las funcionalidades desplegadas. Si clickamos una vez en el símbolo `-` se esconderán las funcionalidades de la carpeta.

	+ Lista simple

	.. image:: images/simbologia3.png

	Este símbolo nos indica que si clickamos en él, se abrirá una nueva pestaña con una vista en forma de lista con las distintas opciones.

	+ Lista en árbol

	.. image:: images/simbologia4.png

	Este símbolo nos indica que si clickamos en él, se abrirá una nueva pestaña con una vista en forma de árbol donde podremos ver la opciones classificadas por tipo/categoria/... en función del concepto que tengamos seleccionado.

	+ Nuevo

	.. image:: images/simbologia5.png

	Este símbolo indica que queremos añadir un nuevo objeto (dependiendo del módulo y la funcionalidad padre que tengamos seleccionado en ese momento).


Zona - Accesos directos
-----------------------

	.. image:: images/zona4.png

	En esta zona aparece una lista de accesos directos (configurable) para poder acceder directamente a alguna funcionalidad sin tener que seleccionar el módulo y los submenús correspondientes.


Zona - Estado
-------------

	.. image:: images/zona6.png

	En esta zona, encontraremos información relativa al Usuario y empresa.

+ Conexión
		
	.. image:: images/zona6_1.png

        En esta parte podemos observar el tipo de conexión (NET-RPC, XML-RPC, XML-RPC seguro o PYRO, que es el más rápido), luego podemos ver la dirección donde está el servidor OpenERP seguida del puerto utilizado. Entre corchetes podemos ver la Base de datos a la que estamos conectados.

+ Usuario

	.. image:: images/zona6_2.png

        En esta parte podemos observar el usuario que estamos utilizando y entre paréntesis, la compañía.


+ Peticiones

	.. image:: images/zona6_3.png

        En esta parte vemos el número de solicitudes que hemos recibido y los que hemos enviado.
	
+ Solicitudes

	.. image:: images/zona6_4.png

	Tenemos 2 accesos directos, el primero (izquierda) es para ver los mensajes que nos han enviado a nosotros. Y el segundo (derecha) es para ver las solicitudes que hemos realizado y que todavía no han eliminado.	


Particularidades del Koo
========================

	A continuación vamos a mostrar como interactuar con koo de forma más eficaz, utilizando diferentes abreviaturas, iconos y indicadores que nos van apareciendo en las diferentes ventanas.

	+ `Abreviaturas de teclado`_
	+ Iconos_
	+ `Información cromática`_
	+ Vistas_
        + Trucos_

Abreviaturas de teclado
-----------------------

	Aunque tenemos una ayuda con todas las abreviaturas que utiliza koo. Vamos a indicar las más utilizadas:
	
	.. image:: images/ayuda_abreviaturas.png


	+ F1
		Crear nuevo registro.

	+ F2
		Buscar/editar registros existentes. En cualquier campo que nos pida escojer un registro, podemos presionar F2 y nos aparecerá una lista de registros.

	+ F5
		Recargar. Ejemplo: si hemos añadido un registro, pero no lo vemos en la vista de formato lista, recargamos la lista con F5 y nos aparecerá el nuevo registro.
		
	+ F6
		Cambiar de vista. De tipo vista a tipo de formulario.

	+ F10
		Muestra ayuda del campo.

	+ Tabulador
		Seleccionamos el campo siguiente del formulario. Si queremos ir al anterior tenemos que presionar <Shift> + <Tabulador>

	+ CTRL + <flecha izquierda/derecha>

		Si tenemos varias pestañas, seleccionaremos la pestaña de la derecha o izquierda de la que tenemos seleccionada actualmente.

	+ `CTRL + A`
		Selecciona todos los registros

	+ `<Shift> + Cambio de Vista`
		Abre una nueva pestaña con la vista actual. Esto nos puede ser util cuando tengamos que revisar diferentes registros a posteriori.

	+ <Alt> + Flecha
		Para seleccionar el campo más cercano al actual en la dirección que hayamos establacido (izquierda, derecha, arriba o abajo). Esto puede ser util en formularios con muchos campos a editar y queramos modificar uno de ellos.

Iconos
------

	En esta sección vamos a describir la funcionalidad de los iconos propios del OpenERP.

	+ .. image:: images/icono_carpeta.png

	Este icono nos indica que si clickamos en él, entraremos en la ficha del objeto que estamos seleccionando.

	+ .. image:: images/icono_nuevo.png

	Este icono nos indica que si clickamos en él, crearemos una nueva ficha del objeto que estamos seleccionando.

	+ .. image:: images/icono_editar.png

	Este icono nos indica que si clickamos en él, modificaremos la ficha del objeto que estamos seleccionando.

	+ .. image:: images/icono_eliminar.png

	Este icono nos indica que si clickamos en él, vaciaremos el valor del campo seleccionado. Hay que tener cuidado y no confundir con el icono 

	.. image:: images/icono_borrar_registro.png

	el cual hace una eliminación de los datos de la ficha que estemos editando.

	+ .. image:: images/icono_eliminar_pestaña.png

	Este icono nos indica que si clickamos en él, nos cerrará la pestaña con la que estamos actuando en este momento.

	+ .. image:: images/icono_buscar.png

	Este icono nos indica que el campo actual tiene diferentes valores y que si clickamos en este icono nos aparecerá una lista de valores para poder seleccionar uno.
	
	+ .. image:: images/icono_idioma.png

	Este icono nos indica que el campo actual se puede traducir a diferentes idiomas y que si clickamos en él, podremos escribir la traducción en los diferentes idiomas.

	+ .. image:: images/icono_vista.png

	Este icono nos indica que si clickamos en él, nos cambiará la vista actual.

	+ .. image:: images/icono_derecha.png

	Este icono nos indica que el formulario que tenemos abierto, tiene asociado un acceso directo. Puede ser un listado o cualquier otra función asociada, que nos facilite lo que estemos haciendo.

	+ .. image:: images/icono_abajo.png

	Este icono puede aparecer en vistas de tipo lista, y nos indica que la selección se puede filtrar por mas campos de los que aparecen en la vista actual. Al clickar en él, aparecerán más campos para poder hacer el filtrado de la lista de valores.

	+ .. image:: images/icono_arriba.png

	Este icono puede aparecer en vistas de tipo lista, y nos indica que podemos reducir los campos de filtrado. Al clickar en él, se reducirá el número de campos de filtrado.

	+ .. image:: images/icono_herramienta.png

	Este icono puede aparecer en vistas de tipo lista, y nos indica que podemos crear nuestro propio filtro de selección especificando el campo (de la lista de campos), el tipo de operación y el valor. Al clickar en él, aparecerá una lista de los campos de este objeto. Luego tendremos que seleccionar el campo de la derecha para indicar el tipo de operación (igual, mayor que, contiene,...) y luego tendremos que indicar en el campo de la derrecha el valor del filtro. Seguidamente clickaremos en el icono "Buscar" que suele aparecer más a la derecha.
		
	+ .. image:: images/icono_nuevo_filtro.png

	Este icono puede aparecer en vistas de tipo lista cuando hemos seleccionado el icono de filtrado personalizado, y nos indica que podemos añadir otro filtro personalizado. Al clickar en él, aparecerá una nueva línea con tres campos, es decir, campo de filtrado, operación y valor.

	+ .. image:: images/icono_borrar_filtro.png

	Este icono puede aparecer en vistas de tipo lista cuando hemos seleccionado el icono de filtrado personalizado, y nos indica que podemos eliminar uno de los filtros que hemos creado. Al clickar en él, desaparecerá la línea con sus tres respectivos campos.

	+ .. image:: images/icono_borrar_filtros.png

	Este icono puede aparecer en vistas de tipo lista. Al clickar en él, nos eliminará los filtros creados anteriormente y vaciará los valores de los campos, para poder hacer un nuevo filtrado.


Información cromática 
---------------------

	En esta sección vamos a describir el significado de los colores en la aplicación.

	.. _`están en azul`:

	.. _`tipo obligatorio`:

	+ Fondo azul de un campo

	.. image:: images/campo_azul2.png

	Cuando estemos en un formulario y tengamos un campo con el fondo azul, esto significará que esta campo es obligatorio, y no nos dejará crear el registro si no hemos puesto ningún valor en este campo.

	.. _`en rojo`:

	+ Fondo rojo de un campo

	.. image:: images/campo_rojo.png

	Indica que el campo es obligatorio y hemos intentado guardar el registro sin rellenarlo.

	+ Fondo gris de un campo

	.. image:: images/campo_gris.png

	Esto indica que este campo no es modificable. No nos dejará entrar ningún valor.

	+ Fondo blanco de un campo

	.. image:: images/campo_blanco.png

	Esto indica que este campo es editable y opcional.


	.. _`Funciones de menú`:

        + Las cajas de texto grandes verifican la ortografía mientras se escribe en el idioma con el que trabaja el usuario. 

        .. image:: images/spellchecker1.png
        
        En caso de acceder a la pantalla de traducción de dicho texto, la verificación de ortografía se produce en el idioma a traducir.

        .. image:: images/spellchecker2.png

Vistas
------

	En esta sección describiremos el funcionamiento de las vistas y como utilizarlas de forma eficiente.

	.. image:: images/zona_vistas.png
	
+ Información de registro

	En la parte inferior izquierda, podemos ver información relativa al registro que tenemos seleccionado. Podemos ver el número de registro, el número total de registros y el identificador (interno) del registro seleccionado.

+ Estado

	En la parte inferior derecha, se puede ver si el registro seleccionado tiene algún documento adjunto o no. A demás, en esta sección puede aparecer información relativa a los cambios realizados del registro seleccionado. Nos pueden aparecer 3 mensajes:

	- En verde, nos informa que el registro se ha guardado correctamente.

	- En azul, nos indica que el registro se ha modificado correctamente.

	- `En rojo`_, nos indica que ha fallado al salvar los datos, suele suceder cuando hemos intentado guardar un registro sin rellenar un campo de `tipo obligatorio`_. En este caso, nos aparecerá una ventana de tipo pop-up, mostrando el campo obligatorio que hemos intentado guardar vacío.
	

Trucos
------

	Existen una serie de trucos para /seleccionar registros de forma más rápida y eficiente:

	.. image:: images/zona_vistas_busqueda.png
        
..

	- <TABULADOR>
		El tabulador nos puede servir ( a parte de movernos por los campo ), para buscar un valor.

	Por ejemplo:
		Si queremos buscar un objeto cuya primera palabra empiece por "wizard", escribimos wizard en el campo Objeto y seguidamente presionamos la tecla <Tabulador>. Nos mostrará el primer Objeto que cumpla esta premisa.

	- Operaciones matemáticas

		Si estando en un formulario, tenemos un campo numérico, podríamos realizar una  operación matemática simple ( +,-,*,/) directamente en el campo.
	
	- Fechas

		Para introducir una fecha, no es necesario escribir la fecha completa.

		+ Si queremos escribir el día de hoy, basta con escribir el símbolo **=**. (Ejemplo: si hoy escribimos **=**, aparecerá |DIA|/|MES|/|AÑO|) 
		+ Si queremos poner un día de este mes, basta con escribir el número de día. (Ejemplo: **26**, para indicar **26**/|MES|/|AÑO|)
		+ Si queremos poner un día y un mes de este año, basta con escribir el número de día seguido del número de mes. (Ejemplo: **1401**, para indicar **14**/**01**/|AÑO|)

.. Note:: para que autocomplete el campo fecha hay que salir del campo.
		
-----------------
Funciones de menú
-----------------

Base de datos
=============

Opciones básicas
----------------

Apartado que nos da acceso a cuatro acciones relacionadas con la Base de datos a utilizar. 

 .. image:: images/menu_base_de_datos_opciones.png

- Conectar
- Desconectar
- Administrar una Base de Datos
- Salir de la aplicación OpenERP

**Conectar**
	Para poder conectar a una Base de Datos.

**Desconectar**
	Si deseamos desconectar de la Base de Datos actual.

**Administrar una Base de Datos**
	Si accedemos a esta opción, nos aparece otro menú_ con las siguientes funcionalidades 

**Salir**
	Para salir de la aplicación OpenERP

.. _menú:
.. _`Volver a Administrar Base de datos`:

Administrar una Base de Datos
-----------------------------


 .. image:: images/menu_base_de_datos_administracion.png

..

- `Nueva Base de datos`_
- `Restaurar Base de datos`_
- `Copia de Seguridad`_
- `Eliminar una Base de Datos`_
- `Cambiar contraseña del administrador`_
	
.. _`Nueva Base de datos`:

**Nueva Base de datos**

	Al acceder a esta opción, nos parece una nueva ventana con este formulario

 .. image:: images/menu_base_de_datos_nueva.png

..

+------------------------------+-------------------------------------------------+
|Campos			       |Información adicional                            |
+==============================+=================================================+
|Servidor OpenERP:	       |Aquí debemos incorporar la dirección IP donde    |
|			       |reside el servidor junto con el puerto           |
|			       |utilizado (después de los :)                     |
+------------------------------+-------------------------------------------------+
|Contraseña de super 	       |Se pide la contraseña actual del super usuario   |
|administrador                 |para poder dar de alta la base de datos nueva    |
+------------------------------+-------------------------------------------------+
|Nombre de la nueva base de    |Cualquier nombre que no tenga caracteres         |
|datos:                        |especiales                                       |
+------------------------------+-------------------------------------------------+
|Cargar datos de demostración  |Añade datos de demostración (normalmente se      |
|                              |utilizan para hacer pruebas y aprender a utilizar|
|                              |la aplicación)                                   |
|                              |**Importante:** No utilizar nunca como datos de  |
|                              |Explotación                                      |
+------------------------------+-------------------------------------------------+
|Idioma por defecto            |Solo aparecen los idiomas instalados en la       |
|                              |aplicación                                       |
+------------------------------+-------------------------------------------------+
|Contraseña de admin           |Establecer una contraseña para poder administrar |
|                              |la Base de datos                                 |
+------------------------------+-------------------------------------------------+

..

.. _`Restaurar Base de datos`:
	
**Restaurar copia de una Base de datos**

	Al acceder a esta opción, nos parece una nueva ventana con este formulario

	 .. image:: images/menu_base_de_datos_restaurar1.png

	seguidamente nos preguntará que base de datos de destino queremos.

	 .. image:: images/menu_base_de_datos_restaurar2.png

	Finalmente solo tenemos que clicar en 'Aceptar' y empezará la restauración.

..

.. _`Copia de Seguridad`:

**Copia de Seguridad de una base de datos**
	Al acceder a esta opción, nos parece una nueva ventana con este formulario

 .. image:: images/menu_base_de_datos_copia.png

Introducimos la contraseña del administrador, seleccionamos la Base de Datos y clicamos en "Aceptar".

Seguidamente aparece una ventana para escoger el nombre de fichero y la carpeta de destino donde deseamos guardar la copia de la Base de Datos.

 .. image:: images/menu_base_de_datos_guardar.png

..

.. _`Eliminar una Base de Datos`:

**Eliminar una Base de Datos**
	Al acceder a esta opción, nos parece una nueva ventana con este formulario

 .. image:: images/menu_base_de_datos_eliminar.png

Introducimos la contraseña del administrador, seleccionamos la Base de Datos y clicamos en "Aceptar".

Seguidamente nos eliminará la Base de Datos.

.. _`Cambiar contraseña del administrador`:

**Cambiar contraseña del administrador**
	Al acceder a esta opción, nos parece una nueva ventana con este formulario

 .. image:: images/menu_base_de_datos_contraseña.png

Introducimos la contraseña del administrador, la nueva contraseña y la volvemos a escribir. Finalmente clicamos en "Aceptar".

`Volver a Administrar Base de datos`_

.. _`Preferencias de Usuario`:

Usuarios
========

Apartado que nos da acceso a cinco acciones relacionadas con el usuario de la Base de datos con el que hemos entrado. 

 .. image:: images/menu_usuario.png

- Preferencias
- Limpiar cache
- Enviar una Petición
- Leer Mis Peticiones
- Peticiones en Espera

**Preferencias**


	.. image:: images/menu_usuario_preferencias.png

	En esta pantalla podemos cambiar la contraseña del usuario, cambiar el idioma (teniendo en cuanta que sólo podemos escojer entre los idiomas instalados), Zona horaria y la Firma.

**Limpiar cache**

**Enviar una Petición**
	La funcionalidad de esta opción, es la de enviar un mensaje a otro usuario de la empresa. Este mensaje se puede enviar al momento o dejarlo programado para su futuro envío. Cuando el usuario destino acceda a la aplicación koo y consulte los `mensajes recibidos`_, podrá ver el mensaje que hemos enviado anteriormente.

	Para poder enviar el mensaje, nos obliga a introducir los campos /// f: base.field_res_request_act_to /// y /// f: base.field_res_request_name /// 

	/// v: base.res_request-view ///

	En el campo /// f: base.field_res_request_act_to /// tendremos que introducir el usuario al cual le queremos enviar el mensaje. En el campo /// f: base.field_res_request_name /// pondremos la cabecera del mensaje.

	Por otro lado, cabe destacar el campo /// f: base.field_res_request_trigger_date /// sirve para programar el envio del mensaje. Si no rellenamos este campo, enviará el mensaje en el momento que finalicemos el formulario.

	Como podemos observar en la pestaña /// f: base.field_res_request_history /// podemos ver el historial de todos los mensajes.


.. _`mensajes recibidos`:

**Leer Mis Peticiones**

	En esta opción nos aparece una vista donde podemos observar las peticiones realizadas a nuestro usuario. Podemos filtrar la vista por fechas, asunto y usuario que realizó la petición.

.. _`peticiones en espera`:

**Peticiones en espera**

	En esta opción, al igual que en el apartado anterior, nos aparece una vista, pero en este caso podremos observar las peticiones que hemos realizado pero que todavía no se han enviado (porque están programadas para un envío posterior a la fecha actual).

-------
Idiomas
-------

Descripción
===========

Podemos utilizar koo con diferentes idiomas. Se puede cambiar de idioma en el momento que queramos, pero para poder utilizar los distintos idiomas será necesario que tengamos cargadas las traducciones en el idioma correspondiente. 

Como instalar un idioma
=======================

Para instalar un idioma, tenemos que seguir los siguientes pasos:

#. Ir al módulo de "Administración" en el menú principal

#. Desplegar la pestaña de "Traducciones"

#. Escojer la opción "Cargar una traducción oficial"

#. Seleccionamos el idioma

#. I clickamos en "Iniciar instalación"

#. Una vez finalizado, nos aparece una ventana donde nos dice que la instalación se ha realizado correctamente. Clicamos en "Aceptar"

#. Ahora solo nos queda seleccionar el idioma en la preferencias del usuario. Vamos a `Preferencias de Usuario`_ y escojemos el idioma que acabamos de instalar.

#. Una vez escojido el idioma, es importante refrescar la ventana con la tecla 'F5'


----------------------------------
El fichero de configuración .koorc
----------------------------------

Algunos aspectos del funcionamiento y apariencia de Koo pueden alterarse mediante el fichero de configuración .koorc que se puede encontrar en la carpeta principal del usuario que lo ejecuta. Típicamente `c:\\documents and settins\\usuario` en windows y `/home/usuario` en GNU/Linux.

El fichero está dividido en varios grupos:

[koo]
=====

show_pos_toolbar = True / False
  Indica si se mostrará o no una barra de herramientas para la versión de pantalla completa de Koo. El koopos.py.

pos_mode = True / False
  Indica si Koo se iniciará en modo Terminal Punto de Venta. El modo terminal punto de venta muestra un teclado virtual
  en pantalla cada vez que el usuario hace click en algún elemento de la aplicación que requiera la introducción de texto
  por parte del usuario.

allow_massive_updates = True / False
  Indica si se mostrarán las opciones de actualización, inserción y click de botones masivas. 

[login]
=======

url = http://admin:contraseña@localhost:8069
  Indica el protocolo, usuario, contraseña, servidor y puerto a utilizar inicialmente para conectarse. Si especifica una contraseña, Koo intentará entrar directamente al sistema.

db = database
  Indica la base de datos que se va a utilizar por defecto al entrar en la aplicación.

[open]
======

model = 'res.partner'
  Indica el modelo de OpenERP a abrir automáticamente cuando se ponga en marcha Koo.

id = 45
  Indica el id del registro a abrir dentro del model indicado. Si 'id' no se especifica, se mostrará el listado de todos los registros.

always = True/False
  Si *always* es False (por defecto), Koo limpiará automáticamente los parámetros model e id, de forma que la próxima vez que se inicie la aplicación no entrará automáticamente al model e id indicados.
