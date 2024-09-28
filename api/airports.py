import sys
import simplejson as json
import mariadb
import os
import flask
from flask import request, Blueprint, jsonify
from dotenv import load_dotenv

load_dotenv()

airports = Blueprint('airports', __name__)

config = {
    'host': os.getenv("DB_HOST"),
    'port': int(os.getenv("DB_PORT")),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASS"),
    'database': os.getenv("DB_NAME")
}

@airports.route('/api/airports', methods=['GET'])
def index():
    try:
        conn = mariadb.connect(**config)
        cur = conn.cursor()
        cur.execute("SELECT * FROM airports ORDER BY airport")
        row_headers=[x[0] for x in cur.description]
        rv = cur.fetchall()
        json_data=[]
        for result in rv:
            json_data.append(dict(zip(row_headers,result)))
        return jsonify(json_data)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}", file=sys.stderr)
        return jsonify({"error": "Database connection error"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
