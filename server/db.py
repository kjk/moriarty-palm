# Handles InfoMan database creation
# Holds settings for the database

import sys, os, string, MySQLdb
import arsutils
import multiUserSupport

DB_HOST        = 'localhost'
DB_PWD         = "infoman" # TODO: should we change this to be more secure?

def getDbUser():
    dbUser = multiUserSupport.getDbUser()
    return dbUser

def getDbName():
    dbName = multiUserSupport.getServerDatabaseName()
    return dbName

g_connRoot       = None
g_conn           = None

usersSql = """CREATE TABLE users (
  user_id           INT(10) NOT NULL auto_increment,
  cookie            VARCHAR(64)  NOT NULL,
  device_info       VARCHAR(255) NOT NULL,
  cookie_issue_date TIMESTAMP(14) NOT NULL,
  reg_code          VARCHAR(64) NULL,
  registration_date TIMESTAMP(14) NULL,
  disabled_p        CHAR(1) NOT NULL default 'f',

  PRIMARY KEY(user_id),
  UNIQUE (cookie)

) TYPE=MyISAM;"""

requestLogSql = """CREATE TABLE request_log (
    request_id       INT(10) NOT NULL auto_increment,
    user_id          INT(10) NOT NULL REFERENCES users(user_id),
    client_ip        VARCHAR(24) NOT NULL,
    log_date         TIMESTAMP(14) NOT NULL,
    free_p           CHAR(1) NOT NULL,  -- is this request free?
    request          VARCHAR(255) NULL,
    result           VARCHAR(255) NULL,
    -- if not NULL, there was an error processing the request and this is the
    -- error number
    error            INT(10) NULL,

  PRIMARY KEY(request_id)

) TYPE=MyISAM;"""

# index on user_id so that checking for lookup limit from unregistered
# users is faster
requestLogUserIndexSql = "ALTER TABLE request_log ADD INDEX (user_id);"

getCookieLogSql = """CREATE TABLE get_cookie_log (
    log_id          INT(10) NOT NULL auto_increment,

    user_id         INT(10) NOT NULL REFERENCES users(user_id),
    client_ip       VARCHAR(24) NOT NULL,
    log_date        TIMESTAMP(14) NOT NULL,
    device_info     VARCHAR(255) NOT NULL,
    cookie          VARCHAR(64) NOT NULL,

    PRIMARY KEY(log_id)

) TYPE=MyISAM;"""

verifyRegCodeLogSql = """CREATE TABLE verify_reg_code_log (
    log_id          INT(10) NOT NULL auto_increment,

    user_id         INT(10) NOT NULL REFERENCES users(user_id),
    client_ip       VARCHAR(24) NOT NULL,
    log_date        TIMESTAMP(14) NOT NULL,
    reg_code        VARCHAR(64) NOT NULL,
    reg_code_valid_p CHAR(1) NOT NULL,

    PRIMARY KEY(log_id)

) TYPE=MyISAM;"""

# table contains list of valid registration codes
regCodesSql = """CREATE TABLE reg_codes (
  reg_code      VARCHAR(64) NOT NULL,
  purpose       VARCHAR(255) NOT NULL,
  when_entered  TIMESTAMP NOT NULL,
  disabled_p    CHAR(1) NOT NULL DEFAULT 'f',

  PRIMARY KEY (reg_code)
) TYPE=MyISAM;"""


cookieJarsSql = """CREATE TABLE cookie_jars (
  user_id      INT(10) NOT NULL REFERENCES users(user_id),
  pickled_cookie_jar TEXT NOT NULL,
  PRIMARY KEY (user_id)
) TYPE=MyISAM;"""

