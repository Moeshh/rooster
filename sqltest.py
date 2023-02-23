import mysql.connector
import urllib.request
from urllib.parse import urlparse
from urllib.parse import parse_qs
import pandas as pd
from html_table_parser import HTMLTableParser
from datetime import datetime

dbconnect = mysql.connector.connect(
    host='localhost',
    port='3306',
    user='root',
    password='',
    database='yc2302'
)

mycursor = dbconnect.cursor()

def selectquery():
    mycursor.execute('SELECT * FROM students')
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