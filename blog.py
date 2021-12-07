from MySQLdb import cursors
from flask import Flask , render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from werkzeug.user_agent import UserAgent
from wtforms import Form , StringField,PasswordField,TextAreaField,validators 
from functools import wraps

#decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged in" in session:
            return f(*args, **kwargs)
        else:
            flash("önce giriş yap","danger")   
            return redirect(url_for("login")) 
    return decorated_function

#kullanıcı kayıt formu 
class Registerform(Form):
    name = StringField("isim soyisim",validators=[validators.length(min=3,max=26)])
    username = StringField("username",validators=[validators.length(5,35)])
    email = StringField("email",validators=[validators.length(5,30)])
    password = PasswordField("şifre giriniz",validators=[validators.equal_to("confirm","uyuşmadı"),validators.DataRequired("parola zorunludur.")])
    confirm = PasswordField("doğrulayınız")

#kullanıcı giriş formu 
class  Loginform(Form):
    username = StringField("kullancı adı")
    password = PasswordField("şifre")

#makale formu
class Addarticle(Form):
    title = StringField("makale başlığı",[validators.length(3)])
    content = TextAreaField("makale içeriği",[validators.length(3)])







app = Flask(__name__)
app.secret_key = "ybblog"
app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "Usersdb"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)




numbers = [{"id":1,"general":"one"},{"id":2,"general":"two"} ]
@app.route("/")
def index():
    return render_template('index.html', numbers = numbers)

@app.route("/about")
def about():
    return render_template("about.html")

""" @app.route("/article/<string:id>")
def details(id):
    return "id:" +  id 

"""
#dashboard sayfası
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0 :
        articles = cursor.fetchall()

        return render_template("dashboard.html",articles = articles)
    return render_template("dashboard.html")


#kayıt ol sayfası 
@app.route("/register", methods=["GET","POST"])
def register():
    form = Registerform(request.form)
    if request.method == "POST" and form.validate():
        # girilen inputların veri tabanına kayıt edilmesi 
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into ybblog(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash('kayıt olundu.','success')



        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
#giriş yap bölümü 
@app.route('/login',methods=["GET","POST"])
def login():
    form = Loginform(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data
# girilen kullanıcı adı ile şifrenin database de olup olmama kontrolu 
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM ybblog where username = (%s)"
        sorgulama = cursor.execute(sorgu,(username,))
        if sorgulama > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if real_password == password:
                flash("başarıyla giriş yapıldı.","success")
                session["logged in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("şifre yanlış girildi.","danger")
            

        else :
            flash("böyle bir hesap bulunamadı","danger")
            return redirect(url_for("login"))



    return render_template("login.html",form = form )


#çıkış yap 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#makale görüntüleme
@app.route ("/article/<string:id>")
@login_required
def article (id):

    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result >0 :
        article = cursor.fetchone()
        return render_template("article.html", article = article) 
    else:
        return render_template("article.html")

#makale silme 
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("makale size ait degil","danger")
        return redirect(url_for("dashboard"))

#makale güncelle 
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where author = %s and id = %s"
        result = cursor.execute(sorgu,(session["username"],id))
        if result == 0:
            flash("bu makale yok veya sana ait degil")
            return redirect(url_for("dashboard"))
        else:
            article = cursor.fetchone()
            form = Addarticle()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        form2 = Addarticle(request.form)
        new_title = form2.title.data
        new_content = form2.content.data
        cursor2 = mysql.connection.cursor()
        sorgu2 = "update articles set title = %s , content = %s where id = %s"
        cursor2.execute(sorgu2,(new_title,new_content,id))
        mysql.connection.commit()
        flash("makale güncellendi","success")
        return redirect(url_for("dashboard"))


 

#makale ekle 
@app.route("/addarticle",methods=("POST","GET"))
@login_required
def addarticle():
    form = Addarticle(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title, session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("makale başarıyla kaydedildi.","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

#makaleler
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles"
    result = cursor.execute(sorgu)
    if result > 0 :
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles )
    return render_template("articles.html")

    
#arama motoru
@app.route("/search",methods=["GET","POST"])
def search():
    
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where title like '%" + keyword +  "%' "
        result = cursor.execute(sorgu)
        if result == 0:
            flash("aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)


    
    
 
if __name__ == '__main__':
    app.run(debug=True)

