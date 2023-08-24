#!/usr/bin/python
# -*- encoding: utf-8 -*-

# uvozimo bottle.py
from bottleext import *

# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) 
# se znebimo problemov s šumniki

import os
import hashlib
from datetime import date, timedelta

skrivnost="NaJsKrIvNoStNeJsAsKrIvNoSt"

# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

####################################################
debug(True)

def nastaviSporocilo(sporocilo = None):
    # global napakaSporocilo
    staro = request.get_cookie("sporocilo", secret=skrivnost)
#    if sporocilo is None:
#        bottle.Response.delete_cookie(key='sporocilo', path='/', secret=skrivnost)
#    else:
#        bottle.Response.set_cookie(key='sporocilo', value=sporocilo, path="/", secret=skrivnost)
    return staro 
######################################################3


# mapa za statične vire
static_dir = "./static"

# streženje statičnih datotek
@route("/static/<filename:path>")
def static(filename):
    return static_file(filename, root=static_dir)


def preveriUporabnika(): 
    uporabnisko_ime = request.get_cookie("uporabnisko_ime", secret=skrivnost)
    if uporabnisko_ime:
       # cur = baza.cursor()    
        uporabnik = None
        try: 
            cur.execute("SELECT * FROM oseba WHERE uporabnisko_ime = %s", [uporabnisko_ime])
            uporabnik = cur.fetchone()
        except:
            uporabnik = None
        if uporabnik: 
            return uporabnik
    redirect(url('prijava'))


#########################################################

@get('/')
def index():
    return template('zacetna.html', napaka=None)


@get('/projekt')
def projekt():
    return template("projekt.html", napaka=None)


# prijava
@get('/prijava')
def prijava():
    return template('zacetna_stran.html',napaka=None)


######################################################################
# Glavni program

######################################################################


# priklopimo se na bazo
baza = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
