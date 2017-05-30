import dbconfig as cfg
import MySQLdb as sql
import common as cm

## Basic MySQL database helper functions
## Handles connection configuration, and system wide errors


class Database(object):
    # Execute an SQL query
    def execQuery(self, strCmd, args=()):
        conn = sql.connect(host=cfg.mysql["host"], user=cfg.mysql["user"], passwd=cfg.mysql["passwd"], db=cfg.mysql["db"], use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        try:
            cursor.execute(strCmd, args)                
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except MySQLdb.Error, e:
            self.throwSQLError(e, conn, cursor)


    # Execute an SQL insert/update command
    def execUpdate(self, strCmd, args=()):
        strCmd = strCmd.strip()
        strCommitCmd = ""
        if(not(strCmd.lower().startswith("begin;"))):
            strCommitCmd = "BEGIN; "

        strCommitCmd += strCmd

        if(not(strCmd.lower().endswith(";"))):
            strCommitCmd += ";"

        if(not(strCmd.lower().endswith("commit;"))):
            strCommitCmd += " COMMIT;"
        
        return self.execQuery(strCommitCmd, args)


    # Execute an SQL stored procedure
    def execProc(self, strProc, args=()):
        conn = sql.connect(host=cfg.mysql["host"], user=cfg.mysql["user"], passwd=cfg.mysql["passwd"], db=cfg.mysql["db"], use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        try:
            results = cursor.callproc(strProc, args)
            cursor.close()
            conn.close()
            return results
        except sql.Error, e:
            self.throwSQLError(e, conn, cursor)


    # Basic error handling
    # Logs system errors to database
    def throwSQLError(self, e, conn, cursor):
        strError = "SQL Error %d:  %s" % (e.args[0], e.args[1])
        results = cursor.callproc("sp_systemerror", (strError,))
        cursor.close()
        conn.close()
        