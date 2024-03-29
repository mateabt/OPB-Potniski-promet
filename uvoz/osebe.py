# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import csv
import hashlib

def ustvari_tabelo():
    cur.execute("""
    CREATE TABLE oseba (
        uporabnisko_ime TEXT PRIMARY KEY,
        ime TEXT NOT NULL,
        priimek TEXT NOT NULL,
        datum_rojstva DATE NOT NULL,
        drzavljanstvo TEXT REFERENCES drzava(kratica),
        geslo TEXT NOT NULL,
        clanstvo INTEGER REFERENCES skupina(id_skupine),
        st_vlaka INTEGER REFERENCES vlak(st_vlaka)
    );
    """) 
    conn.commit()

def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE oseba;
    """)
    conn.commit()

def uvozi_podatke():
    with open("podatki/oseba.csv", encoding="utf-8", errors='ignore') as f:
        rd = csv.reader(f)
        next(rd) # izpusti naslovno vrstico
        for r in rd:
            r = [None if x == '' else x for x in r]
            cur.execute("""
                INSERT INTO oseba
                (uporabnisko_ime,ime,priimek,datum_rojstva,drzavljanstvo,geslo,clanstvo,st_vlaka)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, r)
            print("Uvožena oseba %s z uporabniškim imenom %s" % (r[1], r[0]))
    conn.commit()


conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

#pobrisi_tabelo()
#ustvari_tabelo()
#uvozi_podatke()

def hashGesla(s):
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

def zgosti():
    cur.execute("SELECT geslo FROM oseba;")
    gesla = cur.fetchall()

    for geslo in gesla:
        geslo_str = geslo[0]  # Izvlece geslo 
        geslo_hashed = hashGesla(geslo_str)
        cur.execute("UPDATE oseba SET geslo=%s WHERE geslo=%s", (geslo_hashed, geslo_str))
        conn.commit()
        print('Password hashed and updated')
        
zgosti()