from db.conexion import Conexion


class TranscripcionesRepo:
    """CRUD para transcripciones e informes generados."""

    @staticmethod
    def guardar_transcripcion(audio_path, texto, paciente_id=None, duracion_seg=None):
        sql = """
            INSERT INTO transcripciones (audio_path, texto, paciente_id, duracion_seg)
            VALUES (%s, %s, %s, %s)
        """
        cur = Conexion.cursor()
        cur.execute(sql, (audio_path, texto, paciente_id, duracion_seg))
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_por_audio(audio_path):
        cur = Conexion.cursor()
        cur.execute(
            "SELECT * FROM transcripciones WHERE audio_path = %s ORDER BY id DESC LIMIT 1",
            (audio_path,)
        )
        resultado = cur.fetchone()
        cur.close()
        return resultado

    @staticmethod
    def obtener_todas():
        sql = """
            SELECT t.*, p.nombre AS paciente_nombre
            FROM transcripciones t
            LEFT JOIN pacientes p ON t.paciente_id = p.id
            ORDER BY t.id DESC
        """
        cur = Conexion.cursor()
        cur.execute(sql)
        resultado = cur.fetchall()
        cur.close()
        return resultado


class InformesRepo:
    """CRUD para informes radiológicos generados."""

    @staticmethod
    def guardar(transcripcion_id, paciente_id, contenido, plantilla_id=None):
        # Cambiamos 'contenido' por 'texto_completo' en el INSERT
        sql = """
            INSERT INTO informes (transcripcion_id, paciente_id, texto_completo, plantilla_id)
            VALUES (%s, %s, %s, %s)
        """
        cur = Conexion.cursor()
        # Mantenemos la variable 'contenido' en la tupla porque es el nombre del parámetro en Python
        cur.execute(sql, (transcripcion_id, paciente_id, contenido, plantilla_id))
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_por_transcripcion(transcripcion_id):
        cur = Conexion.cursor()
        cur.execute(
            "SELECT * FROM informes WHERE transcripcion_id = %s ORDER BY id DESC LIMIT 1",
            (transcripcion_id,)
        )
        resultado = cur.fetchone()
        cur.close()
        return resultado

    @staticmethod
    def obtener_todos():
        sql = """
            SELECT i.*, p.nombre AS paciente_nombre
            FROM informes i
            LEFT JOIN pacientes p ON i.paciente_id = p.id
            ORDER BY i.id DESC
        """
        cur = Conexion.cursor()
        cur.execute(sql)
        resultado = cur.fetchall()
        cur.close()
        return resultado

    @staticmethod
    def guardar_ejemplo_ia(transcripcion_texto, informe_texto, validado=False):
        """Guarda el par transcripción→informe como ejemplo de aprendizaje para la IA."""
        sql = """
            INSERT INTO ejemplos_ia (transcripcion_texto, informe_texto, validado)
            VALUES (%s, %s, %s)
        """
        cur = Conexion.cursor()
        cur.execute(sql, (transcripcion_texto, informe_texto, validado))
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def obtener_ejemplos_validados(limite=20):
        """Devuelve los últimos N ejemplos validados para usar como contexto en Ollama."""
        sql = """
            SELECT transcripcion_texto, informe_texto
            FROM ejemplos_ia
            WHERE validado = 1
            ORDER BY id DESC
            LIMIT %s
        """
        cur = Conexion.cursor()
        cur.execute(sql, (limite,))
        resultado = cur.fetchall()
        cur.close()
        return resultado