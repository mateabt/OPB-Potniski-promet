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
###################################
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
#############################################################
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
###################################################
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
    
 #####################################################################################   
    #osebe 
######################################################################################
@get('/osebe')
def osebe():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    cur.execute("""SELECT uporabnisko_ime,ime,priimek,datum_rojstva,drzavljanstvo,clanstvo,st_vlaka
                FROM oseba ORDER BY priimek, ime""")
    return template('osebe.html', oseba=cur)

######################################
#vlaki
######################################
@get('/vlak')
def vlak():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    cur.execute("""SELECT vlak.st_vlaka, vlak.st_prestopi, 
           zacetek.ime_mesta AS ime_mesta_zacetek, 
           konec.ime_mesta AS ime_mesta_konec, 
           vlak.cas_odhoda, 
           vlak.cas_prihoda
        FROM vlak
        JOIN mesto AS zacetek ON vlak.id_mesta_zacetek = zacetek.id
        JOIN mesto AS konec ON vlak.id_mesta_konec = konec.id;""")
    return template('vlak.html', vlak=cur)

    
#########################
#skupine
############################
@get('/skupine')
def skupine():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    cur.execute("SELECT * FROM skupina ORDER BY id_skupine;")
    return template('skupine.html', skupine=cur)

@get('/dodaj_skupino')
def dodaj_skupino():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('dodaj_skupino.html', id_skupine='', ime_skupine='', napaka=None)

@post('/dodaj_skupino')
def dodaj_skupino_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    id_skupine = request.forms.id_skupine
    ime_skupine = request.forms.ime_skupine
    try:
        cur.execute("INSERT INTO skupina (id_skupine, ime_skupine) VALUES (%s, %s)",
                    (id_skupine, ime_skupine))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('dodaj_skupino.html', id_skupine=id_skupine, ime_skupine=ime_skupine,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('skupine'))

@get('/clani_skupine/<x:int>/')
def clani_skupine(x):
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    cur.execute("""SELECT uporabnisko_ime,ime,priimek,datum_rojstva,drzavljanstvo,clanstvo,st_vlaka
                FROM oseba WHERE clanstvo = %s""", [x])
    return template('clani_skupine.html', x=x, oseba=cur)

def najdi_id_skupine():
    cur.execute("SELECT * FROM skupina;")
    return cur.fetchall()

@get('/uredi_skupino')
def uredi_skupino():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('uredi_skupino.html', id_skupine='', ime_skupine='', napaka=None, skupine = najdi_id_skupine())

@post('/uredi_skupino')
def uredi_skupino_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    id_skupine = request.forms.id_skupine
    ime_skupine = request.forms.ime_skupine
    try:
        cur.execute("UPDATE skupina SET ime_skupine=%s WHERE id_skupine=%s",
                    (ime_skupine, id_skupine))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('uredi_skupino.html', id_skupine=id_skupine, ime_skupine=ime_skupine,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('skupine'))

@get('/izbrisi_skupino')
def izbrisi_skupino():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('izbrisi_skupino.html', id_skupine='', napaka=None, skupine = najdi_id_skupine())

@post('/izbrisi_skupino')
def izbrisi_skupino_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    id_skupine = request.forms.id_skupine
    try:
        cur.execute("UPDATE oseba SET clanstvo = NULL WHERE clanstvo = %s", [id_skupine])
        cur.execute("DELETE FROM skupina WHERE id_skupine= %s", [id_skupine])
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('izbrisi_skupino.html', id_skupine=id_skupine,
                        napaka='Zgodila se je napaka: %s' % ex, skupine=najdi_id_skupine())
    redirect(url('skupine'))
#######################
#vlaki
########################
def najdi_vlak():
    cur.execute("SELECT st_vlaka,st_prestopi,id_mesta_zacetek,id_mesta_konec,cas_odhoda,cas_prihoda FROM vlak;")
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

@get('/dodaj_vlak')
def dodaj_vlak():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    return template('dodaj_vlak.html', st_vlaka='', st_prestopi='', id_mesta_zacetek=najdi_id_mesta(),id_mesta_konec=najdi_id_mesta(),cas_odhoda='',cas_prihoda='', napaka=None)

@post('/dodaj_vlak')
def dodaj_vlak_post():
    uporabnik = preveriUporabnika()
    if uporabnik is None: 
        return
    st_vlaka = request.forms.st_vlaka
    st_prestopi = request.forms.st_prestopi
    id_mesta_zacetek = request.forms.id_mesta_zacetek
    id_mesta_konec=request.forms.id_mesta_konec
    cas_odhoda=request.forms.cas_odhoda
    cas_prihoda=request.forms.cas_prihoda
    try:
        cur.execute("INSERT INTO vlak (st_vlaka, st_prestopi, id_mesta_zacetek,id_mesta_konec,cas_odhoda,cas_prihoda) VALUES (%s, %s, %s, %s,%s,%s)",
                    (st_vlaka, st_prestopi, id_mesta_zacetek,id_mesta_konec,cas_odhoda,cas_prihoda))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('dodaj_vlak.html', st_vlaka=st_vlaka, st_prestopi=st_prestopi, id_mesta_zacetek=id_mesta_zacetek, id_mesta_konec=id_mesta_konec,cas_odhoda=cas_odhoda,cas_prihoda=cas_prihoda,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('vlak'))

#######################
#cena
##################
@get('/cena')
def cena():
    uporabnik = preveriUporabnika()
    if uporabnik is None:
        return

    max_price_enosmerna = request.query.get('max_price_enosmerna', None)  # max za enosmerne cene
    max_price_povratna = request.query.get('max_price_povratna', None)  # max za povratne cene

    # Convert the filter parameters to valid numeric values or None
    max_price_enosmerna = float(max_price_enosmerna) if max_price_enosmerna else None
    max_price_povratna = float(max_price_povratna) if max_price_povratna else None

    # Define placeholders for SQL query and parameters
    sql = """
        SELECT id, cena_enosmerne, cena_povratne
        FROM cena
        WHERE (%s IS NULL OR cena_enosmerne <= %s)
        AND (%s IS NULL OR cena_povratne <= %s)
    """
    params = (max_price_enosmerna, max_price_enosmerna, max_price_povratna, max_price_povratna)

    # Execute the SQL query with placeholders and parameters
    cur.execute(sql, params)

    return template('cena.html', cena=cur)












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
