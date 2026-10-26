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
