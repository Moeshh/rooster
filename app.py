from flask import Flask, jsonify, request
from urllib.parse import urlparse
from urllib.parse import parse_qs
import functie
import pokemon
import sqltest
import pandas as pd
import pymysql
import urllib.request
import locale
import datetime
from html.parser import HTMLParser

app = Flask(__name__)

@app.route('/')
def hello_world():
    return rooster('all')

@app.route('/test/<zoekterm>')
def test(zoekterm):
    return functie.returnwaarde(zoekterm)

@app.route('/getpok/<poke>')
def getpok(poke):
    return pokemon.getpokemons(poke)

@app.route('/sql/<querytype>')
def getquery(querytype):
    query = querytype.split('=')
    match query[0]:
        case 'select':
            return sqltest.selectquery()
        case 'insert':
            return sqltest.insertquery()
        case 'query':
            return sqltest.wherequery(query[1])
        case 'insertrooster':
            return insertrooster()
        case 'inserttrainers':
            return inserttrainers()

@app.route("/newrooster/")
def newrooster():
    xhtml = url_get_contents("http://p.codefounders.nl/p").decode("utf-8")
    p = HTMLParser()
    p.feed(xhtml)
    df = pd.DataFrame(p.tables[0])

    # remove indexed headers 0-1-2-3-4 and use top row as headers datum tijd etc.
    new_header = df.iloc[0]
    df = df[1:]
    df.columns = new_header
    # merge dag and datum into 1 row
    df["Datum"] = df.apply(merge_columns, axis=1)
    # rearrange columns
    columns_titles = [
        "Datum",
        "Tijd",
        "Training",
        "Les info",
        "Trainer(s)",
        "Locatie",
        "Status",
    ]
    df = df.reindex(columns=columns_titles)
    # only show rows relevant to class yc2302
    df.drop(df[df["Training"] == "Weekend"].index, inplace=True)
    df.drop(df[df["Training"] == ""].index, inplace=True)
    # dchange time format
    df["Datum"] = df["Datum"].apply(lambda x: date_replace(x, str(datetime.date.today().year)))
    df["Tijd"] = df["Tijd"].apply(convert_time_range)

    html_string = "<html><head><title>Rooster</title><style>body { background-color: linen; } table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #d8d8d8; padding: 8px; text-align: left; } th { background-color: #d8d8d8; }tr:nth-child(even) { background-color: #f8f8f8;}tr:nth-child(odd) { background-color: #f0f0f0;}</style></head><body>"

    return html_string + df.to_html(index=False)


@app.route('/rooster/')
def roosterall():
    return rooster('all')

