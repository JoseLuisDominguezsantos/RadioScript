import mysql.connector
from mysql.connector import Error
import os

# Configuración de la conexión
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "radioscript_user",
    "password": "RadioScript2024#",
    "database": "radioscript",
    "charset":  "utf8mb4",
    "autocommit": True,
}

class Conexion:
    _instancia = None  # Patrón Singleton — una sola conexión activa

    @classmethod
    def obtener(cls):
        """Devuelve la conexión activa, reconectando si es necesario."""
        if cls._instancia is None or not cls._instancia.is_connected():
            cls._instancia = cls._conectar()
        return cls._instancia

    @classmethod
    def _conectar(cls):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            print("[DB] Conexión establecida con MySQL")
            return conn
        except Error as e:
            print(f"[DB] Error al conectar: {e}")
            raise

    @classmethod
    def cursor(cls, dictionary=True):
        """Devuelve un cursor listo para usar. dictionary=True retorna filas como dicts."""
        conn = cls.obtener()
        return conn.cursor(dictionary=dictionary)

    @classmethod
    def cerrar(cls):
        if cls._instancia and cls._instancia.is_connected():
            cls._instancia.close()
            cls._instancia = None
            print("[DB] Conexión cerrada")


def probar_conexion():
    """Prueba rápida — ejecutar directamente este archivo para verificar."""
    try:
        cur = Conexion.cursor()
        cur.execute("SHOW TABLES;")
        tablas = [list(row.values())[0] for row in cur.fetchall()]
        print(f"[DB] Tablas encontradas ({len(tablas)}): {', '.join(tablas)}")
        cur.close()
        Conexion.cerrar()
    except Exception as e:
        print(f"[DB] Fallo en prueba: {e}")


if __name__ == "__main__":
    probar_conexion()