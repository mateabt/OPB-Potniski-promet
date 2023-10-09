
# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import csv

def ustvari_tabelo():
    cur.execute("""
        CREATE TABLE cena (
            id INTEGER REFERENCES vlak(st_vlaka)
                ON DELETE CASCADE,
            cena_enosmerne REAL,
            cena_povratne REAL,
            PRIMARY KEY(id)
            );
    """)
    conn.commit()

def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE cena;
    """)
    conn.commit()

def uvozi_podatke():
    with open("podatki/cena.csv", encoding="utf-8", errors='ignore') as f:
        rd = csv.reader(f)
        next(rd)  # izpusti naslovno vrstico
        for r in rd:
            id = int(r[0])  
            cena_enosmerne = float(r[1])
            cena_povratne = float(r[2])

            cur.execute(
                """
                INSERT INTO cena
                (id, cena_enosmerne, cena_povratne)
                VALUES (%s, %s, %s)
                """,
                (id, cena_enosmerne, cena_povratne), 
            )

            print(
                "Uvožen vlak z ID-jem %s ki ima ceno enosmerne %s ,povratne %s"
                % (id, cena_enosmerne, cena_povratne)
            )
    conn.commit()




conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

#pobrisi_tabelo()
#ustvari_tabelo()
#uvozi_podatke()