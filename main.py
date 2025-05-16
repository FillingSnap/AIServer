from flask import Flask, request, jsonify, Response
import time
from PIL import Image
from io import BytesIO

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from Dockerized Flask!"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    # image = data.get("image", '')
    # text = data.get("text", '')

    # return jsonify({"result": f"AI 일기 test: {data.get('text', '')}"})
    return jsonify({"result": data})

@app.route("/stream")
def stream_by_character():
    text = "안녕하세요 오늘 생성된 일기입니다."

    def generate():
        for ch in text:
            yield ch
            time.sleep(0.2)  # 글자당 지연 시간

    return Response(generate(), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
