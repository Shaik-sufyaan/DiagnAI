from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/interaction', methods=['GET'])

def get_data():
    # Sample data to send back
    data = {
        "message": "Hello from Flask!",
        "numbers": [1, 2, 3, 4, 5]
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
