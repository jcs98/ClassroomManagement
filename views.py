from app import app, mysql
from flask import render_template, flash, request, redirect, url_for, session, logging
from passlib.hash import sha256_crypt
from functools import wraps
#from models import Member
from forms import RegisterForm, ArticleForm
 # @app.route('/')
# def index():
# 	firstmember = Member.query.first()
# 	return '<h1>The first member is:'+ firstmember.name +'</h1>'
 # Index
@app.route('/')
def index():
	return  render_template('home.html')
 # About
@app.route('/about')
def about():
	return  render_template('about.html')
 # Articles
@app.route('/articles')
def articles():
		# Create cursor
	cur = mysql.connection.cursor()
 	# Get articles
	result = cur.execute("SELECT * FROM articles")
 	articles = cur.fetchall()
 	if result > 0:
		return render_template('articles.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('articles.html', msg=msg)
	# Close connection
	cur.close()
 # Single Article
@app.route('/article/<string:id>/', methods=['GET', 'POST'])
def article(id):
	# Create cursor
	cur = mysql.connection.cursor()
	if request.method == 'POST':
		comment = request.form['comment']
		if(comment != ''):
			# Execute
			cur.execute("INSERT INTO comments(article_id, body, author) VALUES(%s, %s, %s)", (id, comment, session['username']))
			# Commit to DB
			mysql.connection.commit()
 	# Get article
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
 	article = cur.fetchone()
	cur.execute("SELECT * FROM comments WHERE article_id=%s ORDER BY id", [id])
	comments = cur.fetchall()
	cur.execute("SELECT * FROM submissions WHERE assignment_id=%s", [id])
	submissions = cur.fetchall()
	# Close connection
	cur.close()
 	return  render_template('article.html', article=article, comments=comments, submissions=submissions)
 # Register
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Execute query
		if form.isTeacher.data:
			cur.execute("INSERT INTO teachers(name , email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
		else:
			cur.execute("INSERT INTO users(name , email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
 		# Commit to DB
		mysql.connection.commit()
 		# Close connection
		cur.close()
 		flash('You are now registered and can log in', 'success')
 		return redirect(url_for('login'))
	return render_template('register.html', form=form)
 # Login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form Fields (not using WTForms)
		username = request.form['username']
		password_candidate = request.form['password']
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Get user by username
		if request.form.get('isTeacher'):
			result = cur.execute("SELECT * FROM teachers WHERE username = %s", [username])
		else:
			result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
 		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']
 			# Compare passwords
			if sha256_crypt.verify(password_candidate, password):
				# Passed
				session['logged_in'] = True
				session['username'] = username
				if request.form.get('isTeacher'):
					session['isTeacher'] = True
				else:
					session['isTeacher'] = False

 				flash('You are now logged in', 'success')
				return redirect(url_for('articles'))
			else:
				error = 'Invlaid login'
				return render_template('login.html', error=error)
			# Close connection
			cur.close()
 		else:
			error = 'Username not found'
			return render_template('login.html', error=error)
 	return render_template('login.html')
 # Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap
 # Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))
 # Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	# Create cursor
	cur = mysql.connection.cursor()
 	# Get articles
	result = cur.execute("SELECT * FROM articles WHERE author=%s", (session['username'],))
 	articles = cur.fetchall()
 	if result > 0:
		return render_template('dashboard.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('dashboard.html', msg=msg)
	# Close connection
	cur.close()
 # Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Execute
		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
 		# Commit to DB
		mysql.connection.commit()
 		# Close connection
		cur.close()
 		flash('Article Created', 'success')
 		return redirect(url_for('dashboard'))
 	return render_template('add_article.html', form=form)
 # Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Get article by id
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
 	article = cur.fetchone()
 	# Get form
	form = ArticleForm(request.form)
 	# Populate article form fields
	form.title.data = article['title']
	form.body.data = article['body']
 	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Execute
		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
 		# Commit to DB
		mysql.connection.commit()
 		# Close connection
		cur.close()
 		flash('Article Updated', 'success')
 		return redirect(url_for('dashboard'))
 	return render_template('edit_article.html', form=form)
 # Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Execute
	cur.execute("DELETE FROM articles WHERE id=%s", [id])
 	# Commit to DB
	mysql.connection.commit()
 	# Close connection
	cur.close()
 	flash('Article Deleted', 'success')
 	return redirect(url_for('dashboard'))

 # Delete Comment
@app.route('/delete_comment/<string:id>/<string:article_id>', methods=['POST'])
@is_logged_in
def delete_comment(id, article_id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Execute
	cur.execute("DELETE FROM comments WHERE id=%s", [id])
 	# Commit to DB
	mysql.connection.commit()
 	# Close connection
	cur.close()
 	return redirect(url_for('article', id=article_id))

# Submit Assignment
@app.route('/submit_assignment/<string:assignment_id>', methods=['POST'])
@is_logged_in
def submit_assignment(assignment_id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Execute
	cur.execute("INSERT INTO submissions(assignment_id, student_name) VALUES(%s, %s)", (int(assignment_id), session['username']))
 	# Commit to DB
	mysql.connection.commit()
 	# Close connection
	cur.close()
	flash('Assignment Submitted!', 'success')
 	return redirect(url_for('articles'))