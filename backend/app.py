from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth  # Add auth for Firebase Authentication (Optional)
import os

# Initialize Firebase
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), './db/secrets/event-booking-system-833ad-firebase-adminsdk-kwuui-dd652edcd1.json'))
firebase_admin.initialize_app(cred)

db = firestore.client()
print("Firebase configuration loaded successfully.")

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Event Booking API!"})

# Endpoint to create a new event
@app.route('/create_event', methods=['POST'])
def create_event():
    data = request.get_json()
    print("Received data:", data)  # Debugging print

    try:
        event_ref, event_id = db.collection('events').add(data)
        print(f"Event added with ID: {event_id}")  # Debugging print

        return jsonify({'id': str(event_id), 'event': data}), 201
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': f'Failed to add event: {str(e)}'}), 500

# Endpoint to retrieve all events
@app.route('/events', methods=['GET'])
def get_events():
    try:
        events = db.collection('events').get()
        event_list = [{**event.to_dict(), 'id': event.id} for event in events]
        return jsonify(event_list), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': f'Failed to fetch events: {str(e)}'}), 500

# Endpoint to book tickets for an event
@app.route('/book_event', methods=['POST'])
def book_event():
    data = request.get_json()
    event_id = data.get('event_id')
    tickets_requested = data.get('tickets')

    try:
        # Fetch the event from Firestore
        event_ref = db.collection('events').document(event_id)
        event = event_ref.get().to_dict()

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        available_tickets = event.get('available_tickets', 0)

        if available_tickets >= tickets_requested:
            # Update the number of available tickets
            event_ref.update({
                'available_tickets': available_tickets - tickets_requested
            })

            # Store booking information in Firestore
            db.collection('bookings').add({
                'event_id': event_id,
                'tickets': tickets_requested,
                'user_id': data.get('user_id')
            })

            return jsonify({'message': 'Booking successful'}), 200
        else:
            return jsonify({'error': 'Not enough tickets available'}), 400

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': f'Failed to book tickets: {str(e)}'}), 500

# Endpoint to delete an event (Optional)
@app.route('/delete_event/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        db.collection('events').document(event_id).delete()
        return jsonify({'message': f'Event {event_id} deleted successfully'}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': f'Failed to delete event: {str(e)}'}), 500
    
# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        # Create user with Firebase Admin SDK
        user = auth.create_user(email=email, password=password)
        return jsonify({
            "message": "User registered successfully",
            "user_id": user.uid
        }), 201

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to register user: {str(e)}"}), 500

# User login endpoint (simulated token generation)
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        # Simulate login with Firebase Admin SDK
        user = auth.get_user_by_email(email)
        return jsonify({
            "message": "Login successful",
            "user_id": user.uid
        }), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to log in user: {str(e)}"}), 500


def authenticate_user(f):
    def wrapper(*args, **kwargs):
        id_token = request.headers.get('Authorization').split(" ")[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401
    return wrapper

if __name__ == "__main__":
    app.run(debug=True)