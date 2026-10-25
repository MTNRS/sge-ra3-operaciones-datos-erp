# Reporte de proyecto

## Información de generación

- **Fecha:** 2026-10-25 12:20:32 +0100
- **Usuario:** freak
- **Equipo:** JARVIS
- **Sistema operativo:** Windows
- **Arquitectura:** x86_64
- **Directorio de ejecución:** `C:/Users/freak/DAM2`
- **Proyecto documentado:** `C:/Users/freak/Documents/DAM2-entregas/sge-ra3-operaciones-datos-erp`
- **HMAC-SHA-256 de autenticidad:** `899ca6a76b099d8ccf961c2e0aa2a0dc889c54bab1f243f67f812f1f7ec7d4d9`

> El HMAC-SHA-256 se calcula sobre el documento completo usando un secreto incluido en el programa y 64 ceros en el propio campo del HMAC. El secreto no se escribe en el informe. Este mecanismo permite comprobar integridad y que el documento fue generado con el mismo secreto.

## Estructura del proyecto

```
C:/Users/freak/Documents/DAM2-entregas/sge-ra3-operaciones-datos-erp
├── .gitignore
├── 01-ejercicios
│   ├── 01-consultas.md
│   ├── 02-importacion.csv
│   └── 03-rendimiento.md
├── 02-proyecto-unidad
│   └── itc-erp-operaciones
│       ├── OPERACIONES.md
│       ├── data
│       │   └── itc_erp_ra3.sqlite [SQLite]
│       ├── erp_operaciones.py
│       └── salidas
│           ├── .gitkeep
│           ├── clientes-exportacion.csv
│           └── informe-clientes.md
├── 03-criterios-evaluacion
│   └── RESPUESTAS-CRITERIOS.md
└── README.md
```

## Bases de datos SQLite

Esta sección documenta únicamente el esquema de las bases SQLite detectadas. No se vuelcan registros ni datos de usuario.

### 02-proyecto-unidad/itc-erp-operaciones/data/itc_erp_ra3.sqlite

```text
02-proyecto-unidad/itc-erp-operaciones/data/itc_erp_ra3.sqlite
├── tabla clientes
│   ├── columnas
│   │   ├── id INTEGER PRIMARY KEY
│   │   ├── nombre TEXT NOT NULL
│   │   ├── email TEXT NOT NULL
│   │   ├── estado TEXT NOT NULL
│   │   └── creado TEXT NOT NULL
│   └── índices
│       ├── idx_clientes_estado: estado
│       └── sqlite_autoindex_clientes_1 (UNIQUE): email
└── tabla operaciones
    └── columnas
        ├── momento TEXT
        ├── accion TEXT
        └── detalle TEXT
```


## Código (intercalado)

