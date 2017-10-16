import dbconfig as cfg
import MySQLdb as sql
import common as cm

class Database(object):
    """ Basic MySQL database helper functions """
    conn = None

    def __init__(self):
        self.conn = sql.connect(host=cfg.mysql["host"], user=cfg.mysql["user"], passwd=cfg.mysql["passwd"], db=cfg.mysql["db"], use_unicode=True, charset='utf8')

    def execQuery(self, strCmd, args=(), is_update=False):
        """ Execute an SQL query """
        cursor = self.conn.cursor() 
        try:
            if is_update:
                self.conn.begin()
            cursor.execute("SET NAMES utf8mb4;")
            cursor.execute("SET CHARACTER SET utf8mb4;")
            cursor.execute("SET character_set_connection=utf8mb4;")
            cursor.execute(strCmd, args)
            if is_update:
                self.conn.commit()
            results = cursor.fetchall()
            return results
        except Exception, e:
            # self.throwSQLError(e)
            raise
        finally:
            cursor.close()


    def execUpdate(self, strCmd, args=()):
        """ Execute an SQL insert/update command """
        # strCmd = strCmd.strip()
        # strCommitCmd = ""
        # if(not(strCmd.lower().startswith("begin;"))):
        #     strCommitCmd = "BEGIN; "

        # strCommitCmd += strCmd

        # if(not(strCmd.lower().endswith(";"))):
        #     strCommitCmd += ";"

        # if(not(strCmd.lower().endswith("commit;"))):
        #     strCommitCmd += " COMMIT;"
        
        return self.execQuery(strCmd, args, is_update=True)


    def execProc(self, strProc, args=()):
        """ Execute an SQL stored procedure """
        cursor = self.conn.cursor() 

        try:
            cursor.execute("SET NAMES utf8mb4; SET CHARACTER SET utf8mb4; SET character_set_connection=utf8mb4;")
            results = cursor.callproc(strProc, args)
            return results        
        except Exception, e:
            self.throwSQLError(e)
            raise
        finally:
            cursor.close()    

    def throwSQLError(self, e):
        """ Log system errors to database """
        strError = "SQL Error %d:  %s" % (e.args[0], e.args[1])
        results = cursor.callproc("sp_systemerror", (strError,))

    def __del__(self):
        self.conn.close()
        