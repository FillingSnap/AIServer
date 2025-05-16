from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from Dockerized Flask!"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    return jsonify({"result": f"AI 일기 test: {data.get('text', '')}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
