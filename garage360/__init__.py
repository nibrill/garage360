"""Garage360 - plataforma de gestion y reservas para talleres mecanicos."""

# Driver MySQL: usa mysqlclient si esta instalado; si no, PyMySQL (puro Python, sin compilar).
try:
    import MySQLdb  # noqa: F401
except ImportError:
    import pymysql

    pymysql.version_info = (2, 2, 1, 'final', 0)  # version que Django exige a mysqlclient
    pymysql.install_as_MySQLdb()
