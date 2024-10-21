from flask import Flask, session, render_template, request, jsonify, redirect
from datetime import date
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import json

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
app = Flask(__name__, template_folder='templates', static_folder='static')

app.secret_key = 'crisis_management'

app.config["MONGO_URI"] = MONGO_URL
mongo = PyMongo(app)

donations = mongo.db.donations
donors = mongo.db.donors
help = mongo.db.help
incidents = mongo.db.incidents
ngos = mongo.db.ngos
user_log = mongo.db.user_log
users = mongo.db.users
victims = mongo.db.victims

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('loggedUser', None)  # Remove the user from session
    return redirect('/login')  # Redirect to the login page

@app.route('/victim')
def victim():
    return render_template('victim.html')

@app.route('/incident')
def incident():
    return render_template('incident.html')

@app.route('/donation')
def donation():
    # Fetching donor information from MongoDB
    email = session['loggedEmail']
    donor = mongo.db.donors.find_one({'Email': email})
    
    # If the donor doesn't exist, insert the new donor record
    if not donor:
        loggedUser = session['loggedUser']
        mongo.db.donors.insert_one({'Name': loggedUser, 'Email': email})
    
    # Fetching all NGO names from the MongoDB ngos collection
    ngos = mongo.db.ngos.find({}, {'Name': 1, '_id': 0})  # Projection to return only the Name field
    
    ngo_names = [ngo['Name'] for ngo in ngos]  # Extracting the names from the result
    
    # Rendering the donor.html template and passing the list of NGO names
    return render_template('donor.html', ngos=ngo_names)


@app.route('/ngo/<id>')
def donate(id):
    # Replace "-" with a space and store it in the session
    session['ngo'] = id.replace("-", " ")
    return render_template('donation.html')



@app.route('/homePage')
def home_page():
    if 'loggedUser' in session:
        loggedUser = session['loggedUser']
        return render_template('homePage.html', loggedUser=loggedUser)
    else:
        return redirect('/login')  # Redirect to login if user is not logged in


@app.route('/donating')
def donating():
    return render_template('homePage.html')

@app.route('/ngoRegistration')
def ngo():
    return render_template('ngos.html')

@app.route('/register', methods=['POST'])
def registered():
    try:
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        
        # Check if the user already exists
        existing_user = users.find_one({'email': email})
        if existing_user:
            return jsonify({'message': 'User already exists!'}), 409
        
        # Insert new user
        user = {'name': name, 'email': email, 'password': password}
        users.insert_one(user)
        
        return render_template('index.html')
    
    except Exception as e:
        print(f"Error: {e}")  # Better for debugging
        return render_template('register.html'), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        # Fetch email and password from form
        email = request.form['email']
        password = request.form['password']

        # Find the user in MongoDB by email
        user = users.find_one({'email': email})

        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found!'}), 404
        
        # Compare the password (ensure you're handling hashed passwords in production)
        if user['password'] == password:  # Replace with proper password check if hashed
            session['loggedUser'] = user['name']
            session['loggedEmail'] = email # Store in session
            return redirect('/homePage')
        else:
            return jsonify({'message': 'Incorrect password!'}), 401

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'message': 'Internal server error'}), 500


        
@app.route('/donating', methods=['POST'])
def donating_to_ngo():
    # Fetching donor information
    email = session['loggedEmail']  # Make sure to retrieve email from the form
    donor = mongo.db.donors.find_one({'Email': email})
    if donor:
        donor_id = donor['_id']  # MongoDB ObjectId

    # Fetching NGO information
    ngo = request.form['ngo']  # Make sure to retrieve the NGO name from the form
    ngo_data = mongo.db.ngos.find_one({'Name': ngo})
    if ngo_data:
        ngo_id = ngo_data['_id']  # MongoDB ObjectId

    # Getting form data
    date = request.form['date']
    donation_type = request.form['focusArea']

    # Inserting donation record into the donations collection
    donation = {
        'donor_id': donor_id,
        'ngo_id': ngo_id,
        'donation_date': date,
        'donation_type': donation_type
    }
    mongo.db.donations.insert_one(donation)

    return render_template('homePage.html')

        
@app.route('/ngoRegistration', methods=['POST'])
def NGOregistered():
    try:
        # Fetch form data
        email = request.form['email']
        name = request.form['name']
        focusArea = request.form['focusArea']
        
        # Insert the new NGO record into MongoDB
        ngo = {
            'Name': name,
            'Email': email,
            'focus_area': focusArea
        }
        mongo.db.ngos.insert_one(ngo)  # Insert NGO into the 'ngos' collection
        
        # Success message
        message = "Registration successful!"
        return render_template('homePage.html', message=message)
    
    except Exception as e:
        print("Error:", e)
        message = "Registration failed. Please try again."
        return render_template('ngos.html', message=message)



@app.route('/victim', methods=['POST'])
def Victim():
    try:
        age = request.form['age']
        name = request.form['name']
        gender = request.form['gender']

        email = session['loggedEmail']

        # Insert the victim data into the collection
        victim_data = {
            'name': name,
            'age': age,
            'gender': gender,
            'email' : email
        }

        # Insert into MongoDB
        victims.insert_one(victim_data)

        message = "Registration successful!"
        return render_template('incident.html', message=message)
    except Exception as e:
        print("Error:", e)
        message = "Registration failed. Please try again."
        return render_template('victim.html', message=message)


