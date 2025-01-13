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
model = genai.GenerativeModel("gemini-1.5-flash")

# 허용되는 이미지 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 업로드된 이미지를 저장할 폴더 생성
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def check_114_spam(keyword):
    try:
        url = 'https://www.114.co.kr/action/search/scam'
        
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://www.114.co.kr',
            'Pragma': 'no-cache',
            'Referer': 'https://www.114.co.kr/search?tab=scam',
            'Request-Type': 'action',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': 'Windows',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        data = {
            "spam_kwd_tp_cd": "P",
            "spam_keyword": keyword
        }
        
        print(f"Sending request to 114 API with data: {data}")
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Parsed JSON response: {result}")
            
            data = result.get('data', {})
            whowho = data.get('whowho', {})
            kisa = data.get('kisa', {})
            
            def safe_int(value, default=0):
                try:
                    return int(value) if value is not None else default
                except (ValueError, TypeError):
                    return default
            
            # whowho 데이터 파싱
            spam_count = safe_int(whowho.get('spam_count'))
            safe_count = safe_int(whowho.get('safe_count'))
            spam_type_cnt = safe_int(whowho.get('spam_type_cnt'))
            whowho_cnt = safe_int(whowho.get('whowho_cnt'))
            
            # kisa 데이터 파싱
            spam_count_voice = safe_int(kisa.get('spam_count_voice'))
            spam_count_sms = safe_int(kisa.get('spam_count_sms'))
            
            # 스팸 여부 판단
            is_spam = spam_count > 0 or spam_type_cnt > 0 or spam_count_voice > 0 or spam_count_sms > 0
            
            return {
                "is_spam": is_spam,
                "whowho_data": {
                    "spam_desc": whowho.get('spam_desc', ''),
                    "spam_count": spam_count,
                    "safe_count": safe_count,
                    "spam_type_cnt": spam_type_cnt,
                    "total_reports": whowho_cnt,
                    "last_reported": whowho.get('last_registed_date', '')
                },
                "kisa_data": {
                    "spam_count_voice": spam_count_voice,
                    "spam_count_sms": spam_count_sms,
                    "date_start": kisa.get('date_start', ''),
                    "date_end": kisa.get('date_end', '')
                },
                "has_thecheat": data.get('thecheat') is not None
            }
            
        else:
            print(f"Error response: {response.text}")
            return {
                "error": "API request failed",
                "status_code": response.status_code,
                "is_spam": False
            }
            
    except Exception as e:
        print(f"Error in check_114_spam: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "is_spam": False
        }
def check_url_safety(url):
    try:
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
            
            category_meanings = {
                0: "알 수 없음",
                1: "일반 웹사이트",
                2: "악성 웹사이트",
                3: "피싱 웹사이트",
                4: "스캠 웹사이트"
            }
            
            return {
                "is_safe": category == 1,
                "is_malicious": category in [2, 3, 4],
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

def check_police_fraud(key):
    try:
        url = 'https://www.police.go.kr/user/cyber/fraud.do'
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/javascript, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Origin': 'https://www.police.go.kr',
            'Referer': 'https://www.police.go.kr/www/security/cyber/cyber04.jsp',
            'Connection': 'keep-alive'
        }
        
        params = {
            'key': key,
            'ftype': 'P'
        }
        
        response = requests.post(url, headers=headers, params=params)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "is_fraud": result.get('result', {}).get('count', '0') != '0',
                "raw_response": result
            }
        else:
            return {
                "error": "경찰청 API 요청 실패",
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {
            "error": str(e)
        }

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
            
        if '114_keyword' in request.form:
            keyword = request.form['114_keyword']
            spam_check_result = check_114_spam(keyword)
            return render_template('index.html', spam_check_result=spam_check_result)
        
        # 전화번호/계좌번호 체크 로직
        if 'fraud_key' in request.form:
            fraud_key = request.form['fraud_key']
            fraud_check_result = check_police_fraud(fraud_key)
            return render_template('index.html', fraud_check_result=fraud_check_result)
            
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
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        with open(filepath, 'rb') as image_file:
            image_content = base64.b64encode(image_file.read()).decode('utf-8')
        
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
        
        if 'error' in result.get('responses', [{}])[0]:
            error_message = result['responses'][0]['error']['message']
            error = f'오류 발생: {error_message}'
            return render_template('index.html', error=error)
        
        text_annotations = result['responses'][0].get('textAnnotations', [])
        extracted_text = text_annotations[0]['description'] if text_annotations else '텍스트를 인식하지 못했습니다.'
        
        try:
            prompt = f"""이건 웹사이트의 스크린샷 화면이야. 바로가기가 많아서 헷갈릴 수 있겠지만, 이 화면 내의 url주소, 혹은 전화번호를 찾아내서 출력해줘야 해.

도메인, 혹은 전화번호만 출력해 줘.
{extracted_text}
"""
            response = model.generate_content(prompt)
            gemini_result_text = response.text
        except Exception as e:
            error = f'Gemini AI 오류: {e}'
            return render_template('index.html', error=error)
        
        uploaded_image = os.path.join('uploads', unique_filename)
        
        return render_template('index.html', extracted_text=extracted_text, gemini_result_text=gemini_result_text, uploaded_image=uploaded_image)
    else:
        return render_template('index.html')

# API 엔드포인트들
@app.route('/api/check-url', methods=['POST'])
def api_check_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL이 제공되지 않았습니다.'}), 400
        
    url = data['url']
    result = check_url_safety(url)
    return jsonify(result)

@app.route('/api/check-fraud', methods=['POST'])
def api_check_fraud():
    data = request.get_json()
    if not data or 'key' not in data:
        return jsonify({'error': '검사할 키가 제공되지 않았습니다.'}), 400
        
    key = data['key']
    result = check_police_fraud(key)
    return jsonify(result)

@app.route('/api/check-114', methods=['POST'])
def api_check_114():
    data = request.get_json()
    if not data or 'keyword' not in data:
        return jsonify({'error': '검색어가 제공되지 않았습니다.'}), 400
        
    keyword = data['keyword']
    result = check_114_spam(keyword)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)