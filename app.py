from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import re
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for /api/*

# Set OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY')  
ESP32_IP = os.getenv('ESP32_IP')  

if openai.api_key is None:
    raise EnvironmentError("OPENAI_API_KEY not set")
if ESP32_IP is None:
    raise EnvironmentError("ESP32_IP not set")

# ✅ Global dictionary to store device states
device_states = {
    "roomLight": False,
    "mainLight": False,
    "motor1": False,
    
}

@app.route('/')
def index():
    return "Welcome! Your Flask app is running on Render."

# Helper function to clean OpenAI response
def clean_openai_response(response_text):
    cleaned_response = re.sub(r'(opening curly bracket|closing curly bracket|opening bracket|closing bracket)', '', response_text, flags=re.IGNORECASE)
    return cleaned_response.strip()

# ✅ Function to control ESP32 devices and update state
def control_esp32_device(device_type, device_number, action):
    global device_states

    try:
        if device_type == 'led':
            if device_number == 1:
                device_states["roomLight"] = (action == 'on')
                requests.get(f"{ESP32_IP}/led1/{action}")
                return f"Turning {'on' if action == 'on' else 'off'} Room Light"

            elif device_number == 2:
                device_states["mainLight"] = (action == 'on')
                requests.get(f"{ESP32_IP}/led2/{action}")
                return f"Turning {'on' if action == 'on' else 'off'} Main Light"

        elif device_type == 'motor':
            if device_number == 1:
                device_states["motor1"] = (action == 'on')
                requests.get(f"{ESP32_IP}/motor1/{action}")
                return f"Turning {'on' if action == 'on' else 'off'} Motor 1"

            

        return "Invalid command"
    
    except Exception as e:
        app.logger.error(f"Error sending command to ESP32: {str(e)}")
        return "Failed to communicate with ESP32"

# ✅ API to get the current device states
@app.route('/api/get_device_states', methods=['GET'])
def get_device_states():
    return jsonify(device_states)

@app.route('/api/openai', methods=['POST'])
def handle_openai():
    try:
        data = request.get_json()
        if not data or 'current_question' not in data:
            return jsonify({'error': 'Invalid request format, "current_question" key is missing'}), 400

        user_message = data['current_question'].lower()
        previous_conversation = data.get('previous_conversation', '')

        # ✅ Update device states when a command is executed
        if "turn on room light" in user_message:
            response_message = control_esp32_device('led', 1, 'on')
            return jsonify({'response': response_message})

        elif "turn off room light" in user_message:
            response_message = control_esp32_device('led', 1, 'off')
            return jsonify({'response': response_message})

        elif "turn on main light" in user_message:
            response_message = control_esp32_device('led', 2, 'on')
            return jsonify({'response': response_message})

        elif "turn off main light" in user_message:
            response_message = control_esp32_device('led', 2, 'off')
            return jsonify({'response': response_message})

        elif "turn on motor 1" in user_message:
            response_message = control_esp32_device('motor', 1, 'on')
            return jsonify({'response': response_message})

        elif "turn off motor 1" in user_message:
            response_message = control_esp32_device('motor', 1, 'off')
            return jsonify({'response': response_message})

        elif "kill power" in user_message:
            response_message_led1 = control_esp32_device('led', 1, 'off')
            response_message_led2 = control_esp32_device('led', 2, 'off')
            response_message_motor1 = control_esp32_device('motor', 1, 'off')
            
            return jsonify({'response': f"{response_message_led1}, {response_message_led2}, {response_message_motor1}, and {response_message_motor2}"})

        elif "full power" in user_message:
            response_message_led1 = control_esp32_device('led', 1, 'on')
            response_message_led2 = control_esp32_device('led', 2, 'on')
            response_message_motor1 = control_esp32_device('motor', 1, 'on')
            
            return jsonify({'response': f"{response_message_led1}, {response_message_led2}, {response_message_motor1}, and {response_message_motor2}"})       

        full_conversation = f"Previous: {previous_conversation}\nCurrent: {user_message}"

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "act as JAVIS, your name is 'LUNA', your creaters are student from J D T Polytechnic college and you should respond conversationally without unnecessary punctuation descriptions like 'opening' and 'closing'."},
                {"role": "user", "content": full_conversation}
            ],
            max_tokens=200
        )

        openai_response = response['choices'][0]['message']['content'].strip()
        cleaned_response = clean_openai_response(openai_response)

        return jsonify({'response': cleaned_response})

    except Exception as e:
        app.logger.error(f"Error while communicating with OpenAI: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
