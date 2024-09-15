from flask import Flask, request, jsonify
import openai
import re
import requests

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key =  os.getenv('OPENAI_API_KEY')  # Replace with your actual OpenAI API key

# ESP32 IP address (replace with your actual ESP32 IP address)
ESP32_IP = "http://192.168.43.98"  # Replace with the IP address of your ESP32

# Helper function to clean the OpenAI response
def clean_openai_response(response_text):
    # Remove specific unwanted phrases like "opening curly bracket", "closing curly bracket"
    cleaned_response = re.sub(r'(opening curly bracket|closing curly bracket|opening bracket|closing bracket)', '', response_text, flags=re.IGNORECASE)
    
    # Strip excess whitespace
    cleaned_response = cleaned_response.strip()

    return cleaned_response

# Function to control the ESP32 LEDs and motors
def control_esp32_device(device_type, device_number, action):
    try:
        if device_type == 'led':
            if device_number == 1 and action == 'on':
                requests.get(f"{ESP32_IP}/led1/on")
                return "Turning on Light in room"
            elif device_number == 1 and action == 'off':
                requests.get(f"{ESP32_IP}/led1/off")
                return "Turning off LED1"
            elif device_number == 2 and action == 'on':
                requests.get(f"{ESP32_IP}/led2/on")
                return "Turning on LED2"
            elif device_number == 2 and action == 'off':
                requests.get(f"{ESP32_IP}/led2/off")
                return "Turning off LED2"
        elif device_type == 'motor':
            if device_number == 1 and action == 'on':
                requests.get(f"{ESP32_IP}/motor1/on")
                return "Turning on Motor 1"
            elif device_number == 1 and action == 'off':
                requests.get(f"{ESP32_IP}/motor1/off")
                return "Turning off Motor 1"
            elif device_number == 2 and action == 'on':
                requests.get(f"{ESP32_IP}/motor2/on")
                return "Turning on Motor 2"
            elif device_number == 2 and action == 'off':
                requests.get(f"{ESP32_IP}/motor2/off")
                return "Turning off Motor 2"
        return "Invalid command"
    except Exception as e:
        app.logger.error(f"Error while sending command to ESP32: {str(e)}")
        return "Failed to communicate with ESP32"

@app.route('/api/openai', methods=['POST'])
def handle_openai():
    try:
        # Extract the user's message from the POST request
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({'error': 'Invalid request format, "message" key is missing'}), 400

        user_message = data['message'].lower()

        # If the message contains LED or Motor commands, handle it
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

        elif "turn on motor 2" in user_message:
            response_message = control_esp32_device('motor', 2, 'on')
            return jsonify({'response': response_message})

        elif "turn off motor 2" in user_message:
            response_message = control_esp32_device('motor', 2, 'off')
            return jsonify({'response': response_message})

        elif "kill power" in user_message:
            response_message_led1 = control_esp32_device('led', 1, 'off')
            response_message_led2 = control_esp32_device('led', 2, 'off')
            response_message_motor1 = control_esp32_device('motor', 1, 'off')
            response_message_motor2 = control_esp32_device('motor', 2, 'off')
            return jsonify({'response': f"{response_message_led1}, {response_message_led2}, {response_message_motor1}, and {response_message_motor2}"})

        elif "full power" in user_message:
            response_message_led1 = control_esp32_device('led', 1, 'on')
            response_message_led2 = control_esp32_device('led', 2, 'on')
            response_message_motor1 = control_esp32_device('motor', 1, 'on')
            response_message_motor2 = control_esp32_device('motor', 2, 'on')
            return jsonify({'response': f"{response_message_led1}, {response_message_led2}, {response_message_motor1}, and {response_message_motor2}"})       

        # Make OpenAI request for general queries
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "act as JAVIS, your name is 'LUNA' and you should respond conversationally without unnecessary punctuation descriptions like 'opening' and 'closing'."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200
        )

        # Extract the response message from OpenAI's response
        openai_response = response['choices'][0]['message']['content'].strip()

        # Clean the OpenAI response before sending it to the Android app
        cleaned_response = clean_openai_response(openai_response)

        # Send the cleaned response back to the Android app
        return jsonify({'response': cleaned_response})

    except Exception as e:
        app.logger.error(f"Error while communicating with OpenAI: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)