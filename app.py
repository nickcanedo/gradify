from flask import Flask, request, session, render_template, redirect
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# initialize app
app = Flask(__name__)

# configure app
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure database
db = SQL("sqlite:///grades.db")

# app routes
@app.route("/")
@login_required
def index():
    return render_template("index.html", )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        
        # initialize form data into variables
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        users = db.execute("SELECT * FROM users;")
        error = False
        
        # USERNAME VALIDATION
        
        # empty username
        if not username:
            error = "You must enter a username"
            
        # username already in use
        for user in users:
            if user['username'] == username:
                error = "Username is already in use"
                
        # PASSWORD VALIDATION
        
        # empty password or confirm password field
        if not password or not confirm:
            error = "You must enter a password"
        
        # password and confirm password fields do not match
        if password != confirm:
            error = "You must enter matching passwords"
            
        if error:
            return render_template('register.html', error=error, username=username, password=password, confirm=confirm)
        
        # register user into database
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username,hash) VALUES (?,?);",username,hash)
        return redirect("/login")
    
    else:
        return render_template('register.html')
            

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        username = request.form.get("username")
        password = request.form.get("password")
        error = False

        # Ensure username was submitted
        if not username:
            error = "must provide username"

        # Ensure password was submitted
        elif not password:
            error = "must provide password"

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?;", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            error = "invalid username and/or password"
            
        if error:
            return render_template("login.html", error=error, username=username)

        # Remember which user has logged in
        session["name"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/grades", methods=["GET", "POST"])
@login_required
def grades():
    if request.method == "GET":
        courses = db.execute("SELECT * FROM courses WHERE username = ?;",session['name'])
        return render_template("grades.html", courses=courses)


@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    if request.method == "POST":
        if not request.form.get('code') or not request.form.get('name'):
            return redirect("/")
        code = request.form.get('code')
        name = request.form.get('name')
        username = session['name']
        id = db.execute('SELECT id FROM courses WHERE username = ? AND course_name = ? AND course_code = ?;',username,name,code)[0]['id']
        
        # get course info
        course = db.execute("SELECT * FROM courses WHERE username = ? AND course_name = ? AND course_code = ?;",username,name,code)
        assignments = db.execute("SELECT * FROM assignments WHERE course_id = ?;",id)
        return render_template("view.html",assignments=assignments, course=course)
    else:
        return redirect("/grades")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        code = request.form.get("code")
        name = request.form.get("name")
        username = session['name']
        
        # form validation
        if not code or not name:
            error = "Please fill out both of the required fields"
            return render_template("add.html", error=error, code=code, name=name)
        else:
            db.execute("INSERT INTO courses (username,course_name,course_code) VALUES (?,?,?);",username,name,code)
            return redirect("/grades")
    else:
        return render_template("add.html")
        


@app.route("/drop", methods=["GET", "POST"])
@login_required
def drop():
    if request.method == "POST":
        code = request.form.get('code')
        name = request.form.get("name")
        username = session['name']
        error = False
        
        # FORM VALIDATION
        
        # if field(s) are empty
        if not code or not name:
            error = "Please fill out both of the required fields"
            
        # if course does not exist
        course = db.execute("SELECT * FROM courses WHERE username = ? AND course_name = ? AND course_code = ?;",username,name,code)
        if not course:
            error = "That course does not exist"
            
        if error:
            return render_template("drop.html", error=error,code=code,name=name)

        # drop course
        db.execute("DELETE FROM courses WHERE username = ? AND course_name = ? AND course_code = ?;",username,name,code)
        return redirect('/grades')
    
    else:
        return render_template("drop.html")
    

@app.route("/assignmentadd", methods=["GET", "POST"])
@login_required
def assignmentadd():
    if request.method == "POST":
        name = request.form.get("name")
        weight = int(request.form.get("weight"))
        grade = int(request.form.get("grade"))
        course = request.form.get('course')
        username = session['name']
        course_id = db.execute("SELECT id FROM courses WHERE course_code = ? AND username = ?;",course,username)[0]['id']
        
        # form validation
        if not name or not course or not weight or not grade:
            error = "Please fill out all of the required fields"
            return render_template("assignment_add.html", error=error)
        elif weight < 0 or grade < 0:
            return render_template("assignment_add.html", error=error)
        else:
            db.execute("INSERT INTO assignments (assignment_name,course_id,username,grade,weight) VALUES (?,?,?,?,?);",name,course_id,username,grade,weight)
            return redirect("/grades")
    else:
        return render_template("assignment_add.html")
    
    
@app.route("/assignmentremove", methods=["GET", "POST"])
@login_required
def assignmentremove():
    if request.method == "POST":
        name = request.form.get("name")
        course = request.form.get('course')
        username = session['name']
        course_id = db.execute("SELECT id FROM courses WHERE course_code = ? AND username = ?;",course,username)[0]['id']
        
        # form validation
        if not name or not course:
            error = "Please fill out all of the required fields"
            return render_template("assignment_remove.html", error=error)
        else:
            db.execute("DELETE FROM assignments WHERE assignment_name = ? AND username = ? AND course_id = ?;",name,username,course_id)
            return redirect("/grades")
    else:
        return render_template("assignment_remove.html")