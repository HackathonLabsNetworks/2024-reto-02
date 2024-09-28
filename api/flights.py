import sys
import simplejson as json
import datetime
import decimal
import mariadb
import os
import flask
from flask import request, Blueprint, jsonify
from dotenv import load_dotenv

load_dotenv()

flights = Blueprint('flights', __name__)

config = {
    'host': os.getenv("DB_HOST"),
    'port': int(os.getenv("DB_PORT")),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASS"),
    'database': os.getenv("DB_NAME")
}

def converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

@flights.route('/api/flights/airlines_stats', methods=['GET'])
def airline_stats():
    origin = request.args.get('o')
    dest = request.args.get('dst')
    yearFrom = request.args.get('yf')
    yearTo = request.args.get('yt')
    month = request.args.get('m')
    day = request.args.get('d')

    try:
        conn = mariadb.connect(**config)
        cur = conn.cursor()

        query = "SELECT " \
                    "q.carrier, " \
                    "q.airline, " \
                    "q.volume flight_count, " \
                    "ROUND(100 * q.volume / SUM(q.volume) " \
                    "OVER(ORDER BY q.airline ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),2) market_share_pct, " \
                    "ROUND(100 * (q.`delayed` / q.volume), 2) delayed_pct, " \
                    "ROUND(100 * (q.cancelled / q.volume), 2) cancelled_pct, " \
                    "ROUND(100 * (q.diverted / q.volume), 2) diverted_pct " \
                    "FROM ( " \
                        "SELECT f.carrier, a.airline, COUNT(*) volume, " \
                        "SUM(CASE WHEN dep_delay > 0 THEN 1 ELSE 0 END) `delayed`, " \
                        "SUM(diverted) diverted, SUM(cancelled) cancelled " \
                        "FROM flights f JOIN airlines a ON f.carrier = a.iata_code " \
                        "WHERE " \
                            "f.origin = ? AND " \
                            "f.dest = ? AND " \
                            "f.year >= ? AND " \
                            "f.year <= ?"

        if month is not None:
            query += " AND f.month = " + month

        if day is not None:
            query += " AND f.day = " + day

        query += " GROUP BY a.airline, f.carrier) q ORDER BY flight_count desc"

        cur.execute(query,(origin,dest,yearFrom,yearTo))
        row_headers=[x[0] for x in cur.description] 
        rv = cur.fetchall()

        json_data=[]
        for result in rv:
            json_data.append(dict(zip(row_headers,result)))

        return json.dumps(json_data)

    except mariadb.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return jsonify({"error": "Database connection error"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@flights.route('/api/flights/airline_delays', methods=['GET'])
def airline_delays():
    origin = request.args.get('o')
    dest = request.args.get('dst')
    airline = request.args.get('a')
    yearFrom = request.args.get('yf')
    yearTo = request.args.get('yt')
    month = request.args.get('m')
    day = request.args.get('d')

    try:
        conn = mariadb.connect(**config)
        cur = conn.cursor()

        query = "SELECT " \
                    "ROUND(100 * (weather_delayed / total_delayed), 2) weather_delay_pct, " \
                    "ROUND(100 * (carrier_delayed / total_delayed), 2) carrier_delay_pct, " \
                    "ROUND(100 * (nas_delayed / total_delayed), 2) nas_delay_pct, " \
                    "ROUND(100 * (security_delayed / total_delayed), 2) security_delay_pct, " \
                    "ROUND(100 * (late_aircraft_delayed / total_delayed), 2) late_aircraft_delay_pct " \
                "FROM (" \
                    "SELECT " \
                        "carrier_delayed, nas_delayed, security_delayed, late_aircraft_delayed, weather_delayed, " \
                        "(carrier_delayed+nas_delayed+security_delayed+late_aircraft_delayed+weather_delayed) total_delayed " \
                    "FROM (" \
                        "SELECT " \
                            "AVG(carrier_delay) carrier_delayed, " \
                            "AVG(nas_delay) nas_delayed, " \
                            "AVG(security_delay) security_delayed, " \
                            "AVG(late_aircraft_delay) late_aircraft_delayed, " \
                            "AVG(weather_delay) weather_delayed " \
                         "FROM " \
                            "flights f JOIN airlines a ON f.carrier = a.iata_code " \
                         "WHERE " \
                            "f.origin = ? AND f.dest = ? AND f.carrier = ? AND f.year >= ? AND f.year <= ?"

        if month is not None:
            query += " AND f.month = " + month

        if day is not None:
            query += " AND f.day = " + day

        query += " GROUP BY a.airline, f.carrier) a) b"

        cur.execute(query,(origin, dest, airline, yearFrom, yearTo))
        row_headers=[x[0] for x in cur.description] 
        result = cur.fetchone()
        json_obj=dict(zip(row_headers,result))

        return json.dumps(json_obj)

    except mariadb.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return jsonify({"error": "Database connection error"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@flights.route('/api/flights/delays_comparison', methods=['GET'])
def delays_comparison():
    origin = request.args.get('o')
    dest = request.args.get('dst')
    airline = request.args.get('a')
    yearFrom = request.args.get('yf')
    yearTo = request.args.get('yt')
    month = request.args.get('m')
    day = request.args.get('d')

    try:
        conn = mariadb.connect(**config)
        cur = conn.cursor()

        query = "SELECT " \
                    "AVG(carrier_delay) carrier, " \
                    "AVG(nas_delay) nas, " \
                    "AVG(security_delay) sec, " \
                    "AVG(late_aircraft_delay) late_aircraft, " \
                    "AVG(weather_delay) weather " \
                "FROM " \
                    "flights f " \
                "WHERE " \
                    "f.origin = ? " \
                    "AND f.dest = ? " \
                    "AND f.carrier = ? " \
                    "AND f.year >= ? AND f.year <= ?"

        if month is not None:
            query += " AND f.month = " + month

        if day is not None:
            query += " AND f.day = " + day

        query +=    " UNION SELECT " \
                        "AVG(carrier_delay) carrier, " \
                        "AVG(nas_delay) nas, " \
                        "AVG(security_delay) sec, " \
                        "AVG(late_aircraft_delay) late_aircraft, " \
                        "AVG(weather_delay) weather " \
                    "FROM " \
                        "flights f " \
                    "WHERE " \
                        "f.origin = ? " \
                        "AND f.dest = ? " \
                        "AND f.year >= ? AND f.year <= ?"

        if month is not None:
            query += " AND f.month = " + month

        if day is not None:
            query += " AND f.day = " + day

        cur.execute(query,(origin, dest, airline, yearFrom, yearTo, origin, dest, yearFrom, yearTo))

        row_headers=[x[0] for x in cur.description] 
        rv = cur.fetchall()

        json_data=[]
        for result in rv:
            json_data.append(dict(zip(row_headers,result)))

        return json.dumps(json_data, default = converter)

    except mariadb.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return jsonify({"error": "Database connection error"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
