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
@get('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static')

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
# začetna stran
@get('/')
def zacetna():
    return template('zacetna_stran.html')

# prijava, registracija, odjava

def hashGesla(s):
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

@get('/registracija')
def registracija_get():
    napaka = nastaviSporocilo()
    return template('registracija.html', napaka=napaka)

@post('/registracija')
def registracija_post():
    uporabnisko_ime = request.forms.uporabnisko_ime
    geslo = request.forms.geslo
    geslo2 = request.forms.geslo2
    ime = request.forms.ime
    priimek = request.forms.priimek
    datum_rojstva = request.forms.datum_rojstva
    if uporabnisko_ime is None or geslo is None or geslo2 is None:
        nastaviSporocilo('Registracija ni možna') 
        redirect(url('registracija_get'))
        return
    uporabnik = None
    try: 
        cur.execute("SELECT * FROM oseba WHERE uporabnisko_ime = %s", [uporabnisko_ime])
        uporabnik = cur.fetchone()
    except:
        uporabnik = None
    if uporabnik is not None:
        nastaviSporocilo('Registracija ni možna') 
        redirect(url('registracija_get'))
        return
    if len(geslo) < 3:
        nastaviSporocilo('Geslo mora imeti vsaj 3 znake.') 
        redirect(url('registracija_get'))
        return
    if geslo != geslo2:
        nastaviSporocilo('Gesli se ne ujemata.')
        redirect(url('registracija_get'))
        return
    zgostitev = hashGesla(geslo)
    cur.execute("""INSERT INTO oseba
                (uporabnisko_ime,ime,priimek,datum_rojstva,geslo)
                VALUES (%s, %s, %s, %s, %s)""", (uporabnisko_ime,ime,priimek,datum_rojstva, zgostitev))
    conn.commit()
    response.set_cookie('uporabnisko_ime', uporabnisko_ime, path='/', secret=skrivnost)
    redirect(url('podatki_prijavljenega'))


@get('/prijava')
def prijava_get():
    return template('prijava.html')

@post('/prijava')
def prijava_post():
    uporabnisko_ime = request.forms.uporabnisko_ime
    geslo = request.forms.geslo
    if uporabnisko_ime is None or geslo is None:
        nastaviSporocilo('Uporabniško ima in geslo morata biti neprazna') 
        redirect(url('prijava_get'))
        return
    hashBaza = None
    try: 
        cur.execute("SELECT geslo FROM oseba WHERE uporabnisko_ime = %s", [uporabnisko_ime])
        hashBaza, = cur.fetchone()
    except:
        hashBaza = None
    if hashBaza is None:
        nastaviSporocilo('Uporabniško geslo ali ime nista ustrezni') 
        redirect(url('prijava_get'))
        return
    if hashGesla(geslo) != hashBaza:
        nastaviSporocilo('Uporabniško geslo ali ime nista ustrezni') 
        redirect(url('prijava_get'))
        return
    response.set_cookie('uporabnisko_ime', uporabnisko_ime, secret=skrivnost)
    redirect(url('podatki_prijavljenega'))
    
@get('/odjava')
def odjava_get():
    response.delete_cookie(key='uporabnisko_ime')
    redirect(url('zacetna'))





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
