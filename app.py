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
# GenerativeModel 초기화
model = genai.GenerativeModel("gemini-1.5-flash")

# 허용되는 이미지 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 업로드된 이미지를 저장할 폴더 생성
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def check_url_safety(url):
    try:
        # NordVPN의 URL 체커 API 엔드포인트
        check_api_url = "https://link-checker.nordvpn.com/v1/public-url-checker/check-url"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Sec-Ch-Ua-Platform': 'Windows',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36'
        }
        
        data = {
            "url": url
        }
        
        response = requests.post(check_api_url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            category = result.get("category")
            
            # 카테고리 해석
            category_meanings = {
                0: "알 수 없음",
                1: "일반 웹사이트",
                2: "악성 웹사이트",
                3: "피싱 웹사이트",
                4: "스캠 웹사이트"
            }
            
            return {
                "is_safe": category == 1,  # 카테고리가 1(일반)인 경우만 안전
                "is_malicious": category in [2, 3, 4],  # 악성/피싱/스캠인 경우
                "category": category,
                "category_description": category_meanings.get(category, "알 수 없음"),
                "checked_url": result.get("url"),
                "raw_response": result
            }
        else:
            return {
                "error": "API request failed",
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {
            "error": str(e)
        }

# 허용된 파일인지 확인하는 함수
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 메인 페이지 라우트
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # URL 체크 로직
        if 'url' in request.form:
            url = request.form['url']
            url_check_result = check_url_safety(url)
            return render_template('index.html', url_check_result=url_check_result)
            
        # 이미지 처리 로직
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
            prompt = f"""다음 텍스트가 가짜일 확률을 0에서 100 사이의 퍼센트로 표시하고, 그 이유를 간결하게 설명해 주세요. 다음 형식을 따라주세요:

가짜일 확률: XX%
이유: ...

텍스트:
{extracted_text}
"""
            response = model.generate_content(prompt)
            gemini_result_text = response.text
        except Exception as e:
            error = f'Gemini AI 오류: {e}'
            return render_template('index.html', error=error)
        
        # 업로드된 이미지의 상대 경로
        uploaded_image = os.path.join('uploads', unique_filename)
        
        return render_template('index.html', extracted_text=extracted_text, gemini_result_text=gemini_result_text, uploaded_image=uploaded_image)
    else:
        return render_template('index.html')

# OCR만 수행하는 API 엔드포인트
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
    
    return jsonify({'extracted_text': extracted_text})

# URL 체크 API 엔드포인트
@app.route('/api/check-url', methods=['POST'])
def api_check_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL이 제공되지 않았습니다.'}), 400
        
    url = data['url']
    result = check_url_safety(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)