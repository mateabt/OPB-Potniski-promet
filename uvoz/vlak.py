# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import csv

def ustvari_tabelo():
    cur.execute("""
        CREATE TABLE vlak (
            st_vlaka INTEGER PRIMARY KEY,
            st_prestopi NUMERIC 
            id_mesta_zacetek NUMERIC REFERENCES mesto(id),
            id_mesta_konec NUMERIC REFERENCES mesto(id),
            );
    """)
    conn.commit()

def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE vlak;
    """)
    conn.commit()

def uvozi_podatke():
    with open("podatki/vlak.csv", encoding="utf-8", errors='ignore') as f:
        rd = csv.reader(f)
        next(rd) # izpusti naslovno vrstico
        for r in rd:
            cur.execute("""
                INSERT INTO vlak
                (st_vlaka,st_prestopi,id_mesta_zacetek,id_mesta_konec)
                VALUES (%s, %s, %s,%s)
                """, r)
            # rid, = cur.fetchone()
            print("Uvožen vlak z ID-jem %s" % (r[0]))
    conn.commit()


conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

#pobrisi_tabelo()
ustvari_tabelo()
#uvozi_podatke()