


import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def conectar():
    driver = os.getenv("DB_DRIVER")
    servidor = os.getenv("DB_SERVER")
    base_datos = os.getenv("DB_NAME")

    cadena = (
        f"DRIVER={{{driver}}};"
        f"SERVER={servidor};"
        f"DATABASE={base_datos};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(cadena, timeout=5)
