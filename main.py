from flask import Flask, request, jsonify, Response
from google.cloud import vision
import openai
from PIL import Image
from io import BytesIO

import os
import time
import requests
import json
import secrets

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from Dockerized Flask!"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    image = data.get("image", '')
    text = data.get("text", '')

    
    # return jsonify({"result": f"AI 일기 test: {data.get('text', '')}"})
    return jsonify({"result": data, "KEY": os.getenv("OPENAI_API_KEY")})

@app.route("/stream", methods=["POST"])
def stream_by_character():
    # JSON 파일 로딩
    def load_json(path):
        with open(path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)

    def detect_objects(image_link):
        client = vision.ImageAnnotatorClient()
        
        response = requests.get(image_link)
        image = Image.open(BytesIO(response.content)).convert('RGB')

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        image = vision.Image(content=img_byte_arr)
        response = client.object_localization(image=image)
        objects = response.localized_object_annotations
        
        filtered_names = set()
        for obj in objects:
            if obj.score >= 0.65:
                filtered_names.add(obj.name)  # set으로 중복 제거

        return filtered_names
    
    try:
        data_list = request.get_json()
        all_keywords = []
        text_list = []

        KEY = os.getenv("OPENAI_API_KEY")
        # client = OpenAI(api_key=KEY)
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # JSON 파일로부터 시스템 프롬프트 및 예시 불러오기
        PROMPT = load_json(f'config/PROMPTS.json')
        DIARY_EXAMPLE = load_json(f'config/DIARY.json')

        messages = [{'role': 'system', 'content': PROMPT['system_prompt']}]
        # (Few-shot 예시 추가) 예시가 필요하면 추가
        for example in DIARY_EXAMPLE:
            user_example = "키워드: "
            keyword_list = []
            for keyword in example['keyword']:
                keyword_list += [f"[{','.join(keyword)}]"]
            user_example += ','.join(keyword_list)
            user_example += "\n"

            user_example += f"텍스트: [{','.join(example['text'])}]"
            
            messages.append({'role': 'user', 'content': user_example})
            messages.append({'role': 'assistant', 'content': example['content']})
        
        for data in data_list:
            image_link = data.get("image", '')
            text_list.append(data.get("text", ''))
            keywords = detect_objects(image_link)
            all_keywords.append(list(keywords))

        text_prompt = f"[{','.join(text_list)}]"
        keyword_prompt = ','.join(f"[{','.join(keyword)}]" for keyword in all_keywords)
        final_prompt = f"키워드: {keyword_prompt}\n"
        final_prompt += f"텍스트: {text_prompt}"

        messages.append({'role': 'user', 'content': final_prompt})

        text_response = openai.ChatCompletion.create(
            model='gpt-5',
            messages=messages,
            temperature=0.95,
            stream=False,
        )

        # messages.append({'role': 'user', 'content': final_prompt})
        # text_response = client.chat.completions.create(
        #     model='gpt-4o',
        #     messages=messages,
        #     temperature=0.95,
        #     stream=False,
        # )

        text = text_response.choices[0].message.content
        
        def generate():
            for ch in text:
                yield f"data: {ch}\n\n"
                time.sleep(0.2)  # 글자당 지연 시간

        return Response(generate(), mimetype="text/event-stream")
        # return Response(
        #         json.dumps({
        #             "KEY": os.getenv("OPENAI_API_KEY"),
        #             "text": final_prompt,
        #             "openai": f"{openai.__version__}",
        #         }, ensure_ascii=False),
        #         status=200,
        #         mimetype='application/json'
        #     )
    
    except Exception as e:
        payload = json.dumps({"message": str(e)})
        yield f"event: error\ndata: {payload}\n\n"
        return jsonify({"error": f"{str(e)}"}), 500

@app.route("/stream_test", methods=["POST"])
def stream():
    text = "AI 일기 생성 테스트입니다. 이 텍스트는 스트리밍 방식으로 전송됩니다."
    def generate():
        for ch in text:
            yield f"data: {ch}\n\n"
            time.sleep(0.2)  # 글자당 지연 시간

    return Response(generate(), mimetype="text/event-stream")
if __name__ == "__main__":
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    app.run(host="0.0.0.0", port=8080)