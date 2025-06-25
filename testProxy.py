from flask import Flask, g, request, jsonify, send_file, Response
from flask_cors import CORS  # Import CORS extension
import requests, json, datetime, time
from enum import Enum, auto
import sqlite3

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DATABASE = 'tests.db'

class TestResult(Enum):
    PASSED = 'PASSED'
    FAILED = 'FAILED'
    SKIPPED = 'SKIPPED'
    ERROR = 'ERROR'

def multiLineStringToDict(header_string):
    if header_string is None or header_string == "":
        return {}

    headers = {}
    lines = header_string.strip().split('\n')
    for line in lines:
        key, value = line.split(':', 1)
        headers[key.strip()] = value.strip()
    return headers

@app.route('/proxy/health', methods=['GET'])
def health_check():
    # Check the health of the proxy service
    # You can perform any necessary checks here, such as checking dependencies, database connections, etc.
    return jsonify({'status': 'ok'}), 200

@app.route('/proxy', methods=['POST'])
def proxy():
    # Get request details from the client
    start_time = time.time() 

    request_data = request.json
    url = request_data.get('url')  # URL of the target endpoint
    method = request_data.get('method', 'GET')  # Default to GET if method is not specified
    
    cookies = request_data.get('cookies', '')
    cookies = multiLineStringToDict(cookies)

    headers = request_data.get('headers', '')  # Headers from the client's request
    headers = multiLineStringToDict(headers)

    data = request_data.get('data')  # JSON data for POST requests

    try:
        # Make the request to the target endpoint
        print(url)

        if method == 'GET':
            response = requests.get(url, headers=headers, cookies=cookies, timeout=20, verify=False)  # Set timeout to 10 seconds
        if method == 'POST':
            data = multiLineStringToDict(data)
            response = requests.post(url, headers=headers, cookies=cookies, data=data, timeout=20, verify=False)  # Set timeout to 10 seconds
        
        json_response = response.json()
        duration = int((time.time() - start_time) * 1000)

        store_result(request_data.get('id'), TestResult.PASSED, duration, json_response)

    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        store_result(request_data.get('id'), TestResult.ERROR, duration, str(e))
        return jsonify({'error': 'General exception: ' + str(e)}), 500

    return jsonify({
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'data': json_response
    })

def store_result(test_id, result, duration = None, payload = ""):
    #print(str(result))
    #print(payload)
    with app.app_context():
        run_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO results (runDate, testId, result, duration, payload)
            VALUES (?, ?, ?, ?, ?)
        ''', (run_date, test_id, result.value, duration, json.dumps(payload)))
        db.commit()
    return None

# Create a connection to the SQLite database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Initialize the database schema
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT,
                cookies TEXT,
                data TEXT,
                idx INTEGER,
                metadata TEXT 
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variables (
                name TEXT PRIMARY KEY NOT NULL,
                value TEXT NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                runDate DATETIME NOT NULL,
                testId INTEGER NOT NULL,
                result TEXT NOT NULL,
                duration INTEGER,
                payload TEXT,
                UNIQUE(testId, runDate)
            );
        ''')
        db.commit()

# Load all tests from the database
def load_tests():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, name, method, url, headers, cookies, data, idx, metadata FROM tests ORDER BY idx')
        tests = cursor.fetchall()

        # Convert the array of values to a list of dictionaries
        tests_dict = []
        for test in tests:
            test_dict = {
                'id': test[0],
                'name': test[1],
                'method': test[2],
                'url': test[3],
                'headers': test[4],
                'cookies': test[5],
                'data': test[6].replace('\n', '\r\n'),
                'idx': test[7],
                'metadata': test[8]
            }
            tests_dict.append(test_dict)

        return tests_dict

# Save a new test to the database
def save_test(name, method, url, headers, cookies, data, idx = 0, metadata = ""):
    with app.app_context():
        data = data.replace('\r\n', '\n')
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO tests (name, method, url, headers, cookies, data, idx, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, method, url, headers, cookies, data, idx, json.dumps(metadata)))
        db.commit()