@app.route('/incident', methods=['POST'])
def Incident():
    try:
        email = session['loggedEmail']  

        # Fetch the victim_id based on the logged-in user's email
        victim_data = victims.find_one({'email': email})
        victim_id = victim_data['_id']

        # Get the form data for the incident
        date = request.form['date']
        location = request.form['location']
        incident_type = request.form['type']

        # Insert the incident data into MongoDB
        incident_data = {
            'victim_id': victim_id,
            'date': date,
            'location': location,
            'type': incident_type
        }

        # Insert into MongoDB
        incidents.insert_one(incident_data)

        message = "Incident registration successful!"
        return render_template('homePage.html', message=message)

    except Exception as e:
        print("Error:", e)
        message = "Incident registration failed. Please try again."
        return render_template('incident.html', message=message)

    
# @app.route('/profile')
# def profile():
#     sql = "select victim_id from victims where email = %s"
#     val = (email,)
#     myCursor.execute(sql,val)
#     victimData = myCursor.fetchone()
#     sql = "select ngo_id from ngos where Email = %s"
#     val = (email,)
#     myCursor.execute(sql,val)
#     ngoData = myCursor.fetchone()
#     sql = "select donor_id from donors where Email = %s"
#     val = (email,)
#     myCursor.execute(sql,val)
#     donorData = myCursor.fetchone()
#     message = ""
#     if not victimData and not ngoData and not donorData:
#         message="Your not registered for ngo ,victim or donor your are just user"
#         return render_template('profile.html',email=email,name=loggedUser,message=message)
#     # condition  for victim
#     elif not ngoData and not donorData:
#         sql = "select victim_id from victims where email = %s"
#         val = (email,)
#         myCursor.execute(sql,val)
#         victimIdArr = myCursor.fetchone()
#         victimId = victimIdArr[0]
#         sql = "select ngo_id,date from help where victim_id = %s"
#         val = (victimId,)
#         myCursor.execute(sql,val)
#         victimRequestApproval = myCursor.fetchall()
#         if not victimRequestApproval:
#             print("request not approved")
#             message = "Your request is still pending"
#             return render_template('profile.html',email=email,name=loggedUser,message=message)
#         else :
#             print(victimRequestApproval)
#             ngoId = victimRequestApproval[0][0]
#             print(ngoId)
#             approvalDate = victimRequestApproval[0][1]
#             print(approvalDate)
#             sql = "select Name from ngos where ngo_id = %s"
#             val = (ngoId,)
#             myCursor.execute(sql,val)
#             ngoNameArr = myCursor.fetchone()
#             ngoName = ngoNameArr[0]
#             message = "Your request is approved on {} by {} Ngo".format(approvalDate, ngoName)
#             return render_template('profile.html',email=email,name=loggedUser,message=message)
#     # condition for ngos
#     elif not victimData and not donorData:
#         sql = "select * from victims"
#         myCursor.execute(sql)
#         victims = myCursor.fetchall()
#         victim_details = []
#         for victim in victims: 
#             sql = "select Date,Type,Location from incidents where victim_id = %s"
#             val=(victim[0],)
#             myCursor.execute(sql,val)
#             Details = myCursor.fetchall()
#             if Details:
#                 victim_details.append((victim,Details))
#         print(victim_details)
#         return render_template('ngoProfile.html',victim_details=victim_details)
#     # condition for donors
#     elif not victimData and not ngoData:
#         sql = "select donor_id,Name from donors where Email = %s"
#         val = (email,)
#         myCursor.execute(sql,val)
#         donorIdArr = myCursor.fetchall()
#         donorId = donorIdArr[0][0]
#         donorName = donorIdArr[0][1]
#         print(donorId)
#         sql = "select ngo_id,donation_date,donation_type from donations where donor_id = %s"
#         val=(donorId,)
#         myCursor.execute(sql,val)
#         donationDetailsArr = myCursor.fetchall()
#         print(donationDetailsArr)
#         donation_details = []
#         for donation in donationDetailsArr: 
#             sql = "select Name from ngos where ngo_id = %s"
#             val=(donation[0],)
#             myCursor.execute(sql,val)
#             ngoName = myCursor.fetchone()
#             donation_details.append((donation,ngoName))
#         return render_template('donorProfile.html',donation_details=donation_details,donorName=donorName,donorEmail=email)

# @app.route('/help/<id>')
# def help(id):
#     victimID = id
#     today = date.today()
    
#     sql = "select ngo_id from ngos where Email = %s"
#     val = (email,)
#     myCursor.execute(sql,val)
#     ngoIDArr = myCursor.fetchone()
#     ngoID = ngoIDArr[0]
    
#     sql = "insert into help(victim_id,ngo_id,date) values(%s,%s,%s)"
#     val=(victimID,ngoID,today)
#     myCursor.execute(sql,val)
#     mydb.commit()
    
#     sql = "delete from incidents where victim_id = %s"
#     val = (victimID,)
#     myCursor.execute(sql,val)
#     mydb.commit()
    
#     return redirect('/profile')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',debug=True)
