from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re      
    
                       
app = Flask(__name__)
app.secret_key = "big secret"
bcrypt = Bcrypt(app)    


@app.route('/')
def index():
    print('In Index function')
    print(session)
 
    return render_template('index.html')


@app.route('/processreg', methods=['POST'])
def process():
    print('In process function')
    print(request.url)
    print(request.form)
    
    isValid = True

    firstname = request.form["firstname"].strip()
    lastname = request.form["lastname"].strip()    
    email = request.form["email"].strip()
    password = request.form["password"].strip()
    cnfmpassword = request.form["cnfmpassword"].strip()

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
    # PASSWORD_REGEX = re.compile(r'.[a-z]{1}.*[A-Z]{1}.*\d*.*$')
    #PASSWORD_REGEX = re.compile(r"((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W]).{8,64})")
    # /((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W]).{8,64})/g

    # Ensure that password is 8 to 64 characters long and contains a mix of upper and lower case characters, one numeric and one special character
  
    
    if len(firstname) < 2 or not firstname.isalpha():
        flash('First name has to be 2 or more letters only', category='firstname')
        isValid = False

    if len(lastname) < 2 or not lastname.isalpha():
        flash('Last name name has to be 2 or more letters only', category='lastname')
        isValid = False

    if not EMAIL_REGEX.match(email):    # test whether a field matches the pattern
        flash("Invalid email address ()@(0.()!", category='email_reg')
        isValid = False

    if len(password) < 8:
        flash('Password length has to be a minimum of 8 characters', category='password')
        isValid = False

    # if not PASSWORD_REGEX.match(password):
    #     flash("Password must contain at least 1 number, 1 lowercase and 1 uppercase character")
    #     isValid = False

    if password != cnfmpassword:
        flash('Password fields do not match!', category='cnfmpassword')
        isValid = False

    if not isValid:
        return redirect('/')

    #If isValid is True proceed
    hashpass = bcrypt.generate_password_hash(password)
    print(f'hashpass = {hashpass}')

    # result = bcrypt.check_password_hash(hashpass, password)
    # print(result)
    
    query = 'SELECT count(*) c FROM users WHERE email =%(email)s'

    data = {
        "email" : request.form["email"].strip()
    }

    mysql = connectToMySQL('wall')
    users = mysql.query_db(query, data)

    print(users, users[0]['c'])

    if users[0]['c'] == 0:
        query = 'INSERT INTO users(firstname, lastname, email, password) VALUES(%(firstname)s, %(lastname)s, %(email)s, %(password)s);'

        data = {
            "firstname" : request.form["firstname"].strip(),
            "lastname" : request.form["lastname"].strip(),
            "email" : request.form["email"].strip(),
            "password" : hashpass
        }

        mysql = connectToMySQL('wall')
        users = mysql.query_db(query, data)

        print(f"Inserted user id {users} ")

        session['id'] = users
        session['firstname'] = data['firstname']
        session['lastname'] = data['lastname']
        session['email'] = data['email']

        return redirect('/welcome')

    else:
        print('Email exists')
        flash('Email already exists!', category='email_reg')
        return redirect('/')

  


@app.route('/processlogin', methods=['POST'])
def processlogin():
    print('In processlogin function')
    print(request.url)
    print(request.form)

    email = request.form["email"].strip()
    password = request.form["password"].strip()
    
    query = 'SELECT * FROM users WHERE email =%(email)s'

    data = {
        "email" : email
    }

    mysql = connectToMySQL('wall')
    users = mysql.query_db(query, data)

    print(users, len(users))

    if len(users) == 0:
        flash('Email or Password is invalid!', 'email_log')
        return redirect('/')
   
    hashpass = users[0]['password']
    print(hashpass)
    result = bcrypt.check_password_hash(hashpass, password)
    print(result)

    if result:
        session['id'] = users[0]['id']
        session['firstname'] = users[0]['firstname']
        session['lastname'] = users[0]['lastname']
        session['email'] = users[0]['email']

        # query = 'SELECT count(*) c FROM messages WHERE user_from = %(id)s'

        # data = {
        #     "id" : users[0]['id']
        # }

        # mysql = connectToMySQL('wall')
        # sent_message_count = mysql.query_db(query, data)

        # session['sent_message_count'] = sent_message_count[0]['c']

        # return render_template('welcome.html')
        return redirect('/welcome')
        
    else:
        flash('Email or Password is invalid!')
        return redirect('/')


