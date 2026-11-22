import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def conectar():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

if __name__ == "__main__":
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            for tabela in cur.fetchall():
                print(tabela[0])