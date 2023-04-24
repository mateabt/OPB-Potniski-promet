#Bottle
from bottle import *
from bottleext import *
# avtorizacija za priklop na bazo
from auth_public import *
# za gesla
import hashlib
#za trenutni cas
from datetime import date    
# za priklop na bazo
import psycopg2, psycopg2.extensions, psycopg2.extras
#znebimo problema s sumniki
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

import os
# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

# PRIKLOP NA BAZO
conn = psycopg2.connect(database=db, host=host, user=user, password=password, port=DB_PORT)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

# sporočila o napakah
debug(True)  # za izpise pri razvoju

# params
static_dir = "./static"

skrivnost = 'laqwXUtKfHTp1SSpnkSg7VbsJtCgYS89Qnbhjv'



# začetna stran
@get('/')
def index():
        redirect(url('uporabnik_get'))
    return template('zacetna_stran.html', znacka=znacka)

######################################################################
# Glavni program

# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
