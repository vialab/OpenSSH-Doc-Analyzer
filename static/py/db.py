#import dbconfig as cfg
import MySQLdb as sql
import common as cm
import os
from urllib.parse import urlparse


class Database(object):
    """ Basic MySQL database helper functions """

    conn = None
    session_open = False

    def __init__(self):
        self._connect()

    def _connect(self):
        env = os.environ.get("DEPLOY_ENV")
        connstr = os.environ.get("DATABASE_URL")
        if env is None or env == "PROD":
            if connstr is None:
                raise Exception("DATABASE_URL was not provided")
            url = urlparse(connstr)
            self.conn = sql.connect(    
                host=url.hostname,
                user=url.username,
                passwd=url.password,
                db=url.path[1:],
                charset="utf8mb4"
            )
        else:
            self.conn = sql.connect(
                host=cfg.mysql["host"],
                user=cfg.mysql["user"],
                passwd=cfg.mysql["passwd"],
                db=cfg.mysql["db"],
                charset="utf8mb4"
            )

    def _execute(self, sqlStmt, args=None, cursor=None, is_update=True):
        try:
            if not self.conn.open:
                self._connect()

            if cursor is None:
                cursor = self.conn.cursor()

            cursor.execute(sqlStmt, args)
        except (AttributeError, sql.OperationalError):
            self._connect()
            cursor = self.conn.cursor()
            cursor.execute(sqlStmt, args)
        try:
            if is_update:
                self.conn.commit()
        except Exception as e:
            print(e)
        return cursor

    def beginSession(self):
        """ Returns a cursor to be able to maintain a session """
        if self.session_open:
            raise Exception("A session already exists.")
        if not self.conn.open:
            self._connect()
        return self.conn.cursor()

    def execSessionQuery(
        self, cursor, strCmd, args=(), close_cursor=False, is_update=False
    ):
        """ Used to run a query on a specific cursor """
        r_cursor = self._execute(strCmd, args, cursor, is_update)
        results = []

        if r_cursor is not None:
            results = r_cursor.fetchall()

        if close_cursor:
            r_cursor.close()

        return results

    def execQuery(self, strCmd, args=(), is_update=False, to_dict=False):
        """ Execute an SQL query """
        results = self.execSessionQuery(None, strCmd, args, False, is_update)
        if to_dict:
            # make these results retrievable by id (assumes id is always first)
            new_results = {}
            for result in results:
                new_results[str(result[0])] = result[1:]
            return new_results
        return results

    def execUpdate(self, strCmd, args=()):
        """ Execute an SQL insert/update command """
        return self.execQuery(strCmd, args, is_update=True)

    def execProc(self, strProc, args=()):
        """ Execute an SQL stored procedure """
        cursor = None

        try:
            cursor = self.conn.cursor()
            cursor.callproc(strProc, args)
        except (AttributeError, sql.OperationalError):
            self._connect()

            cursor = self.conn.cursor()
            cursor.callproc(strProc, args)

        results = cursor.fetchall()
        cursor.close()

        return results

    def throwSQLError(self, e):
        """ Log system errors to database """
        strError = "SQL Error %d:  %s" % (e.args[0], e.args[1])
        results = cursor.callproc("sp_systemerror", (strError,))

    def __del__(self):
        if self.conn is not None:
            self.conn.close()