zap2itSql = """
CREATE TABLE `zap2it_cached_data` (
  `provider_id` int(10) unsigned NOT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY  (`provider_id`,`date`)
) ENGINE=MyISAM ROW_FORMAT=FIXED;

CREATE TABLE `zap2it_programs` (
  `zap2it_id` varchar(30) NOT NULL,
  `title` varchar(100) NOT NULL,
  `series_id` int(10) unsigned,
  `series_volume_title` varchar(100),
  `category` varchar(30),
  `additional_info` varchar(30),
  `description` varchar(200),
  `id` int(10) unsigned NOT NULL auto_increment,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `Index_2` (`zap2it_id`,`series_id`)
) ENGINE=MyISAM;

CREATE TABLE `zap2it_providers` (
  `id` int(10) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM;

CREATE TABLE `zap2it_providers_listings` (
  `provider_id` int(10) unsigned NOT NULL,
  `station_id` int(10) unsigned NOT NULL,
  `index_in_listing` varchar(8) NOT NULL,
  PRIMARY KEY  (`provider_id`,`station_id`)
) ENGINE=MyISAM;

CREATE TABLE `zap2it_stations` (
  `id` int(10) unsigned NOT NULL,
  `name` varchar(20) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM;

CREATE TABLE `zap2it_stations_schedule` (
  `program_id` int(10) unsigned NOT NULL,
  `station_id` int(10) unsigned NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY  (`program_id`,`station_id`,`time`)
) ENGINE=MyISAM
"""

def getRootConnection():
    global g_connRoot
    if None == g_connRoot:
        g_connRoot = MySQLdb.Connect(host='localhost', user='root', passwd='', db='')
    return g_connRoot

def getConnection():
    global g_conn
    if None == g_conn:
        g_conn = MySQLdb.Connect(host=DB_HOST, user=getDbUser(), passwd=DB_PWD, db=getDbName())
    return g_conn

def dbEscape(txt):
    # it's silly that we need connection just for escaping strings
    global g_conn
    return g_conn.escape_string(txt)

g_dbList = None
# return a list of databases on the server
def getDbList():
    global g_dbList
    if None == g_dbList:
        conn = getRootConnection()
        cur = conn.cursor()
        cur.execute("SHOW DATABASES;")
        dbs = []
        for row in cur.fetchall():
            dbs.append(row[0])
        cur.close()
        g_dbList = dbs
    return g_dbList

def FDbExists():
    if getDbName() in getDbList():
        return True
    return False

def deinitDatabase():
    global g_conn, g_connRoot
    if g_conn:
        g_conn.close()
    if g_connRoot:
        g_connRoot.close()

def dropDb(conn):
    cur = conn.cursor()
    cur.execute("DROP DATABASE %s" % getDbName())
    cur.close()
    print "Database '%s' dropped" % getDbName()

def createDb(conn):
    print "creating database '%s'" % getDbName()
    cur = conn.cursor()
    cur.execute("CREATE DATABASE %s" % getDbName())
    cur.execute("USE %s" % getDbName())
    cur.execute(usersSql)

    # TODO: add it but first check the perf implications
    # it's supposed to speed up calculating lookup limit for unregistered users
    #cur.execute(requestLogUserIndexSql)
    cur.execute(requestLogSql)
    cur.execute(getCookieLogSql)
    cur.execute(verifyRegCodeLogSql)
    cur.execute(regCodesSql)
    cur.execute(cookieJarsSql)
    for sql in zap2itSql.split(";"):
        cur.execute(sql)

    cur.execute("GRANT ALL ON %s.* TO '%s'@'%s' IDENTIFIED BY '%s';" % (getDbName(),getDbUser(),DB_HOST,DB_PWD))
    cur.execute("GRANT ALL ON %s.* TO '%s'@'%%' IDENTIFIED BY '%s';" % (getDbName(),getDbUser(),DB_PWD))

    #insertRegCode(cur, iPediaServer.testValidRegCode, True)
    #insertRegCode(cur, iPediaServer.testDisabledRegCode, False)
    cur.close()
    print "Created '%s' database and granted perms to user '%s'" % (getDbName(),getDbUser())

def recreateDb(conn):
    dropDb(conn)
    createDb(conn)

def usageAndExit():
    print "db.py [-create] [-recreate]"

def main():
    if sys.platform == "win32":
        print "Warning: test me directly on the server!"

    fRecreate = arsutils.fDetectRemoveCmdFlag("-recreate")
    fCreate = arsutils.fDetectRemoveCmdFlag("-create")

    if len(sys.argv) != 1:
        usageAndExit()

    try:
        conn = getRootConnection()
        fExists = FDbExists()
        if fExists:
            if fRecreate:
                print "infoman database already exists."
                recreateDb(conn)
            else:
                print "infoman database already exists. Use -recreate flag to force it's recreation"
        else:
            if fCreate:
                print "infoman database doesn't exist."
                createDb(conn)
            else:
                    print "infoman database doesn't exist. Use -create flag to create it"
    finally:
        deinitDatabase()

if __name__ == "__main__":
    main()
