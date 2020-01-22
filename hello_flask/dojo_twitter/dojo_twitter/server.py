from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from datetime import datetime
import re
from mysqlconnection import connectToMySQL

app = Flask(__name__)
app.secret_key = "Welcome to the thunder dome"
bcrpyt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_user', methods=['POST'])
def create_user():
    is_valid = True
    SpecialSym = ['$','@', '#', '%']
    
    if len(request.form['fname']) < 1:
        is_valid = False
        flash("Please enter a first name")
    
    if len(request.form['lname']) < 1:
        is_valid = False
        flash("Please enter a last name")
    
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address!")
    
    if len(request.form['pass']) < 5:
        is_valid = False
        flash("Password Must Be At Least 5 Characters")
    
    if request.form['cpass'] != request.form ['pass']:
        is_valid = False
        flash("Incorrect Password")
    
    if not request.form['fname'].isalpha():
        is_valid = False
        flash("First name can only contain alphabetic characters")
    
    if not request.form['lname'].isalpha():
        is_valid = False
        flash("Last name can only contain alphabetic characters")
    
    if not any(char.isdigit() for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one numeral') 
    
    if not any(char.isupper() for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one uppercase letter') 
    
    if not any(char.islower() for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one lowercase letter') 
    
    if not any(char in SpecialSym for char in request.form['pass']): 
        is_valid = False
        flash('Password should have at least one of the symbols $@#')
    
    mysql = connectToMySQL("dojo_twitter")
    validate_email_query = 'SELECT id_users FROM users WHERE email=%(email)s;'
    form_data = {
        'email': request.form['email']
    }
    existing_users = mysql.query_db(validate_email_query, form_data)

    if existing_users:
        is_valid = False
        flash("Email already in use")
    
    if not is_valid:
        return redirect("/")

    if is_valid:
        mysql = connectToMySQL("dojo_twitter")
        pw_hash = bcrpyt.generate_password_hash(request.form['pass'])
        query = "INSERT into users(first_name, last_name, email, password, created_at, updated_at) VALUES (%(fname)s, %(lname)s, %(email)s, %(password_hash)s, NOW(), NOW());"

        data = {
            "fname": request.form['fname'],
            "lname": request.form['lname'],
            "email": request.form['email'],
            "password_hash": pw_hash
        }
        result_id = mysql.query_db(query, data)
        flash("Successfully added:{}".format(result_id))
        return redirect("/success")
    return redirect("/")

@app.route('/login', methods=['POST'])
def login():
    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email": request.form['email'] }
    result = mysql.query_db(query,data)
    if result: 
        if bcrpyt.check_password_hash(result[0]['password'], request.form['pass']):
            session['user_id'] = result[0]['id_users']
            return redirect("/success")
    flash("You could not be logged in")
    return redirect("/")

@app.route('/success')
def success():
    if 'user_id' not in session: 
        return redirect("/")

    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT users.first_name FROM users WHERE id_users = %(uid)s"
    data = {
        'uid': session['user_id']
    }
    result = mysql.query_db(query,data)

    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT tweets.author, tweets.id_tweets, tweets.content, tweets.created_at, users.first_name, users.last_name FROM tweets JOIN users on tweets.author = users.id_users ORDER BY created_at DESC;"
    all_tweets = mysql.query_db(query)

    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT tweets_id_tweets FROM liked_tweets WHERE users_id_users = %(user_id)s"
    data = {
        'user_id': session['user_id']
    }
    results = mysql.query_db(query,data)
    liked_tweet_ids = [result['tweets_id_tweets'] for result in results]

    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT tweets_id_tweets, COUNT(tweets_id_tweets) AS like_count FROM liked_tweets GROUP BY tweets_id_tweets;"
    like_count = mysql.query_db(query)

    for tweet in all_tweets:
        td = datetime.now() - tweet['created_at']

        if td.seconds == 0:
            tweet['time_since_secs'] = 1
        if td.seconds < 60 and td.seconds > 0:
            tweet['time_since_secs'] = td.seconds
        if td.seconds < 3600:
            tweet['time_since_minutes'] = round(td.seconds/60)
        if td.seconds > 3660:
            tweet['time_since_hours'] = round(td.seconds/3600)
        if td.days > 0:
            tweet['time_since_days'] = td.days
        
        for like in like_count:
            if like['tweets_id_tweets']  == tweet['id_tweets']:
                tweet['like_count'] = like['like_count']
        
        if 'like_count' not in tweet:
            tweet['like_count'] = 0 
    if result:
        return render_template("dashboard.html", user_fn = result[0], all_tweets = all_tweets, liked_tweet_ids = liked_tweet_ids)
    else:
        return render_template("dashboard.html") 

@app.route('/tweets/create', methods=["POST"])
def create_tweet():
    is_valid = True
    if len(request.form['tweet']) < 1:
        is_valid = False
        flash("Tweet must be between 1-255 characters")
    if len(request.form['tweet']) > 255:
        is_valid = False
        flash("Tweet must be between 1-255 characters")

    if is_valid:
        mysql = connectToMySQL("dojo_twitter")
        query = "INSERT into tweets(content, author, created_at, updated_at) VALUES (%(tc)s, %(aid)s, NOW(), NOW());"

        data = {
            "tc": request.form['tweet'],
            "aid": session['user_id']
        }
        mysql.query_db(query, data)
        
    return redirect("/success")


@app.route('/like_tweet/<tweet_id>')
def like_tweet(tweet_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "INSERT INTO liked_tweets (users_id_users, tweets_id_tweets) VALUES (%(user_id)s, %(tweet_id)s);"
    data = {
        'user_id': session['user_id'],
        'tweet_id': tweet_id
    }
    mysql.query_db(query,data)
    return redirect("/success")

@app.route('/unlike_tweet/<tweet_id>')
def unlike_tweet(tweet_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "DELETE FROM liked_tweets WHERE users_id_users = %(user_id)s AND tweets_id_tweets = %(tweet_id)s;"
    data = {
        'user_id': session['user_id'],
        'tweet_id': tweet_id
    }
    mysql.query_db(query, data)
    return redirect("/success")

@app.route('/edit_tweet/<tweet_id>')
def edit_tweet(tweet_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT * FROM tweets WHERE id_tweets = %(t_id)s;"
    data = { 
        't_id': tweet_id,
    }
    tweet_data = mysql.query_db(query,data)
    return render_template("edit.html", tweet_data = tweet_data[0])

@app.route('/update_tweet/<tweet_id>', methods=["POST"])
def update_tweet(tweet_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "UPDATE tweets SET content = %(content)s, updated_at = NOW() WHERE tweets.id_tweets = %(t_id)s;"
    data = {
        'content': request.form['tweet'],
        't_id': tweet_id
    }
    mysql.query_db(query,data)
    return redirect('/success')

@app.route('/delete_tweet/<tweet_id>')
def delete_tweet(tweet_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "DELETE FROM tweets WHERE id_tweets = %(t_id)s AND author = %(u_id)s;"
    data = { 
        't_id': tweet_id,
        'u_id': session['user_id']
    }
    mysql.query_db(query,data)
    return redirect('/success')

@app.route('/tweet_details/<tweet_id>') 
def tweet_details(tweet_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT tweets.author, tweets.id_tweets, tweets.content, tweets.created_at, users.first_name, users.last_name FROM tweets JOIN users on tweets.author = users.id_users WHERE tweets.id_tweets = %(t_id)s ORDER BY created_at DESC;"
    data = {
        't_id': tweet_id 
    }
    tweet = mysql.query_db(query, data)
    if tweet:
        tweet = tweet[0]

    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT users.first_name, users.last_name FROM liked_tweets JOIN users on liked_tweets.users_id_users = users.id_users WHERE tweets_id_tweets = %(t_id)s;"
    data = {
            't_id': tweet_id
    }
    user_who_have_liked = mysql.query_db(query,data)
    return render_template("tweet_details.html", tweet = tweet, user_who_have_liked = user_who_have_liked)

@app.route('/users')
def display_users():
    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT user_followers.followed FROM user_followers WHERE follower = %(uid)s;"
    data = {
        'uid': session['user_id']
    }
    result = mysql.query_db(query,data)
    users_already_followed = [user_id['followed'] for user_id in result]

    mysql = connectToMySQL("dojo_twitter")
    query = "SELECT users.first_name, users.last_name, users.email, users.id_users FROM users WHERE users.id_users != %(uid)s"
    data = {
        'uid': session['user_id']
    }
    all_users = mysql.query_db(query,data)

    followed = []

    for idx in range(len(all_users)):
        if all_users[idx]['id_users'] in users_already_followed:
            followed.append(all_users[idx]['id_users'])

    
    return render_template("users.html", all_users = all_users, followed = followed)

@app.route('/follow/<user_id>')
def follow_user(user_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "INSERT INTO user_followers (follower, followed) VALUES (%(follower)s, %(followed)s)"
    data = {
        'follower': session['user_id'],
        'followed': user_id
    }
    mysql.query_db(query,data)
    return redirect("/users")

@app.route('/unfollow/<user_id>')
def unfollow_user(user_id):
    mysql = connectToMySQL("dojo_twitter")
    query = "DELETE FROM user_followers WHERE follower = %(follower)s AND followed = %(followed)s"
    data = {
        'follower': session['user_id'],
        'followed': user_id
    }
    mysql.query_db(query, data)
    return redirect("/users")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged yourself out")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)