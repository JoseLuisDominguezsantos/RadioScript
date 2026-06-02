from db.conexion import Conexion


class PlantillasRepo:
    """CRUD para la tabla plantillas."""

    @staticmethod
    def crear(nombre, tipo_estudio_id, contenido_base, descripcion=""):
        sql = """
            INSERT INTO plantillas (nombre, tipo_estudio_id, contenido_base, descripcion)
            VALUES (%s, %s, %s, %s)
        """
        cur = Conexion.cursor()
        cur.execute(sql, (nombre, tipo_estudio_id, contenido_base, descripcion))
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_todos():
        sql = """
            SELECT p.*, t.nombre AS tipo_estudio
            FROM plantillas p
            LEFT JOIN tipos_estudio t ON p.tipo_estudio_id = t.id
            ORDER BY p.nombre
        """
        cur = Conexion.cursor()
        cur.execute(sql)
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def obtener_por_id(plantilla_id):
        sql = """
            SELECT p.*, t.nombre AS tipo_estudio
            FROM plantillas p
            LEFT JOIN tipos_estudio t ON p.tipo_estudio_id = t.id
            WHERE p.id = %s
        """
        cur = Conexion.cursor()
        cur.execute(sql, (plantilla_id,))
        resultado = cur.fetchone()
        cur.close()
        return resultado

    @staticmethod
    def obtener_por_tipo(tipo_estudio_id):
        sql = """
            SELECT * FROM plantillas
            WHERE tipo_estudio_id = %s
            ORDER BY nombre
        """
        cur = Conexion.cursor()
        cur.execute(sql, (tipo_estudio_id,))
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def actualizar(plantilla_id, nombre, contenido_base, descripcion=""):
        sql = """
            UPDATE plantillas
            SET nombre = %s, contenido_base = %s, descripcion = %s
            WHERE id = %s
        """
        cur = Conexion.cursor()
        cur.execute(sql, (nombre, contenido_base, descripcion, plantilla_id))
        cur.close()

    @staticmethod
    def eliminar(plantilla_id):
        cur = Conexion.cursor()
        cur.execute("DELETE FROM plantillas WHERE id = %s", (plantilla_id,))
        cur.close()