@app.route('/tests', methods=['GET', 'POST'])
def manage_tests():
    if request.method == 'GET':
        tests = load_tests()
        return jsonify(tests)
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        method = data.get('method')
        url = data.get('url')
        headers = data.get('headers')
        cookies = data.get('cookies')
        ddata = data.get('data')
        idx = data.get('idx', 0)
        meta = data.get('metadata', "")
        save_test(name, method, url, headers, cookies, ddata, idx, meta)
        return jsonify({'message': 'Test saved successfully'})

# Delete a test from the database based on its ID
def delete_test(test_id):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
        db.commit()

@app.route('/tests/<int:test_id>', methods=['GET'])
def get_test(test_id):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, name, method, url, headers, cookies, data, idx, metadata FROM tests WHERE id = ?', (test_id, ))
        test = cursor.fetchone()  # Use fetchone() since you expect only one row

    if test:
        # Create a dictionary from the row data
        test_data = {
            'id': test[0],
            'name': test[1],
            'method': test[2],
            'url': test[3],
            'headers': test[4],
            'cookies': test[5],
            'data': test[6],
            'idx': test[7],
            'metadata': test[8]
        }
        return jsonify(test_data)
    else:
        return jsonify({'message': 'Test not found'}), 404

@app.route('/tests/<int:test_id>', methods=['POST'])
def update_test(test_id):
    try:
        # Parse request data
        data = request.json
        # Extract field values from data
        name = data.get('name')
        url = data.get('url')
        method = data.get('method')
        headers = data.get('headers')
        cookies = data.get('cookies')
        datas = data.get('data')
        meta = data.get('metadata')

        # Update database
        with get_db() as db:
            cursor = db.cursor()
            # Execute SQL update statement
            cursor.execute('UPDATE tests SET name = ?, url = ?, method = ?, headers = ?, cookies = ?, data = ?, metadata = ? WHERE id = ?', (name, url, method, headers, cookies, datas, meta, test_id))
            db.commit()
        return jsonify({'message': 'Test updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tests/<int:test_id>', methods=['DELETE'])
def delete_test_route(test_id):
    delete_test(test_id)
    return jsonify({'message': 'Test deleted successfully'})

# Load all variables from the database
def load_all_variables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM variables')
        variables = cursor.fetchall()
        variables_dict = [{'name': var[0], 'value': var[1]} for var in variables]
        return variables_dict

# Save a variable to the database
def save_variable(name, value):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO variables (name, value)
            VALUES (?, ?)
        ''', (name, value))
        db.commit()

@app.route('/variables', methods=['GET', 'POST'])
def manage_variables():
    if request.method == 'GET':
        variables = load_all_variables()
        return jsonify(variables)
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        value = data.get('value')
        save_variable(name, value)
        return jsonify({'message': 'Variable saved successfully'})

@app.route('/custom-sql', methods=['POST'])
def execute_custom_sql():
    try:
        # Extract the SQL query from the request body
        sql_query = request.json.get('query')

        # Connect to the database
        conn = sqlite3.connect('tests.db')
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(sql_query)
        conn.commit()

        result = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Return the query result as JSON
        return jsonify({'result': result})
    except Exception as e:
        # Return error message if an exception occurs
        return jsonify({'error': str(e)}), 400

@app.route('/analyze')
def analyze():
    return send_file('analyze.html')

@app.route('/t/<int:test_id>')
def showTest(test_id):
    return send_file('test.html')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/lib/<path:filename>')
def library(filename):
    if filename.endswith('.js'):
        mimetype = 'text/javascript'
    elif filename.endswith('.css'):
        mimetype = 'text/css'
    else:
        # For other file types or if the file is not found, serve HTML by default
        filename = 'index.html'
        mimetype = 'text/html'
    

    return send_file('lib/' + filename, mimetype=mimetype)

if __name__ == '__main__':
    init_db()  # Initialize the database schema
    app.run(debug=True)
