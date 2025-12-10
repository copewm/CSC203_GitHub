# Citation: Used infomation from Flask documentation (https://flask.palletsprojects.com/en/3.0.x/quickstart/)

import hashlib  # For generating short codes from URLs to be at the end (I think hash values are really cool)

from flask import Flask, request, request, redirect, url_for, session, flash, abort, render_template_string
import mysql.connector  # For MySQL connection
import os
from dotenv import load_dotenv


# Load .env file (works both locally and in Docker)
load_dotenv()  # ← this is the magic line

app = Flask(__name__) # Creates a flask key
app.secret_key = 'random'

# the def get_db function to use the .env file is from Grok 3 in socratic mode (all prompts are told to advoid direct answers and foster understanding)
# I gave it the instruction PDF and asked how the .env files worked and what to import and how to integrate it
def get_db():
    return mysql.connector.connect( # This returns a connection object using mysql.connector.connect()
        host=os.getenv('MYSQL_HOST'),      # local → localhost, Docker → host.docker.internal
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DB')
    )
# End of AI code import

@app.before_request
def require_login():
    # These pages are public to check if the user is logged in
    if request.endpoint in ['login', 'register', 'redirect_short', 'static']:
        return
    if 'user_id' not in session:
        return redirect(url_for('login')) # redirects to login page if not logged in

# ———————— AUTH ————————
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'] # Gets the username and password from the login form
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor() # Connects to the database and sets the cursor
        cur.execute("SELECT id, username, is_admin FROM users WHERE username=%s AND password=%s",(username, password))
        # usernames and passwords are in plain text which isn't ideal, but this is just for class, it could be a hash tho
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = bool(user[2]) # boolean for if the account is an admin
            return redirect(url_for('index'))
        flash('Bad login') # I was trying to send a response message but the page just reloads, websites are not my strong suit
        # I found the flash command online to attempt a response and I don't think they work the way I though
    # HTML for the simple login page form
    return '''
        <h2>Login</h2>
        <form method=post>
            Username: <input name=username required><br><br>
            Password: <input type=password name=password required><br><br>
            <button>Login</button>
        </form>
        <p><a href="/register">Register</a>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        try: # using a try statement to try to catch errors
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                        (username, password))
            conn.commit()
            flash('Registered — log in now')
            return redirect('/login')
        except:
            flash('Username taken')
        finally:
            cur.close()
            conn.close()
    # Create account form HTML
    return '''
        <h2>Register</h2>
        <form method=post>
            Username: <input name=username required><br><br>
            Password: <input type=password name=password required><br><br>
            <button>Create account</button>
        </form>
    '''

# logout function that clears the session data and effectivly restarts
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ———————— MAIN ————————
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db()
    cur = conn.cursor()

    # handles the URL shortening
    if request.method == 'POST':
        long_url = request.form['url'].strip()
        if not long_url.startswith(('http://', 'https://')):
            long_url = 'https://' + long_url # adds the https, fixes some urls and others seemed fine
        short_code = hashlib.md5(long_url.encode()).hexdigest()[:6]

        cur.execute("""INSERT INTO urls (short_code, long_url, user_id) VALUES (%s, %s, %s)  ON DUPLICATE KEY UPDATE long_url=VALUES(long_url)""",
                    (short_code, long_url, session['user_id']))
        conn.commit()

    # Decide what URLs to show
    if session.get('is_admin'): # check if it is an admin and to show all
        cur.execute("""SELECT short_code, long_url, username FROM urls JOIN users ON urls.user_id = users.id ORDER BY urls.id DESC""")
    else: # else only show the URLS connected to the userID
        cur.execute("SELECT short_code, long_url FROM urls WHERE user_id=%s ORDER BY id DESC",
                    (session['user_id'],))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # gets the URL base without the slash at the end
    base = request.host_url.rstrip('/')
    list_html = ''
    for row in rows:
        short_code, long_url = row[0], row[1]
        owner = row[2] if len(row) == 3 else session['username']
        delete_link = f'<a href="/delete/{short_code}" style="color:red">[Delete]</a>' \
                      if session.get('is_admin') or owner == session['username'] else ''
        list_html += f'<li><b>{owner}:</b> <a href="{base}/{short_code}" target="_blank">{base}/{short_code}</a> → {long_url} {delete_link}</li>'

    return f'''
        <h2>Hello {session['username']} {"(ADMIN)" if session.get('is_admin') else ""} | <a href="/logout">Logout</a></h2>
        <form method=post>
            <input name=url placeholder="https://very-long-url.com/..." size=70 required>
            <button>Shorten</button>
        </form>
        <h3>Shortened URLs:</h3>
        <ul>{list_html or "<i>none yet</i>"}</ul>
    '''

# redirect the short hash codes to the original URL
@app.route('/<short_code>')
def redirect_short(short_code):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT long_url FROM urls WHERE short_code=%s", (short_code,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row: # if found it will redirect to the page
        return redirect(row[0])
    abort(404) # otherwise it gives a 404 error

# Deletes a users URL code, or an admin can as well
@app.route('/delete/<short_code>')
def delete(short_code):
    conn = get_db()
    cur = conn.cursor()
    if session.get('is_admin'): # admin delete anything
        cur.execute("DELETE FROM urls WHERE short_code=%s", (short_code,))
    else: # user can delete a user's URL
        cur.execute("DELETE FROM urls WHERE short_code=%s AND user_id=%s",(short_code, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__': # run the app
    app.run(debug=False, port=5000)