@app.route("/rooster/<group>")
def rooster(group):
    df = pd
    locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")
    if group == "new":
        xhtml = url_get_contents("http://p.codefounders.nl/p").decode("utf-8")
        p = HTMLParser()
        p.feed(xhtml)
        df = pd.DataFrame(p.tables[0])

        # remove indexed headers 0-1-2-3-4 and use top row as headers datum tijd etc.
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header
        # merge dag and datum into 1 row
        df["Datum"] = df.apply(merge_columns, axis=1)

        # rearrange columns
        df = df.rename(
            columns={
                "Les info": "Training",
                "Training": "Groep",
                "Status": "Source",
                "Les notities": "Info",
            }
        )
        columns_titles = [
            "Datum",
            "Tijd",
            "Groep",
            "Training",
            "Info",
            "Trainer(s)",
            "Locatie",
            "Source",
        ]
        df = df.reindex(columns=columns_titles)

        # only show rows relevant to class yc2302
        df.drop(df[df["Groep"] == "Weekend"].index, inplace=True)
        df.drop(df[df["Groep"] == ""].index, inplace=True)
        # dchange time format
        df["Datum"] = df["Datum"].apply(lambda x: date_replace(x, str(datetime.date.today().year)))
        df["Datum"] = pd.to_datetime(df["Datum"], format="%d-%m-%Y").dt.strftime("%a %d %b")
        df["Tijd"] = df["Tijd"].apply(convert_time_range)
    else:
        dbconnect = pymysql.connect(user='yc2302',
            password='Water123',
            database='yc2302',
            host='yc2302sql.mysql.database.azure.com',
            ssl={'ca': 'DigiCertGlobalRootCA.crt.pem'})
        query = "SELECT r.*, GROUP_CONCAT(t.name SEPARATOR ', ') AS trainers \
            FROM rooster r \
            LEFT JOIN classes c ON r.id = c.rooster_id \
            LEFT JOIN trainers t ON c.trainer_id = t.id \
            GROUP BY r.id"
        df = pd.read_sql_query(query, dbconnect)
        # create columns for date and time
        df["Datum"] = pd.to_datetime(df["starttime"]).dt.strftime("%a %d %b")
        df["Tijd"] = (
            pd.to_datetime(df["starttime"]).dt.strftime("%H:%M")
            + " tot "
            + pd.to_datetime(df["endtime"]).dt.strftime("%H:%M")
        )
        # sort by datetime
        df = df.sort_values(by=["starttime"])
        # rename headers and sort the headers
        df = df.rename(
            columns={
                "starttime": "starttime",
                "endtime": "endtime",
                "class": "Groep",
                "training": "Training",
                "trainers": "Trainer(s)",
                "location": "Locatie",
                "info": "Info",
                "source": "Source",
            }
        )
        columns_titles = [
            "Datum",
            "Tijd",
            "Groep",
            "Training",
            "Info",
            "Trainer(s)",
            "Locatie",
            "Source",
        ]
        df = df.reindex(columns=columns_titles)

    class_select = '<div id="ClassSelect"><label for="class">Groep:</label><select onchange="val()" name="class" id="SelectClass">'
    trainer_select = '<div id="TrainerSelect"><label for="trainer">Trainer:</label><select onchange="val()" name="trainer" id="SelectTrainer">'
    if group == "all" or group == "new":
        class_select += '<option value="all">Alle</option>'
        trainer_select += '<option value="all">Alle</option>'
        unique_groups = sorted(df["Groep"].unique(), reverse=True)
        for groep in unique_groups:
            class_select += (
                '<option value="' + str(groep) + '">' + str(groep) + "</option>"
            )

        # Get unique trainers
        unique_trainers = set()
        for trainer in df["Trainer(s)"].unique():
            if trainer is not None and ', ' in trainer:
                trainers = trainer.split(', ')
                for t in trainers:
                    unique_trainers.add(t)
            elif trainer is not None:
                unique_trainers.add(trainer)
        unique_trainers = sorted(unique_trainers)
        # Generate select element options for trainers
        for trainer in list(unique_trainers):
            trainer_select += (
                '<option value="' + str(trainer) + '">' + str(trainer) + "</option>"
            )
    else:
        df.drop(df[df["Groep"] != group].index, inplace=True)
        class_select += '<option value="' + group + '">' + group + "</option>"

    class_select += "</select></div>"
    trainer_select += "</select></div>"

    styles = [
        dict(selector=".row_heading, .blank, .index_name", props=[("display", "none")]),
        dict(selector=".col_heading, .level0", props=[("text-align", "center")]),
    ]
    
    df_styled = (
        df.style.apply(highlight_rows, axis=1)
        .set_table_styles(styles)
        .set_properties(**{"text-align": "center"})
        .set_table_attributes('class="roostertable"')
    )
    html_table = df_styled.to_html(index=False)
    js = "<script>function val(){let selectedClass=document.getElementById(\"SelectClass\").value;let selectedTrainer=document.getElementById(\"SelectTrainer\").value;let i=0;let tableRows=document.querySelectorAll('table tr');tableRows.forEach(function(row,index){if(index===0){row.style.display='';return} let rowClass=row.querySelector('td:nth-child(4)');let rowTrainers=row.querySelector('td:nth-child(7)');if((selectedClass!=='all'&&selectedTrainer!=='all'&&rowClass&&rowTrainers&&rowClass.textContent===selectedClass&&rowTrainers.textContent.includes(selectedTrainer))||(selectedClass!=='all'&&selectedTrainer==='all'&&rowClass&&rowClass.textContent===selectedClass)||(selectedClass==='all'&&selectedTrainer!=='all'&&rowTrainers&&rowTrainers.textContent.includes(selectedTrainer))||(selectedClass==='all'&&selectedTrainer==='all')){row.style.display='';if(i%2==0){row.style.background=\"#f0f0f0\"}else{row.style.background=\"#f8f8f8\"} i++}else{row.style.display='none'}})}</script>"    
    html_head = (
        "<html><head><title>Rooster</title>"
        + js
        + "<style>body { background-color: linen; } table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #d8d8d8; padding: 8px; text-align: left; } th { background-color: #d8d8d8; }tr:nth-child(even) { background-color: #f0f0f0;}tr:nth-child(odd) { background-color: #f8f8f8;}.today {background-color: yellow;} #ClassSelect { position:relative; float:left; padding: 5px; } #TrainerSelect { position:relative; float:left; padding: 5px; }</style></head><body>"
    )
    html_end = "</body></html>"
    return html_head + class_select + trainer_select + html_table + html_end



