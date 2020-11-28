from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please log in to access this page", "danger")
            return redirect(url_for("login"))
    return decorated_function

class RegisterForm(Form):
    name = StringField("First Name", validators=[validators.length(min=4, max=25)])
    surname = StringField("Last Name", validators=[validators.length(min=4, max=25)])
    username = StringField("Choose a username", validators=[validators.DataRequired(message="")])
    email = StringField("Email Address", validators=[validators.Email(message="Please enter a valid email address")])
    password = PasswordField("Choose a password", validators=[validators.DataRequired(message=""), validators.EqualTo(fieldname="confirm", message="Your password doesn't match")])
    confirm = PasswordField("Confirm a password")

class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

app = Flask(__name__)

app.secret_key = "Dblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "d blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

@app.route("/")
def index():
    articles = [
        {"id":1, "title":"Deneme1", "content":"Deneme1 icerik"},
        {"id":2, "title":"Deneme2", "content":"Deneme2 icerik"},
        {"id":3, "title":"Deneme3", "content":"Deneme3 icerik"}
        ]
    return render_template("index.html", articles = articles)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    check = "select *from articles"
    result = cursor.execute(check)
    if result>0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    check = "select *from articles where author=%s"
    result = cursor.execute(check,(session["username"],))
    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else: 
        return render_template("dashboard.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name = form.name.data
        surname = form.surname.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        check = "insert into user(name, surname, username, email, password) values(%s,%s,%s,%s,%s)"
        cursor.execute(check,(name, surname,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("You have successfully registered", "success")

        

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)
    
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method=="POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        check = "select *from user where username=%s"
        result = cursor.execute(check,(username,))
        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Successfully entered", "success")
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for("index"))
            else:
                flash("The password you entered is incorrect", "danger")
                return redirect(url_for("login"))


        else:
            flash("User not found", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    check = "select *from articles where id=%s"
    result = cursor.execute(check,(id,))
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")




@app.route("/article/<string:id>")
def detail(id):
    return "Article Id:"+id

#Adding Article
@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        check = "insert into articles(title, author, content) values(%s,%s,%s)"
        cursor.execute(check,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Article successfully saved", "success")
        return redirect(url_for("dashboard"))


    return render_template("addarticle.html", form=form)

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    check = "select * from articles where author=%s and id=%s"
    result = cursor.execute(check,(session["username"], id))
    
    if result>0:
        check2 = "delete from articles where id=%s"
        cursor.execute(check2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("There is no such article or you are not authorized", "danger")
        return redirect(url_for("index"))

@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def edit(id):
    if request.method=="GET":
        cursor = mysql.connection.cursor()
        check = "select * from articles where id=%s and author=%s"
        result = cursor.execute(check,(id, session["username"]))
        if result == 0:
            flash("There is no such article or you are not authorized", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form=form)
    else:
        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data
        check2 = "update articles set title=%s, content=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(check2, (newtitle, newcontent, id))
        mysql.connection.commit()
        flash("Your article successfully updated", "success")
        return redirect(url_for("dashboard"))

#Create Form
class ArticleForm(Form):
    title = StringField("Article Title", validators=[validators.length(min=5, max=50)])
    content = TextAreaField("Content of Article", validators=[validators.length(min=50)])

#Search URL
@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        check ="select *from articles where title like '%"+ keyword +"%'"
        result = cursor.execute(check,)
        if result == 0:
            flash("Keyword not found", "warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles=articles)


if __name__ == "__main__":
    app.run(debug=True)