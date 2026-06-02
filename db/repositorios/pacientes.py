from db.conexion import Conexion


class PacientesRepo:
    """CRUD para la tabla pacientes."""

    @staticmethod
    def crear_o_obtener(nombre, edad=None, fecha_estudio=None):
        """
        Si el paciente ya existe (mismo nombre + edad), devuelve su id.
        Si no existe, lo crea y devuelve el nuevo id.
        """
        cur = Conexion.cursor()
        cur.execute(
            "SELECT id FROM pacientes WHERE nombre = %s AND edad = %s",
            (nombre, edad)
        )
        existente = cur.fetchone()
        if existente:
            cur.close()
            return existente["id"]

        cur.execute(
            "INSERT INTO pacientes (nombre, edad, fecha_estudio) VALUES (%s, %s, %s)",
            (nombre, edad, fecha_estudio)
        )
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_todos():
        cur = Conexion.cursor()
        cur.execute("SELECT * FROM pacientes ORDER BY nombre")
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def obtener_por_id(paciente_id):
        cur = Conexion.cursor()
        cur.execute("SELECT * FROM pacientes WHERE id = %s", (paciente_id,))
        resultado = cur.fetchone()
        cur.close()
        return resultado

    @staticmethod
    def buscar(texto):
        sql = "SELECT * FROM pacientes WHERE nombre LIKE %s ORDER BY nombre"
        cur = Conexion.cursor()
        cur.execute(sql, (f"%{texto}%",))
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def eliminar(paciente_id):
        cur = Conexion.cursor()
        cur.execute("DELETE FROM pacientes WHERE id = %s", (paciente_id,))
        cur.close()