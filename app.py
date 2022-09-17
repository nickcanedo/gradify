from codecs import namereplace_errors
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
    return render_template("index.html")


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
        username = session['name']
        id = db.execute('SELECT id FROM courses WHERE username = ? AND course_code = ?;',username,code)[0]['id']
        
        # get course info
        course = db.execute("SELECT * FROM courses WHERE username = ? AND course_code = ?;",username,code)
        assignments = db.execute("SELECT * FROM assignments WHERE course_id = ?;",id)
        
        # algorithm to calculate total weight
        weights = db.execute("SELECT weight FROM assignments WHERE course_id = ? AND username = ?;",id,username)
        if not weights:
            weight_sum = 0
        else:
            weight_sum = 0
            for weight in weights:
                weight_sum += weight['weight']
            
        # algorithm to calculate course average
        grades = db.execute("SELECT grade,weight FROM assignments WHERE course_id = ? AND username = ?;",id,username)
        grade_sum = 0
        if not grades:
            grade = 0
        else:
            for grade in grades:
                grade_sum += (grade['grade'] * 0.01) * grade['weight']
            grade = (grade_sum/weight_sum) * 100
            
        return render_template("view.html",assignments=assignments, course=course, code=code,weight=round(weight_sum,2),grade=round(grade,2))
    else:
        return redirect("/grades")
    
    
@app.route("/account", methods = ["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        return render_template("account.html")
    else:
        username = session['name']
        return render_template("account.html", username=username)
    

@app.route("/username", methods = ["GET", "POST"])
@login_required
def username():
    if request.method == "POST":
        username = session['name']
        new_username = request.form.get('username')
        users = db.execute("SELECT * FROM users;")
        errorname = False
        
        # USERNAME VALIDATION
        
        # empty username
        if not new_username:
            errorname = "You must enter a username"
            return render_template('account.html', errorname=errorname, username=username)
            
        # username already in use
        for user in users:
            if user['username'] == new_username:
                errorname = "Username is already in use"
                return render_template('account.html', errorname=errorname, username=username)

        # change all instances of old username to new username
        db.execute("UPDATE users SET username = ? WHERE username = ?;", new_username, username)
        db.execute("UPDATE courses SET username = ? WHERE username = ?;", new_username, username)        
        db.execute("UPDATE assignments SET username = ? WHERE username = ?;", new_username, username)
        session['name'] = new_username
        return redirect("/")
    else:
        return redirect("/")
    
    
@app.route("/password", methods = ["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        username = session['name']
        oldpassword = request.form.get('oldpassword')
        newpassword = request.form.get('newpassword')
        hash = db.execute("SELECT hash FROM users WHERE username = ?;", username)[0]['hash']
        errorpass = False
        
        # PASSWORD VALIDATION
        
        # empty password or confirm password field
        if not oldpassword or not newpassword:
            errorpass = "You must enter a password"
            return render_template('account.html', errorpass=errorpass, username=username)
        
        # password and confirm password fields do not match
        if not check_password_hash(hash, oldpassword):
            errorpass = "Incorrect Password"
            return render_template('account.html', errorpass=errorpass, username=username)
        
        # change password
        new_hash = generate_password_hash(newpassword, method='pbkdf2:sha256', salt_length=8)
        db.execute("UPDATE users SET hash = ? WHERE username = ? AND hash = ?;", new_hash, username, hash)
        return redirect("/")
    else:
        return redirect("/")
    
    
@app.route("/delete", methods = ["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        username = session['name']
        db.execute("DELETE FROM assignments WHERE username = ?;", username)
        db.execute("DELETE FROM courses WHERE username = ?;", username)
        db.execute("DELETE FROM users WHERE username = ?;", username)
        session.clear()
        return redirect("/register")
    else:
        return redirect("/")


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
        if not code:
            return redirect("/grades")
        username = session['name']
        course_id = db.execute("SELECT id FROM courses WHERE username = ? AND course_code = ?;",username,code)[0]['id']
        error = False
        
        # FORM VALIDATION
        
        # if field(s) are empty
        if not code:
            error = "Please fill out both of the required fields"
            
        # if course does not exist
        course = db.execute("SELECT * FROM courses WHERE username = ? AND course_code = ?;",username,code)
        if not course:
            error = "That course does not exist"
            
        if error:
            courses = db.execute("SELECT course_code FROM courses WHERE username = ?;",username)
            return render_template("drop.html", error=error, courses=courses)

        # drop course BUT delete all assignments first
        db.execute("DELETE FROM assignments WHERE username = ? AND course_id = ?;",username,course_id)
        db.execute("DELETE FROM courses WHERE username = ? AND course_code = ?;",username,code)
        return redirect('/grades')
    
    else:
        username = session['name']
        courses = db.execute("SELECT course_code FROM courses WHERE username = ?;",username)
        return render_template("drop.html", courses=courses)
    

@app.route("/assignmentadd", methods=["GET", "POST"])
@login_required
def assignmentadd():
    if request.method == "POST":
        name = request.form.get("name")
        if (type(request.form.get('weight')) == int or float) and (type(request.form.get('grade')) == int or float):
            weight = int(request.form.get("weight"))
            grade = int(request.form.get("grade"))
        else:
            error = "Please enter only integers for the grade and weight"
            return render_template("assignment_add.html", error=error)
            
        course = request.form.get('course')
        username = session['name']
        course_id = db.execute("SELECT id FROM courses WHERE course_code = ? AND username = ?;",course,username)[0]['id']
        
        # form validation
        if not name or not course or not weight or not grade:
            error = "Please fill out all of the required fields"
            return render_template("assignment_add.html", error=error)
        elif weight < 0 or grade < 0:
            error = "Please enter a grade equal to or greater than 0"
            return render_template("assignment_add.html", error=error)
        else:
            db.execute("INSERT INTO assignments (assignment_name,course_id,username,grade,weight) VALUES (?,?,?,?,?);",name,course_id,username,grade,weight)
            return redirect("/grades")
    else:
        course = request.args.get('course')
        username = session['name']
        return render_template("assignment_add.html", course=course)
    
    
@app.route("/assignmentremove", methods=["GET", "POST"])
@login_required
def assignmentremove():
    if request.method == "POST":
        course = request.form.get('course')
        name = request.form.get("name")
        username = session['name']
        course_id = db.execute("SELECT id FROM courses WHERE course_code = ? AND username = ?;",course,username)[0]['id']
        
        # form validation
        if not name:
            return redirect('/grades')
        else:
            db.execute("DELETE FROM assignments WHERE assignment_name = ? AND username = ? AND course_id = ?;",name,username,course_id)
            return redirect("/grades")
    else:
        course = request.args.get('course')
        username = session['name']
        course_id = db.execute("SELECT id FROM courses WHERE course_code = ? AND username = ?;",course,username)[0]['id']
        assignments = db.execute("SELECT assignment_name FROM assignments WHERE course_id = ? AND username = ?;",course_id,username)
        return render_template("assignment_remove.html",assignments=assignments, course=course)
    
if __name__ == '__main__':
    app.run()