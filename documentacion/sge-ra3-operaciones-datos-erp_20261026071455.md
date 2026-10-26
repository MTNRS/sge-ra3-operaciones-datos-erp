# Reporte de proyecto

## Información de generación

- **Fecha:** 2026-10-26 07:14:55 +0100
- **Usuario:** freak
- **Equipo:** JARVIS
- **Sistema operativo:** Windows
- **Arquitectura:** x86_64
- **Directorio de ejecución:** `C:/Users/freak/DAM2`
- **Proyecto documentado:** `C:/Users/freak/Documents/DAM2-entregas/sge-ra3-operaciones-datos-erp`
- **HMAC-SHA-256 de autenticidad:** `ef83bf478527cbb857113f03d534010c97bc00e0fdf6a1bfb314baee6d9a5750`

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
│       ├── erp_operaciones.py
│       ├── panel.css
│       ├── panel.html
│       ├── panel.js
│       └── servidor.py
├── 03-criterios-evaluacion
│   └── RESPUESTAS-CRITERIOS.md
└── README.md
```

## Bases de datos SQLite

Esta sección documenta únicamente el esquema de las bases SQLite detectadas. No se vuelcan registros ni datos de usuario.

No se han encontrado bases SQLite con extensiones .db, .sqlite o .sqlite3.

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

## Panel gráfico

```powershell
cd 02-proyecto-unidad/itc-erp-operaciones
python servidor.py
```

Abrir `http://127.0.0.1:8090/panel.html`. El panel reúne consulta y filtro,
formulario de alta, validación de CSV, informe, exportación y rendimiento.