# sge-ra3-operaciones-datos-erp
**README.md**
```markdown
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
```
## 01-ejercicios
**01-consultas.md**
```markdown
# Consultas

Se prueban selección, filtro por estado, ordenación y agrupación con SQLite:
`SELECT estado, count(*) FROM clientes GROUP BY estado`.
```
**03-rendimiento.md**
```markdown
# Rendimiento

El proyecto crea el índice `idx_clientes_estado` y mide el tiempo de una
consulta filtrada. Es una comprobación local previa a la carga real.
```
## 02-proyecto-unidad
### itc-erp-operaciones
**OPERACIONES.md**
```markdown
# Operaciones e incidencias

La herramienta prepara la carga futura con una plantilla CSV validada. Si una
fila no tiene nombre, email válido o estado permitido, se rechaza toda la
importación sin insertar datos parciales. Las salidas se generan en
`salidas/`, excluidas de Git por ser resultados locales.
```
**erp_operaciones.py**
```python
"""Operaciones de información para la preparación de ITC ERP."""
import argparse, csv, json, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).parent; DATA=BASE/"data"; BD=DATA/"itc_erp_ra3.sqlite"; OUT=BASE/"salidas"
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def con():
    DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    return sqlite3.connect(BD)
def init():
    with con() as c:
        c.executescript("CREATE TABLE IF NOT EXISTS clientes(id INTEGER PRIMARY KEY,nombre TEXT NOT NULL,email TEXT NOT NULL UNIQUE,estado TEXT NOT NULL,creado TEXT NOT NULL);CREATE TABLE IF NOT EXISTS operaciones(momento TEXT,accion TEXT,detalle TEXT);CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado);")
        if not c.execute("SELECT count(*) FROM clientes").fetchone()[0]:
            c.executemany("INSERT INTO clientes(nombre,email,estado,creado) VALUES(?,?,?,?)",[(n,e,s,now()) for n,e,s in [('Nexo Formación S.L.','contacto@nexoformacion.example','activo'),('Cafetería Horizonte','gestion@horizonte.example','prospecto'),('Talleres Levante','it@tallereslevante.example','activo'),('Asociación Río Claro','admin@rioclaro.example','inactivo')]])
        c.execute("INSERT INTO operaciones VALUES(?,?,?)",(now(),"inicialización","estructura y datos ficticios preparados"))
    print("Base preparada:",BD)
def query(estado=None):
    with con() as c:
        sql="SELECT id,nombre,email,estado,creado FROM clientes"; args=()
        if estado: sql+=" WHERE estado=?";args=(estado,)
        rows=c.execute(sql+" ORDER BY nombre",args).fetchall()
    print("ID | NOMBRE | EMAIL | ESTADO");[print(" | ".join(map(str,r[:4]))) for r in rows]
    return rows
def alta(nombre,email,estado):
    with con() as c:
        c.execute("INSERT INTO clientes(nombre,email,estado,creado) VALUES(?,?,?,?)",(nombre,email,estado,now()));c.execute("INSERT INTO operaciones VALUES(?,?,?)",(now(),"alta cliente",email))
    print("Cliente registrado.")
def importar(path):
    correctos=[]; errores=[]
    with open(path,encoding="utf-8-sig",newline="") as f:
        for n,row in enumerate(csv.DictReader(f),2):
            if not row.get("nombre") or "@" not in row.get("email","") or row.get("estado") not in ("activo","prospecto","inactivo"): errores.append(f"línea {n}");continue
            correctos.append((row["nombre"].strip(),row["email"].strip(),row["estado"],now()))
    if errores: raise ValueError("CSV rechazado: "+", ".join(errores))
    with con() as c:
        c.executemany("INSERT INTO clientes(nombre,email,estado,creado) VALUES(?,?,?,?)",correctos);c.execute("INSERT INTO operaciones VALUES(?,?,?)",(now(),"importación",f"{len(correctos)} clientes"))
    print("Importación correcta:",len(correctos))
def informe():
    with con() as c: resumen=c.execute("SELECT estado,count(*) FROM clientes GROUP BY estado ORDER BY estado").fetchall()
    p=OUT/"informe-clientes.md";p.write_text("# Informe de clientes ITC ERP\n\n| Estado | Total |\n|---|---:|\n"+"".join(f"| {s} | {n} |\n" for s,n in resumen)+f"\nGenerado: {now()}\n",encoding="utf-8");print(p)
def exportar():
    rows=query();p=OUT/"clientes-exportacion.csv"
    with p.open("w",encoding="utf-8",newline="") as f: w=csv.writer(f);w.writerow(("id","nombre","email","estado","creado"));w.writerows(rows)
    print(p)
def extraer():
    informe();exportar();print("Extracción programable finalizada:",now())
def rendimiento():
    t=time.perf_counter(); query(); ms=(time.perf_counter()-t)*1000;print(f"Consulta indexada: {ms:.2f} ms")
if __name__=="__main__":
    p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
    s.add_parser("inicializar");q=s.add_parser("consultar");q.add_argument("--estado",choices=("activo","prospecto","inactivo"));a=s.add_parser("alta");a.add_argument("nombre");a.add_argument("email");a.add_argument("--estado",default="prospecto",choices=("activo","prospecto","inactivo"));i=s.add_parser("importar");i.add_argument("--archivo",required=True);s.add_parser("informe");s.add_parser("exportar");s.add_parser("extraer");s.add_parser("rendimiento");x=p.parse_args();{"inicializar":init,"consultar":lambda:query(x.estado),"alta":lambda:alta(x.nombre,x.email,x.estado),"importar":lambda:importar(x.archivo),"informe":informe,"exportar":exportar,"extraer":extraer,"rendimiento":rendimiento}[x.cmd]()
```
#### data
#### salidas
**informe-clientes.md**
```markdown
# Informe de clientes ITC ERP

| Estado | Total |
|---|---:|
| activo | 2 |
| inactivo | 1 |
| prospecto | 1 |

Generado: 2026-10-25T11:20:32+00:00
```
## 03-criterios-evaluacion
**RESPUESTAS-CRITERIOS.md**
```markdown
# RA3 · Criterios de evaluación

| Criterio | Evidencia |
|---|---|
| a) | SQLite y consultas SQL de selección, filtro, ordenación y agrupación. |
| b) | Comando `alta` y plantilla CSV como formularios de entrada validados. |
| c) | `informe` genera un informe Markdown agrupado por estado. |
| d) | `exportar` crea CSV reutilizable. |
| e) | `extraer` encadena informe y exportación. |
| f) | `rendimiento` mide consulta indexada por estado. |
| g) | `OPERACIONES.md` documenta procedimiento e incidencias. |
| h) | El informe identifica distribución de cartera por estado. |
```
