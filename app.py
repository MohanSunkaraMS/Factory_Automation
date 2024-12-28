from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Admin credentials
ADMIN_USERNAME = 'Ask68'
ADMIN_PASSWORD = 'admin123'

# Database connection function
def get_db_connection():
    """Establish and return a database connection."""
    try:
        conn = mysql.connector.connect(
            host='localhost',       # Replace with your DB host
            user='MohanDB',         # Replace with your DB user
            password='1234',        # Replace with your DB password
            database='mohan'        # Replace with your DB name
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

# Routes
@app.route('/')
def home():
    """Redirect to login if not authenticated, otherwise render home page."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hardcoded admin authentication
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('machines'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/machines', methods=['GET', 'POST'])
def machines():
    """Display machine metrics and filtered machine data."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    metrics = {
        "total_machines": 0,
        "machines_started": 0,
        "machines_stopped": 0,
        "job_failures": 0
    }
    machine_data = []
    search_query = request.form.get('machine_name', '')

    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            # Fetch metrics
            cursor.execute("SELECT COUNT(*) AS total FROM winding_data")
            metrics["total_machines"] = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS started FROM winding_data WHERE `Current_status` = 'Running'")
            metrics["machines_started"] = cursor.fetchone()["started"]

            cursor.execute("SELECT COUNT(*) AS stopped FROM winding_data WHERE `Current_status` = 'Stopped'")
            metrics["machines_stopped"] = cursor.fetchone()["stopped"]

            cursor.execute("SELECT SUM(`no_of_job_failure`) AS failures FROM winding_data")
            metrics["job_failures"] = cursor.fetchone()["failures"] or 0

            # Fetch machine data based on search query
            if search_query:
                query = """
                    SELECT `plant_name`, `machine_name`, `machine_model`, `plc_model`, 
                           `no_of turns`, `no_of_layers`, `start_time`
                    FROM winding_data
                    WHERE `machine name` = %s
                    LIMIT 4
                """
                cursor.execute(query, (search_query,))
                machine_data = cursor.fetchall()

            cursor.close()
            conn.close()

    except Exception as e:
        flash(f"Database error: {e}")

    return render_template('machines.html', metrics=metrics, machine_data=machine_data)

@app.route('/get_machine_details', methods=['GET'])
def get_machine_details():
    if not session.get('logged_in'):
        return {"error": "Unauthorized"}, 401

    machine_details = []
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT `plant_name`, `machine_name`, `machine_model`, 
                       `plc_model`, `type_of_insulation`, `type_of_conductor`,`Current_status`
                FROM winding_data
            """
            cursor.execute(query)
            machine_details = cursor.fetchall()
            cursor.close()
            conn.close()
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return {"error": "Database error"}, 500

    return {"data": machine_details}


@app.route('/control_panel')
def control_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('control_panel.html')


@app.route('/logout')
def logout():
    """Logout the user and clear the session."""
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