'''
fetch('/getrooster').then(function (response) {return response.json();}).then(function (text) {console.log('GET response:'); console.log(text.greeting); });
<script>function val() { d = document.getElementById("SelectClass").value; alert(d);}</script>
<script>function val() { var selectedClass = document.getElementById("SelectClass").value;	var tableRows = document.querySelectorAll(\'table tr\'); if (selectedClass !== \'All\') {tableRows.forEach(function(row) { if (row.querySelector(\'td:nth-child(3)\').textContent !== selectedClass) {	row.style.display = \'none\';	} else { row.style.display = \'\'; } });} else { tableRows.forEach(function(row) { row.style.display = \'\'; });}}</script>
tableRows.forEach(function(row) { 
arr.forEach(function(value) { console.log(value);});
<script>document.addEventListener(\'DOMContentLoaded\', function() {var classSelect = document.querySelector(\'select[name="class"]\'); classSelect.addEventListener(\'change\', function() {var selectedClass = classSelect.value; var tableRows = document.querySelectorAll(\'table tr\'); if (selectedClass !== \'All\') { tableRows.forEach(function(row) { if (row.querySelector(\'td:nth-child(3)\').textContent !== selectedClass) { row.style.display = \'none\'; } else { row.style.display = \'\'; }});} else {tableRows.forEach(function(row) {row.style.display = \'\';});}});});</script>

'''



@app.route("/getrooster/<groep>", methods=["GET", "POST"])
def getros(groep):
    if request.method == "GET":
        message = {"greeting": "Hello from Flask!"}
        return jsonify(message)  # serialize and use JSON headers
    if request.method == "POST":
        print("post received: " + request.get_json())  # parse as JSON
        # print(request.get_text())  # parse as JSON
        return "Sucesss", 200


def highlight_rows(row):
    today = datetime.datetime.now().strftime("%a %d %b")
    value = row.loc["Datum"]
    if value == today:
        return ["background-color: #BAFFC9; border-color: #6ACD60" for r in row]
    else:
        return ["" for r in row]


def url_get_contents(url):
    req = urllib.request.Request(url=url)
    f = urllib.request.urlopen(req)
    return f.read()


def merge_columns(row):
    return str(row["Dag"]) + " " + row["Datum"]


def convert_time_range(time_range):
    start, end = time_range.split("-")
    start = start.zfill(2)
    end = end.zfill(2)
    return f"{start}:00-{end}:00"


