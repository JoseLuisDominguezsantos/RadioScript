from db.conexion import Conexion


class VocabularioRepo:
    """CRUD para la tabla vocabulario — términos médicos que la IA debe reconocer."""

    @staticmethod
    def crear(termino, descripcion="", correccion_whisper=""):
        """
        termino           — palabra médica correcta (ej: HILIAR)
        descripcion       — qué significa o cuándo se usa
        correccion_whisper — cómo Whisper suele transcribirla mal (ej: iliar)
        """
        sql = """
            INSERT INTO vocabulario (termino, descripcion, correccion_whisper)
            VALUES (%s, %s, %s)
        """
        cur = Conexion.cursor()
        cur.execute(sql, (termino, descripcion, correccion_whisper))
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_todos():
        cur = Conexion.cursor()
        cur.execute("SELECT * FROM vocabulario ORDER BY termino")
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def buscar(texto):
        sql = """
            SELECT * FROM vocabulario
            WHERE termino LIKE %s OR correccion_whisper LIKE %s OR descripcion LIKE %s
            ORDER BY termino
        """
        like = f"%{texto}%"
        cur = Conexion.cursor()
        cur.execute(sql, (like, like, like))
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def obtener_correcciones():
        """Devuelve solo los términos que tienen corrección de Whisper — para el preprocesador."""
        sql = """
            SELECT termino, correccion_whisper FROM vocabulario
            WHERE correccion_whisper IS NOT NULL AND correccion_whisper != ''
        """
        cur = Conexion.cursor()
        cur.execute(sql)
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def actualizar(vocab_id, termino, descripcion="", correccion_whisper=""):
        sql = """
            UPDATE vocabulario
            SET termino = %s, descripcion = %s, correccion_whisper = %s
            WHERE id = %s
        """
        cur = Conexion.cursor()
        cur.execute(sql, (termino, descripcion, correccion_whisper, vocab_id))
        cur.close()

    @staticmethod
    def eliminar(vocab_id):
        cur = Conexion.cursor()
        cur.execute("DELETE FROM vocabulario WHERE id = %s", (vocab_id,))
        cur.close()