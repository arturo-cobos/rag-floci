# Módulo de Depósitos en un Core bancario

El módulo de Depósitos administra los productos pasivos: cuentas de ahorro,
cuentas corrientes y depósitos a término. Su responsabilidad es el saldo y su
movimiento, no la identidad del cliente, que vive en el CIF.

## Funcionalidades

La apertura de cuenta crea la instancia del producto, le asigna un número y la
vincula a un cliente existente. No crea clientes: si el cliente no existe, la
apertura falla y el flujo se devuelve al módulo de Clientes.

El registro de movimientos aplica débitos y créditos contra el saldo. Cada
movimiento genera un asiento contable por partida doble y queda inmutable: una
corrección no edita el movimiento, registra uno nuevo que lo reversa.

El cálculo de intereses corre en el cierre, aplicando la tasa vigente al saldo
promedio del período. La liquidación es un movimiento más.

El bloqueo de fondos reserva una parte del saldo sin moverlo. Es lo que
sostiene las autorizaciones de tarjeta y los embargos judiciales.

## Entidades de datos

La entidad Cuenta concentra el estado: número, tipo de producto, moneda, saldo
disponible, saldo total, estado del ciclo de vida y fecha de apertura. El saldo
disponible y el saldo total se separan a propósito, porque los bloqueos hacen
que difieran.

La entidad Movimiento registra cada débito o crédito: identificador, cuenta,
tipo, valor, fecha de aplicación, fecha valor y referencia al asiento contable.
La fecha de aplicación y la fecha valor también se separan: un movimiento puede
registrarse hoy y tener efecto contable ayer.

La entidad Bloqueo relaciona una cuenta con un monto reservado, su motivo y su
vigencia.
