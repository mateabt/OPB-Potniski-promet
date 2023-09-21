#!/usr/bin/python
# -*- encoding: utf-8 -*-

# uvozimo bottle.py
from bottleext import get, post, run, request, template, redirect, static_file, url, response

# uvozimo ustrezne podatke za povezavo
from uvoz import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import os
import hashlib

# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

# odkomentiraj, če želiš sporočila o napakah
debug = True

skrivnost = "rODX3ulHw3ZYRdbIVcp1IfJTDn8iQTH6TFaNBgrSkjIulr"

def nastaviSporocilo(sporocilo = None):
    # global napakaSporocilo
    staro = request.get_cookie("sporocilo", secret=skrivnost)
#    if sporocilo is None:
#        bottle.Response.delete_cookie(key='sporocilo', path='/', secret=skrivnost)
#    else:
#        bottle.Response.set_cookie(key='sporocilo', value=sporocilo, path="/", secret=skrivnost)
    return staro 

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

##########################
# začetna stran
@get('/')
def hello():
    return template('zacetna_stran.html')

##########################
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
    if len(geslo) < 4:
        nastaviSporocilo('Geslo mora imeti vsaj 4 znake.') 
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
    redirect(url('hello'))

##################################
# podatki prijavljenega

@get('/podatki_prijavljenega')
def podatki_prijavljenega():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    uporabnisko_ime = request.get_cookie("uporabnisko_ime", secret=skrivnost)
    cur.execute("""SELECT uporabnisko_ime,ime,priimek,datum_rojstva,ime_drzave,geslo,ime_skupine,oseba.st_vlaka
                FROM oseba
                LEFT JOIN drzava ON oseba.drzavljanstvo=drzava.kratica
                LEFT JOIN skupina ON oseba.clanstvo=skupina.id_skupine
                LEFT JOIN vlak ON oseba.st_vlaka=vlak.st_vlaka
            
                WHERE uporabnisko_ime=%s;""",[uporabnisko_ime])
    return template('podatki_prijavljenega.html', oseba=cur)
#############################################################
# clanstvo
def najdi_id_skupine():
    cur.execute("SELECT id_skupine,ime_skupine FROM skupina;")
    return cur.fetchall()

@get('/uredi_clanstvo')
def uredi_clanstvo():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('uredi_clanstvo.html', id_skupine='', skupine=najdi_id_skupine())

@post('/uredi_clanstvo')
def uredi_clanstvo_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    uporabnisko_ime = request.get_cookie("uporabnisko_ime", secret=skrivnost)
    id_skupine = request.forms.id_skupine
    try:
        cur.execute("UPDATE oseba SET clanstvo=%s WHERE uporabnisko_ime=%s",
                    (id_skupine, uporabnisko_ime))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('uredi_clanstvo.html', id_skupine=id_skupine,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('podatki_prijavljenega'))

def najdi_kratico():
    cur.execute("SELECT kratica,ime_drzave FROM drzava;")
    return cur.fetchall()
###################################################
# drzavljanstvo
@get('/uredi_drzavljanstvo')
def uredi_drzavljanstvo():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('uredi_drzavljanstvo.html', kratica='', drzave=najdi_kratico())

@post('/uredi_drzavljanstvo')
def uredi_drzavljanstvo_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    uporabnisko_ime = request.get_cookie("uporabnisko_ime", secret=skrivnost)
    drzavljanstvo = request.forms.drzavljanstvo
    try:
        cur.execute("UPDATE oseba SET drzavljanstvo=%s WHERE uporabnisko_ime=%s",
                    (drzavljanstvo, uporabnisko_ime))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('uredi_drzavljanstvo.html', drzavljanstvo=drzavljanstvo,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('podatki_prijavljenega'))
    
    ########################
    #vlak
def najdi_vlak():
    cur.execute("SELECT st_vlaka,st_prestopi,id_mesta_zacetek,id_mesta_konec FROM vlak;")
    return cur.fetchall()
  
    
    
@get('/uredi_vlak')
def uredi_vlak():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('uredi_vlak.html', vlak=najdi_vlak())

@post('/uredi_vlak')
def uredi_vlak_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    uporabnisko_ime = request.get_cookie("uporabnisko_ime", secret=skrivnost)
    st_vlaka = request.forms.st_vlaka
    try:
        cur.execute("UPDATE oseba SET st_vlaka=%s WHERE uporabnisko_ime=%s",
                    (st_vlaka, uporabnisko_ime))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('uredi_vlak.html', st_vlaka=st_vlaka,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('podatki_prijavljenega'))

def najdi_id_mesta():
    cur.execute("SELECT id, ime_mesta FROM mesto;")
    return cur.fetchall()

@get('/dodaj_izlet')
def dodaj_izlet():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('dodaj_vlak.html', st_vlaka='', st_prestopi='', id_mesta_zacetek=najdi_id_mesta(), id_mesta_konec=najdi_id_mesta(), napaka=None)

@post('/dodaj_vlak')
def dodaj_vlak_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    st_vlaka = request.forms.st_vlaka
    st_prestopi = request.forms.st_prestopi
    id_mesta_zacetek = request.forms.id_mesta_zacetek
    id_mesta_konec = request.forms.id_mesta_konec
    try:
        cur.execute("INSERT INTO vlak (st_vlaka, st_prestopi, id_mesta_zacetek, id_mesta_konec) VALUES (%s, %s, %s, %s)",
                    (st_vlaka, st_prestopi, id_mesta_zacetek, id_mesta_konec))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('dodaj_vlak.html', st_vlaka=st_vlaka, st_prestopi=st_prestopi, id_mesta_zacetek=id_mesta_zacetek,id_mesta_konec=id_mesta_konec,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('vlak'))    
    
    
   

##################################
# osebe

@get('/osebe')
def osebe():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    cur.execute("""SELECT uporabnisko_ime,ime,priimek,datum_rojstva,drzavljanstvo,clanstvo,st_vlaka
                FROM oseba ORDER BY priimek, ime""")
    return template('osebe.html', oseba=cur)


######################################################################
# Glavni program

######################################################################



# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
