from flask import Flask, session, render_template, request, jsonify, redirect
from datetime import date
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import json
from bson.objectid import ObjectId

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
app = Flask(__name__, template_folder='templates', static_folder='static')

app.secret_key = 'crisis_management'

app.config["MONGO_URI"] = MONGO_URL
mongo = PyMongo(app)

donations = mongo.db.donations
donors = mongo.db.donors
help_collection = mongo.db.help_collection
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
    return redirect('/')  # Redirect to the login page

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
    print(ngos)
    ngo_names = [ngo['Name'] for ngo in ngos]  # Extracting the names from the result
    print(ngo_names)
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
    ngo = session['ngo']  
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

@app.route('/profile')
def profile():
    email = session['loggedEmail']  # Get logged user email from session
    victimData = victims.find_one({'email': email})
    # victimData = list(victim_data)
    ngoData = ngos.find_one({'Email': email})
    # ngoData = list(ngo_data)
    donorData = donors.find_one({'Email': email})
    # donorData = list(donor_data)
    message = ""

    if victims.count_documents({'email': email}) == 0 and ngos.count_documents({'Email': email}) == 0 and donors.count_documents({'Email': email}) == 0:
        message = "You're not registered as a victim, NGO, or donor. You are just a user."
        return render_template('profile.html', email=email, name=session['loggedUser'], message=message)

    # Condition for victim
    elif  ngos.count_documents({'Email': email}) == 0 and donors.count_documents({'Email': email}) == 0:
        victim = victims.find_one({'email': email})
        victimId = victim['_id']  # Assuming _id is the victim_id in MongoDB
        victimRequestApproval = help_collection.find({'victim_id': victimId})

        victimRequestApproval = list(victimRequestApproval)

        if not victimRequestApproval:
            print("Request not approved")
            message = "Your request is still pending"
            return render_template('profile.html', email=email, name=session['loggedUser'], message=message)
         
        print(victimRequestApproval)
        ngoId = victimRequestApproval[0]['ngo_id']
        approvalDate = victimRequestApproval[0]['date']
        ngoName = ngos.find_one({'_id': ngoId})['Name']
        message = f"Your request was approved on {approvalDate} by {ngoName} NGO."
        return render_template('profile.html', email=email, name=session['loggedUser'], message=message)
    # Condition for NGOs
    elif victims.count_documents({'email': email}) == 0 and donors.count_documents({'Email': email}) == 0:
        victims_list = victims.find({})
        victim_details = []
        for victim in victims_list:
            incident_details = incidents.find({'victim_id': victim['_id']})
            
            if len(list(incident_details)) > 0 :
                victim_details.append((victim, list(incident_details)))
        return render_template('ngoProfile.html', victim_details=victim_details)

    # Condition for donors
    elif victims.count_documents({'email': email}) == 0 and  ngos.count_documents({'Email': email}) == 0:
        donor = donors.find_one({'Email': email})
        donorId = donor['_id']
        donorName = donor['Name']
        donation_details = []
        donationRecords = donations.find({'donor_id': donorId})

        for donation in donationRecords:
            ngoName = ngos.find_one({'_id': donation['ngo_id']})['Name']
            donation_details.append((donation, ngoName))

        return render_template('donorProfile.html', donation_details=donation_details, donorName=donorName, donorEmail=email)


@app.route('/help/<id>')
def help(id):
    victimID = id
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    ngoData = ngos.find_one({'Email': session['loggedEmail']})
    ngoID = ngoData['_id']
    # Insert help record into the help collection
    help_collection.insert_one({'victim_id': ObjectId(victimID), 'ngo_id': ngoID, 'date': today_str})

    # Delete incidents associated with the victim
    incidents.delete_many({'victim_id': ObjectId(victimID)})

    return redirect('/profile')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',debug=True)
