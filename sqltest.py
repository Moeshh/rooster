import urllib.request
from urllib.parse import urlparse
from urllib.parse import parse_qs
#import pandas as pd
#from html_table_parser import HTMLTableParser
#from datetime import datetime
import pymysql
import mysql.connector
from mysql.connector import errorcode
from mysql.connector import ClientFlag

# Obtain connection string information from the portal
dbconnect = pymysql.connect(user='yc2302',
    password='Water123',
    database='yc2302',
    host='yc2302sql.mysql.database.azure.com',
    ssl={'ca': 'DigiCertGlobalRootCA.crt.pem'})
mycursor = dbconnect.cursor()


def selectquery():
    mycursor.execute('SELECT * FROM rooster')
    mydata = mycursor.fetchall()
    return str(mydata)

def insertquery():
    insertquery = 'INSERT INTO students(firstname, lastname, age) VALUES(%s, %s, %s)'
    #values = ('Cecil', 'Boye', 31)
    values = ('David', 'van Meel', 24)
    mycursor.execute(insertquery, values)
    dbconnect.commit()
    return 'values inserted in database'

def wherequery(param):
    mycursor.execute('SELECT * FROM students WHERE age = %s', (param,))
    mydata = mycursor.fetchall()
    return str(mydata)

def insertrooster():
    #test
    return "rooster values inserted in database"

def parse_date(date_str):
    dt = datetime.strptime(date_str, '%d-%m')
    year = datetime.now().year
    return dt.replace(year=year)