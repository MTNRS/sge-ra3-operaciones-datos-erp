# RA3 · Operaciones de información ERP-CRM

Continuación de ITC ERP RA2. Prepara el sistema para recibir datos reales en la
unidad 4 sin incorporarlos todavía: usa una base SQLite local y datos
ficticios/anonimizados.

## Estructura

- `01-ejercicios`: consultas, formularios, informes y rendimiento.
- `02-proyecto-unidad`: herramienta de operaciones ITC ERP.
- `03-criterios-evaluacion`: evidencias de cada criterio.

## Ejecución

```powershell
cd 02-proyecto-unidad/itc-erp-operaciones
python erp_operaciones.py inicializar
python erp_operaciones.py consultar --estado abierto
python erp_operaciones.py informe
python erp_operaciones.py exportar
python erp_operaciones.py rendimiento
```

Para cargar datos futuros se usará `importar --archivo clientes.csv`. El CSV
debe tener las columnas `nombre,email,estado`; se valida antes de insertarlo.
No se incluyen ni se necesitan datos de clientes reales.