## Ejecución por consola

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
**panel.css**
```css
:root{--nav:#09283b;--green:#168f61;--blue:#1686cc;--line:#dbe7ed;--muted:#697986;--bg:#f4f8fa}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#172936;font:14px system-ui}.brand{display:flex;gap:10px;align-items:center;color:white;padding:5px 8px 24px}.brand b,header>b{display:grid;place-items:center;width:37px;height:37px;border-radius:10px;background:#72efb2;color:#063b31}.brand small{display:block;color:#9ab4c1;font-size:10px}aside{position:fixed;width:250px;inset:0 auto 0 0;padding:22px 13px;display:flex;flex-direction:column;background:linear-gradient(#09283b,#0b3a51 60%,#07523d);color:#b8d1db}aside p{margin:18px 10px 6px;color:#74a2b7;font-size:10px;letter-spacing:.12em}aside a{padding:9px 10px;color:#c7d9e0;text-decoration:none;border-radius:7px}aside a:hover,aside .active{color:white;background:#ffffff1b}.note{margin-top:auto;padding:13px 10px;border-top:1px solid #ffffff28;font-size:10px}.note strong{font-size:12px;color:#fff}main{margin-left:250px}header{height:76px;padding:13px 32px;display:flex;justify-content:space-between;align-items:center;background:white;border-bottom:1px solid var(--line)}header h1{margin:2px 0;font-size:21px}header small,.muted{color:var(--muted)}.page{max-width:1200px;margin:auto;padding:28px}.head,.cardhead{display:flex;justify-content:space-between;align-items:start;gap:15px}.head h2{margin:0;font-size:25px}.head p{margin:5px 0;color:var(--muted)}#status,.badge{padding:5px 9px;background:#e4f8ed;color:#137147;border-radius:99px;font-weight:700;font-size:12px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}.metric,.card{background:#fff;border:1px solid var(--line);border-radius:13px;box-shadow:0 5px 16px #16465a0a}.metric{padding:15px}.metric small{color:var(--muted)}.metric b{display:block;font-size:24px;color:var(--blue)}.card{margin:16px 0;overflow:hidden}.cardhead{padding:15px 18px;border-bottom:1px solid var(--line);align-items:center}.cardhead h3{margin:0;font-size:15px}.inner,form{padding:18px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:11px 15px;border-bottom:1px solid var(--line)}th{font-size:11px;text-transform:uppercase;color:var(--muted);background:#fbfdfe}.twocol{display:grid;grid-template-columns:1fr 1fr;gap:16px}form{display:grid;gap:10px}label{display:grid;gap:5px;color:var(--muted);font-size:12px;font-weight:700}input,select{padding:9px;border:1px solid #bfd4df;border-radius:7px;font:inherit}button,.button{border:0;border-radius:7px;background:var(--blue);color:white;padding:10px 13px;font-weight:700;text-decoration:none;cursor:pointer}code{background:#edf3f6;padding:3px}@media(max-width:800px){aside{position:static;width:auto}main{margin:0}.metrics,.twocol{grid-template-columns:1fr 1fr}.page{padding:16px}}@media(max-width:540px){.metrics,.twocol{grid-template-columns:1fr}header{padding:12px 17px}}
```
**panel.html**
```html
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Operaciones de datos · ITC ERP</title><link rel="stylesheet" href="panel.css"></head><body><aside><div class="brand"><b>ITC</b><span>Integra ERP<small>Operaciones de datos · RA3</small></span></div><p>OPERACIONES</p><a class="active" href="#consulta">▦ Consultas</a><a href="#formularios">＋ Alta de cliente</a><a href="#importar">⇧ Importación CSV</a><p>ANÁLISIS</p><a href="#informe">▤ Informe de cartera</a><a href="#exportar">⇩ Exportación</a><a href="#rendimiento">◷ Rendimiento</a><div class="note">ENTORNO LOCAL<br><strong>Datos ficticios</strong></div></aside><main><header><div><small>ERP / Operaciones / Preparación unidad 4</small><h1>Gestión de información</h1></div><b>AD</b></header><section class="page"><div class="head"><div><h2>Preparación de datos reales</h2><p>Herramientas de consulta, validación, análisis y extracción para ITC ERP.</p></div><span id="status">Conectando…</span></div><div id="metrics" class="metrics"></div><section id="consulta" class="card"><div class="cardhead"><h3>Consulta de clientes</h3><select id="filter"><option value="">Todos los estados</option><option value="activo">Activos</option><option value="prospecto">Prospectos</option><option value="inactivo">Inactivos</option></select></div><table><thead><tr><th>Empresa</th><th>Email</th><th>Estado</th><th>Alta</th></tr></thead><tbody id="table"></tbody></table></section><div class="twocol"><section id="formularios" class="card"><div class="cardhead"><h3>Formulario de alta</h3></div><form id="form"><label>Empresa<input name="nombre" required></label><label>Correo<input name="email" type="email" required></label><label>Estado<select name="estado"><option value="prospecto">Prospecto</option><option value="activo">Activo</option><option value="inactivo">Inactivo</option></select></label><button>Registrar cliente</button></form></section><section id="importar" class="card"><div class="cardhead"><h3>Importación CSV validada</h3></div><div class="inner"><p>Columnas: <code>nombre,email,estado</code></p><input id="file" type="file" accept=".csv"><button id="preview" type="button">Validar e importar</button><p id="importMsg"></p></div></section></div><section id="informe" class="card"><div class="cardhead"><h3>Informe de cartera</h3><button id="report">Generar informe</button></div><div id="reportOut" class="inner muted">Genera el informe para obtener información relevante.</div></section><section id="exportar" class="card"><div class="cardhead"><h3>Exportación y extracción</h3><a class="button" href="/api/exportar">Descargar CSV de clientes</a></div><div class="inner">La descarga es una extracción reutilizable de la cartera procesada.</div></section><section id="rendimiento" class="card"><div class="cardhead"><h3>Comprobación de rendimiento</h3></div><div id="perf" class="inner">Pendiente de consulta.</div></section></section></main><script src="panel.js"></script></body></html>
```
**panel.js**
```js
const $=s=>document.querySelector(s);const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));async function api(url,opts){let r=await fetch(url,opts),j=await r.json();if(!r.ok)throw Error(j.error);return j}function paint(m){metrics.innerHTML=[['Clientes totales',m.total],['Activos',m.activos],['Prospectos',m.prospectos],['Consulta indexada',m.consulta_ms+' ms']].map(x=>'<article class="metric"><small>'+x[0]+'</small><b>'+x[1]+'</b></article>').join('');perf.textContent='Última consulta de cartera: '+m.consulta_ms+' ms. El índice por estado está activo.'}async function load(){let q=filter.value?'?estado='+filter.value:'';let [clientes,resumen]=await Promise.all([api('/api/clientes'+q),api('/api/resumen')]);table.innerHTML=clientes.map(x=>'<tr><td><strong>'+esc(x.nombre)+'</strong></td><td>'+esc(x.email)+'</td><td><span class="badge">'+esc(x.estado)+'</span></td><td>'+esc(x.creado)+'</td></tr>').join('')||'<tr><td colspan="4">No hay coincidencias.</td></tr>';paint(resumen);status.textContent='Sistema preparado'}filter.onchange=load;form.onsubmit=async e=>{e.preventDefault();try{await api('/api/clientes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(form)))});form.reset();load()}catch(err){alert(err.message)}};preview.onclick=()=>{let f=file.files[0];if(!f)return importMsg.textContent='Selecciona un CSV.';let r=new FileReader();r.onload=async()=>{let [head,...lines]=r.result.trim().split(/\r?\n/);let keys=head.split(',');let filas=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[keys[i],v.trim()])));try{let x=await api('/api/importar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filas})});importMsg.textContent='Importadas '+x.filas+' filas.';load()}catch(e){importMsg.textContent=e.message}};r.readAsText(f)};report.onclick=async()=>{let x=await api('/api/informe');reportOut.innerHTML='<strong>'+x.titulo+'</strong><p>'+x.conclusion+'</p><small>Generado: '+x.generado+'</small>'};load().catch(e=>status.textContent=e.message);
```
**servidor.py**
```python
"""Servidor local gráfico para las operaciones de datos de ITC ERP."""
import csv, io, json, sqlite3, time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import erp_operaciones as erp

BASE=Path(__file__).parent
def rows(estado=None):
    with erp.con() as c:
        sql="SELECT id,nombre,email,estado,creado FROM clientes";args=()
        if estado: sql+=" WHERE estado=?";args=(estado,)
        return [dict(zip(("id","nombre","email","estado","creado"),r)) for r in c.execute(sql+" ORDER BY nombre",args)]
def metrics():
    start=time.perf_counter(); datos=rows(); ms=round((time.perf_counter()-start)*1000,2)
    resumen={"total":len(datos),"activos":sum(x["estado"]=="activo" for x in datos),"prospectos":sum(x["estado"]=="prospecto" for x in datos),"inactivos":sum(x["estado"]=="inactivo" for x in datos),"consulta_ms":ms}
    return resumen
def validar(items):
    correctos=[];errores=[]
    for pos,x in enumerate(items,1):
        nombre=str(x.get("nombre","")).strip(); email=str(x.get("email","")).strip(); estado=str(x.get("estado","")).strip()
        if not nombre or "@" not in email or estado not in ("activo","prospecto","inactivo"): errores.append(pos)
        else: correctos.append((nombre,email,estado,erp.now()))
    if errores: raise ValueError("Filas no válidas: "+", ".join(map(str,errores)))
    return correctos
class App(SimpleHTTPRequestHandler):
    def json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def body(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))).decode())
    def do_GET(self):
        erp.init()
        if self.path.startswith("/api/clientes"):
            estado=self.path.split("estado=",1)[-1] if "estado=" in self.path else None;return self.json(rows(estado))
        if self.path=="/api/resumen": return self.json(metrics())
        if self.path=="/api/informe":
            datos=metrics();return self.json({"titulo":"Informe de cartera ITC","generado":erp.now(),"resumen":datos,"conclusion":f"{datos['activos']} clientes activos y {datos['prospectos']} prospectos requieren seguimiento."})
        if self.path=="/api/exportar":
            out=io.StringIO();w=csv.writer(out);w.writerow(("id","nombre","email","estado","creado"));[w.writerow(tuple(x.values())) for x in rows()];raw=out.getvalue().encode();self.send_response(200);self.send_header("Content-Type","text/csv; charset=utf-8");self.send_header("Content-Disposition","attachment; filename=clientes-itc.csv");self.end_headers();self.wfile.write(raw);return
        return super().do_GET()
    def do_POST(self):
        try:
            erp.init(); data=self.body()
            if self.path=="/api/clientes":
                valores=validar([data])[0]
                with erp.con() as c:c.execute("INSERT INTO clientes(nombre,email,estado,creado) VALUES(?,?,?,?)",valores);c.execute("INSERT INTO operaciones VALUES(?,?,?)",(erp.now(),"alta gráfica",valores[1]))
                return self.json({"ok":True},201)
            if self.path=="/api/importar":
                valores=validar(data.get("filas",[]))
                with erp.con() as c:c.executemany("INSERT INTO clientes(nombre,email,estado,creado) VALUES(?,?,?,?)",valores);c.execute("INSERT INTO operaciones VALUES(?,?,?)",(erp.now(),"importación gráfica",f"{len(valores)} filas"))
                return self.json({"ok":True,"filas":len(valores)},201)
            return self.json({"error":"Ruta no encontrada"},404)
        except (ValueError,json.JSONDecodeError,sqlite3.Error) as error:self.json({"error":str(error)},400)
if __name__=="__main__":
    erp.init();print("Panel RA3: http://127.0.0.1:8090/panel.html");ThreadingHTTPServer(("127.0.0.1",8090),App).serve_forever()
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