def insertrooster():
    xhtml = url_get_contents("http://p.codefounders.nl/p").decode("utf-8")
    p = HTMLParser()
    p.feed(xhtml)
    df = pd.DataFrame(p.tables[0])

    # remove indexed headers 0-1-2-3-4 and use top row as headers datum tijd etc.
    new_header = df.iloc[0]
    df = df[1:]
    df.columns = new_header
    # merge dag and datum into 1 row
    df["Datum"] = df.apply(merge_columns, axis=1)
    # rearrange columns
    columns_titles = [
        "Datum",
        "Tijd",
        "Training",
        "Les info",
        "Trainer(s)",
        "Locatie",
        "Status",
        "Les notities",
    ]
    df = df.reindex(columns=columns_titles)
    # only show rows relevant to class yc2302
    df.drop(df[df["Training"] == "Weekend"].index, inplace=True)
    df.drop(df[df["Training"] == ""].index, inplace=True)
    # df.drop(df[df['Training'] != 'YC2302'].index, inplace=True)
    # dchange time format
    df["Datum"] = df["Datum"].apply(lambda x: date_replace(x, str(datetime.date.today().year)))
    df["Tijd"] = df["Tijd"].apply(convert_time_range)

    dbconnect = pymysql.connect(user='yc2302',
        password='Water123',
        database='yc2302',
        host='yc2302sql.mysql.database.azure.com',
        ssl={'ca': 'DigiCertGlobalRootCA.crt.pem'})
    mycursor = dbconnect.cursor()
    for row in df.iterrows():
        training = row[1]["Les info"]
        group = row[1]["Training"]
        trainer = row[1]["Trainer(s)"]
        location = row[1]["Locatie"]
        source = row[1]["Status"]
        datum = row[1]["Datum"] + "-2023"
        notes = row[1]["Les notities"]
        start_time, end_time = row[1]["Tijd"].split("-")
        start_datetime = pd.to_datetime(
            datum + start_time, format="%d-%m-%Y%H:%M"
        ).strftime("%Y-%m-%d %H:%M:%S")
        end_datetime = pd.to_datetime(
            datum + end_time, format="%d-%m-%Y%H:%M"
        ).strftime("%Y-%m-%d %H:%M:%S")
        query = "INSERT INTO rooster (starttime, endtime, class, training, trainer, location, info, source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (
            start_datetime,
            end_datetime,
            group,
            training,
            trainer,
            location,
            notes,
            source,
        )
        mycursor.execute(query, values)
    dbconnect.commit()
    return "rooster values inserted in database"

def inserttrainers():
    '''
        //classes table creeren en daarna vullen met values uit r.trainer
        CREATE TABLE classes (
            id INT PRIMARY KEY AUTO_INCREMENT,
            rooster_id INT,
            trainer_id INT,
            FOREIGN KEY (rooster_id) REFERENCES rooster(id),
            FOREIGN KEY (trainer_id) REFERENCES trainers(id)
        );

        INSERT INTO classes (rooster_id, trainer_id)
        SELECT r.id, t.id
        FROM rooster r
        JOIN trainers t ON FIND_IN_SET(t.name, REPLACE(r.trainer, ', ', ',')) > 0;

        //selecteer alle trainer namen vai left join
        SELECT r.*, GROUP_CONCAT(t.name SEPARATOR ', ') AS trainers
        FROM rooster r
        LEFT JOIN classes c ON r.id = c.rooster_id
        LEFT JOIN trainers t ON c.trainer_id = t.id
        GROUP BY r.id

    '''
    return 'ik heb het rechtstreeks in sql gedaan'

def date_replace(date_str, year):
    date_str = (
        date_str
        .replace("ma ", "")
        .replace("di ", "")
        .replace("wo ", "")
        .replace("do ", "")
        .replace("vr ", "")
        .replace("-jan.", "-01-"+year)
        .replace("-feb.", "-02-"+year)
        .replace("-mrt.", "-03-"+year)
        .replace("-apr.", "-04-"+year)
        .replace("-mei.", "-05-"+year)
        .replace("-mei", "-05-"+year)
        .replace("-jun.", "-06-"+year)
        .replace("-jul.", "-07-"+year)
        .replace("-aug.", "-08-"+year)
        .replace("-sep.", "-09-"+year)
        .replace("-okt.", "-10-"+year)
        .replace("-nov.", "-11-"+year)
        .replace("-dec.", "-12-"+year)
    )
    return date_str