@app.route('/welcome')
def welcome():
    print('In welcome function')
    print(session)
    print(len(session))

    if len(session) == 0:
        return redirect('/')

    #Left section
    #Get count of messages received by logged in user
    query = 'SELECT count(*) c FROM messages WHERE user_to = %(id)s ORDER BY modified_at desc;'

    data = {
        "id" : session['id']
    }

    mysql = connectToMySQL('wall')
    received_message_count = mysql.query_db(query, data)

    print(f'******** {received_message_count}')
    session['received_message_count'] = received_message_count[0]['c']


    #Get messages received by logged in user
    # query = 'SELECT * FROM messages WHERE user_to = %(id)s ORDER BY modified_at desc;'
    query = '''
        SELECT u.id as user_from_id, u.firstname, u.lastname, m.id as message_id, m.`message_text`, m.modified_at,
        CASE
            WHEN TIMESTAMPDIFF(second,m.modified_at,now()) < 60 THEN CONCAT(CAST(TIMESTAMPDIFF(SECOND,m.modified_at,NOW()) AS CHAR) , ' second(s)')
            WHEN TIMESTAMPDIFF(minute,m.modified_at,now()) < 60 THEN CONCAT(CAST(TIMESTAMPDIFF(MINUTE,m.modified_at,NOW()) AS CHAR) , ' minute(s)')
            WHEN TIMESTAMPDIFF(hour,m.modified_at,now()) < 24 THEN CONCAT(CAST(TIMESTAMPDIFF(HOUR,m.modified_at,NOW()) AS CHAR), ' hour(s)')
            WHEN TIMESTAMPDIFF(day,m.modified_at,now()) < 30 THEN CONCAT(CAST(TIMESTAMPDIFF(DAY,m.modified_at,NOW()) AS CHAR), ' day(s)')
            ELSE CONCAT(CAST(TIMESTAMPDIFF(month,m.modified_at,now()) AS CHAR), ' month(s)')
        END as timediff 
        FROM messages m
        JOIN users u
        ON m.user_from = u.id
        WHERE user_to = %(id)s ORDER BY m.modified_at desc, m.id desc;
    '''

    data = {
        "id" : session['id']
    }

    mysql = connectToMySQL('wall')
    messages_received = mysql.query_db(query, data)

    print(f'******** Messages Received: {messages_received}')


    #Right section
    #Get count of messages sent by logged in user
    query = 'SELECT count(*) c FROM messages WHERE user_from = %(id)s'

    data = {
        "id" : session['id']
    }

    mysql = connectToMySQL('wall')
    sent_message_count = mysql.query_db(query, data)

    print(f'******** {sent_message_count}')
    session['sent_message_count'] = sent_message_count[0]['c']

    #Get user list
    query = 'SELECT * FROM users WHERE id != %(id)s ORDER BY firstname, lastname, id;'

    data = {
        "id" : session['id']
    }

    mysql = connectToMySQL('wall')
    users = mysql.query_db(query, data)

    print(f'******** {users}')

 
    return render_template('wall.html', users = users, messages_received = messages_received)


@app.route('/logout')
def logout():
    print('In logout function')
    print(session)

    session.clear()

    print(session)
 
    return redirect('/')


@app.route('/sendmessage', methods=['POST'])
def process_sendmessage():
    print('In process_sendmessage function')
    print(request.url)
    print(request.form)

    user_to = request.form["user_to"].strip()
    msg = request.form["msg"].strip()
    
    #Save messsage to database
    query = 'INSERT INTO messages(user_from, user_to, message_text) VALUES(%(user_from)s, %(user_to)s, %(msg)s);'

    data = {
        "user_from" : session["id"],
        "user_to" : int(user_to),
        "msg" : msg
    }

    mysql = connectToMySQL('wall')
    msg_id = mysql.query_db(query, data)

    print(f"Inserted message id {msg_id} ")

    return redirect('/welcome')


@app.route('/deletemessage/<message_id>')
def process_deletemessage(message_id):
    print('In process_deletemessage function')
    print(f'***************************** - {request.url}')
    print(request.form)
    
    #delete messsage from database if message was recieved by logged in user
    query = 'DELETE FROM messages WHERE id = %(msg_id)s and user_to = %(user_to)s'

    data = {
        "user_to" : session["id"],
        "msg_id" : message_id
    }

    mysql = connectToMySQL('wall')
    msg_id = mysql.query_db(query, data)

    print(f"Deleted message id {msg_id} ")

    return redirect('/welcome')




if __name__=="__main__":
    app.run(debug=True)