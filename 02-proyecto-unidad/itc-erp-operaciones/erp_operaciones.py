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
