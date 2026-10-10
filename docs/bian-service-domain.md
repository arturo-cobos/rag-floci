# Service Domain en BIAN

Un Service Domain es la unidad básica de la arquitectura de referencia BIAN.
Representa una capacidad de negocio única y no solapada: una cosa que el banco
sabe hacer, descrita de forma independiente de la tecnología que la implementa.

BIAN define más de 300 Service Domains agrupados en Business Areas y Business
Domains. La regla de oro es que no se solapan: si dos Service Domains parecen
hacer lo mismo, uno de los dos está mal delimitado.

## Control Record

Cada Service Domain administra exactamente un Control Record. Es el objeto de
datos que concentra el estado de la capacidad: su identificador, su ciclo de
vida y los atributos que el Service Domain gobierna. Si el Service Domain es
"Current Account", su Control Record es la instancia de cuenta corriente con su
saldo, su estado y sus condiciones.

El Control Record es la frontera de responsabilidad. Un Service Domain no
escribe en el Control Record de otro: le pide algo a través de un servicio.

## Behavior Qualifier

Los Behavior Qualifiers son las subdivisiones del Control Record. Permiten
exponer partes del comportamiento sin romper el encapsulamiento. En una cuenta
corriente, los movimientos y los bloqueos serían Behavior Qualifiers distintos.

Al mapear un modelo propio contra BIAN, los Behavior Qualifiers se alinean
contra el Business Object Model (BOM), que es el diccionario de datos canónico.
Lo que no existe en BIAN se mantiene como extensión, con un prefijo propio que
deje claro que no es estándar.
