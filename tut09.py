import os, os.path
import random
import sqlite3
import mariadb
import string
import time
from dotenv import dotenv_values

import cherrypy
cherrypy.config.update({'server.socket_host': '192.168.1.191', 'server.socket_port': 8099})

DB_STRING = "my.db"

secrets=dotenv_values(".env")

try:
    mariadbconn = mariadb.connect(
        user=secrets["user"],
        password=secrets["password"],
        host=secrets["host"],
        port=int(secrets["port"]),
        database=secrets["database"]
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

mariadbcur = mariadbconn.cursor()

try:
    test = mariadbcur.execute("SELECT session_id FROM user_string;")
except:
    print("Tabela user_string nie istnieje")
    print("Tworzę")
    mariadbcur.execute("CREATE TABLE `python_test`.`user_string` (`session_id` TEXT NOT NULL , `value` TEXT NOT NULL ) ENGINE = InnoDB;")

# mariadbcur.execute("INSERT INTO user_string (session_id, value) VALUES (?, ?)", ("Maria", "db"))
# mariadbconn.commit()

class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return open('index.html')

@cherrypy.expose
class StringGeneratorWebService(object):

    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        with mariadbconn.cursor() as c:
            cherrypy.session['ts'] = time.time()
            r = c.execute("SELECT value FROM user_string WHERE session_id=?",
                          [cherrypy.session.id])
        mariadbconn.commit()
        return r.fetchone()

    def POST(self, length=8):
        some_string = ''.join(random.sample(string.hexdigits, int(length)))
        with mariadbconn.cursor() as c:
            cherrypy.session['ts'] = time.time()
            c.execute("INSERT INTO user_string (session_id, value) VALUES (?, ?)",
                      [cherrypy.session.id, some_string])
        mariadbconn.commit()
        return some_string

    def PUT(self, another_string):
        with mariadbconn.cursor() as c:
            cherrypy.session['ts'] = time.time()
            c.execute("UPDATE user_string SET value=? WHERE session_id=?",
                      [another_string, cherrypy.session.id])
        mariadbconn.commit()

    def DELETE(self):
        cherrypy.session.pop('ts', None)
        with mariadbconn.cursor() as c:
            c.execute("DELETE FROM user_string WHERE session_id=?",
                      [cherrypy.session.id])
        mariadbconn.commit()


# def setup_database():
#     """
#     Create the `user_string` table in the database
#     on server startup
#     """
#     with sqlite3.connect(DB_STRING) as con:
#         con.execute("CREATE TABLE user_string (session_id, value)")


# def cleanup_database():
#     """
#     Destroy the `user_string` table from the database
#     on server shutdown.
#     """
#     with sqlite3.connect(DB_STRING) as con:
#         con.execute("DROP TABLE user_string")


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/generator': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }

    # cherrypy.engine.subscribe('start', setup_database)
    # cherrypy.engine.subscribe('stop', cleanup_database)

    webapp = StringGenerator()
    webapp.generator = StringGeneratorWebService()
    cherrypy.quickstart(webapp, '/', conf)