from db.conexion import Conexion


class HallazgosRepo:
    """CRUD para la tabla hallazgos."""

    @staticmethod
    def crear(categoria, frase, variantes="", tipo_estudio_id=None):
        sql = """
            INSERT INTO hallazgos (categoria, frase, variantes, tipo_estudio_id)
            VALUES (%s, %s, %s, %s)
        """
        cur = Conexion.cursor()
        cur.execute(sql, (categoria, frase, variantes, tipo_estudio_id))
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_todos():
        sql = """
            SELECT h.*, t.nombre AS tipo_estudio
            FROM hallazgos h
            LEFT JOIN tipos_estudio t ON h.tipo_estudio_id = t.id
            ORDER BY h.categoria, h.frase
        """
        cur = Conexion.cursor()
        cur.execute(sql)
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def obtener_por_categoria(categoria):
        sql = """
            SELECT * FROM hallazgos
            WHERE categoria = %s
            ORDER BY frase
        """
        cur = Conexion.cursor()
        cur.execute(sql, (categoria,))
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def obtener_categorias():
        cur = Conexion.cursor()
        cur.execute("SELECT DISTINCT categoria FROM hallazgos ORDER BY categoria")
        resultado = [row["categoria"] for row in cur.fetchall()]
        cur.close()
        return resultado

    @staticmethod
    def buscar(texto):
        sql = """
            SELECT * FROM hallazgos
            WHERE frase LIKE %s OR variantes LIKE %s
            ORDER BY categoria, frase
        """
        like = f"%{texto}%"
        cur = Conexion.cursor()
        cur.execute(sql, (like, like))
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def actualizar(hallazgo_id, categoria, frase, variantes=""):
        sql = """
            UPDATE hallazgos
            SET categoria = %s, frase = %s, variantes = %s
            WHERE id = %s
        """
        cur = Conexion.cursor()
        cur.execute(sql, (categoria, frase, variantes, hallazgo_id))
        cur.close()

    @staticmethod
    def eliminar(hallazgo_id):
        cur = Conexion.cursor()
        cur.execute("DELETE FROM hallazgos WHERE id = %s", (hallazgo_id,))
        cur.close()