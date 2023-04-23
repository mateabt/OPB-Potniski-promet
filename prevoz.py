#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import bottle
from bottle import *
import hashlib
import auth_public as auth
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
from funkcije import * 
import sqlite3
from datetime import datetime
from bottle import get, static_file

######################################################################

conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password) ########
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)                          #GLOBALNO
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)                                      ############              

secret = "kjbjkvjh675aosfh1309uhn0f1j1f9hj"
#####################################################################################

static_dir = "./static"
# Static Routes
"Da lahko bere css in javascript datoteke iz mape static"
@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return bottle.static_file(filename, root=static_dir)

######################################################################
"""PRVA STRAN"""

@route("/")
def prva_stran():
	"""Prva stran."""

	return bottle.template("zacetna.html", napaka=False) 

######################################################################


######################################################################
# Glavni program

# priklopimo se na bazo
conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
