from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import requests
import base64
import os
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
from flasgger import Swagger, swag_from

# .env 파일에서 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# Swagger 설정
swagger = Swagger(app)

# API 키 가져오기
GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# API 키 확인
if not GOOGLE_VISION_API_KEY:
    raise ValueError("환경 변수 'GOOGLE_VISION_API_KEY'가 설정되지 않았습니다.")
if not GEMINI_API_KEY:
    raise ValueError("환경 변수 'GEMINI_API_KEY'가 설정되지 않았습니다.")

# Google Cloud Vision API URL
VISION_API_URL = f'https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}'

# Google Generative AI 설정
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-1.5-flash"

# 허용되는 이미지 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 업로드된 이미지를 저장할 폴더 생성
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 허용된 파일인지 확인하는 함수
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 메인 페이지 라우트
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            error = '이미지를 업로드해주세요.'
            return render_template('index.html', error=error)
        
        file = request.files['image']
        if file.filename == '':
            error = '파일이 선택되지 않았습니다.'
            return render_template('index.html', error=error)
        
        if not allowed_file(file.filename):
            error = '허용되지 않는 파일 형식입니다.'
            return render_template('index.html', error=error)
        
        # 이미지 파일 저장
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # 이미지 파일을 Base64로 인코딩
        with open(filepath, 'rb') as image_file:
            image_content = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Vision API 요청
        payload = {
            "requests": [
                {
                    "image": {
                        "content": image_content
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION"
                        }
                    ],
                    "imageContext": {
                        "languageHints": ["ko"]
                    }
                }
            ]
        }
        response = requests.post(VISION_API_URL, json=payload)
        result = response.json()
        
        # 오류 처리
        if 'error' in result.get('responses', [{}])[0]:
            error_message = result['responses'][0]['error']['message']
            error = f'오류 발생: {error_message}'
            return render_template('index.html', error=error)
        
        # OCR 결과 추출
        text_annotations = result['responses'][0].get('textAnnotations', [])
        extracted_text = text_annotations[0]['description'] if text_annotations else '텍스트를 인식하지 못했습니다.'
        
        # Gemini AI로 텍스트 분석
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = f"다음 텍스트가 가짜인지 판단하고, 그 이유를 설명해 주세요:\n\n{extracted_text}"
            gemini_response = model.generate_content(prompt)
            gemini_result_text = gemini_response.text
        except Exception as e:
            error = f'Gemini AI 오류: {e}'
            return render_template('index.html', error=error)
        
        # 업로드된 이미지의 상대 경로
        uploaded_image = os.path.join('uploads', unique_filename)
        
        return render_template('index.html', extracted_text=extracted_text, gemini_result_text=gemini_result_text, uploaded_image=uploaded_image)
    else:
        return render_template('index.html')

# API 엔드포인트 (/api/ocr)
@app.route('/api/ocr', methods=['POST'])
@swag_from('swagger/api_ocr.yml')
def api_ocr():
    if 'image' not in request.files:
        return jsonify({'error': '이미지가 포함되지 않았습니다.'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400
    
    # 이미지 처리
    image_content = base64.b64encode(file.read()).decode('utf-8')
    
    # Vision API 요청
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ],
                "imageContext": {
                    "languageHints": ["ko"]
                }
            }
        ]
    }
    response = requests.post(VISION_API_URL, json=payload)
    result = response.json()
    
    # 오류 처리
    if 'error' in result.get('responses', [{}])[0]:
        error_message = result['responses'][0]['error']['message']
        return jsonify({'error': f'Vision API 오류: {error_message}'}), 500
    
    # OCR 결과 추출
    text_annotations = result['responses'][0].get('textAnnotations', [])
    extracted_text = text_annotations[0]['description'] if text_annotations else ''
    
    # Gemini AI로 텍스트 분석
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"다음 텍스트가 가짜인지 판단하고, 그 이유를 설명해 주세요:\n\n{extracted_text}"
        gemini_response = model.generate_content(prompt)
        gemini_result_text = gemini_response.text
    except Exception as e:
        return jsonify({'error': f'Gemini AI 오류: {e}'}), 500
    
    return jsonify({
        'extracted_text': extracted_text,
        'gemini_result_text': gemini_result_text
    })

if __name__ == '__main__':
    app.run(debug=True)