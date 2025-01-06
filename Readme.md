
# 이미지 OCR 및 Gemini AI 분석 웹 애플리케이션

이 웹 애플리케이션은 사용자가 이미지를 업로드하면, **Google Cloud Vision API**를 사용하여 이미지에서 텍스트를 추출하고, 추출된 텍스트를 **Google의 Gemini AI 모델**을 사용하여 분석합니다. 웹 인터페이스와 RESTful API를 모두 제공하여 웹 브라우저와 앱에서 모두 사용할 수 있습니다.

## 주요 기능

- **이미지에서 텍스트 추출**: Google Cloud Vision API를 사용하여 이미지에서 한글 텍스트를 인식합니다.
- **Gemini AI를 통한 텍스트 분석**: 추출된 텍스트를 Google Generative AI 모델인 Gemini를 통해 분석하여 가짜 여부를 판단하고 설명을 제공합니다.
- **이미지 미리보기**: 업로드한 이미지를 웹 페이지에서 미리 볼 수 있습니다.
- **RESTful API 제공**: 앱 등 다른 클라이언트에서 사용할 수 있도록 API 엔드포인트를 제공합니다.
- **Swagger를 통한 API 문서화**: Swagger UI를 통해 API에 대한 문서를 제공합니다.

## 기술 스택

- **프로그래밍 언어**: Python 3.9 이상
- **웹 프레임워크**: Flask
- **프론트엔드**: HTML, Tailwind CSS(CDN 사용)
- **API 통신**: requests 라이브러리
- **환경 변수 관리**: python-dotenv
- **API 문서화**: flasgger (Swagger)

## 사전 요구 사항

- **Python 3.9 이상**이 설치되어 있어야 합니다.
- **Google Cloud Vision API 키**가 필요합니다.
- **Google Generative AI (Gemini AI) API 키**가 필요합니다.

## 설치 및 실행 방법

### 1. 프로젝트 클론

먼저, 저장소를 클론하고 해당 디렉토리로 이동합니다.

```bash
git clone https://your-repository-url.git
cd your-repository-name
```

### 2. 가상환경 설정

Python의 `venv` 모듈을 사용하여 가상환경을 생성하고 활성화합니다.

#### 가상환경 생성

```bash
python -m venv venv
```

#### 가상환경 활성화

- **Windows**:

  ```bash
  venv\Scripts\activate
  ```

- **macOS/Linux**:

  ```bash
  source venv/bin/activate
  ```

### 3. 필요 라이브러리 설치

`requirements.txt` 파일을 사용하여 필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, API 키를 입력합니다.

**`.env` 파일 내용 예시**:

```env
GOOGLE_VISION_API_KEY=YOUR_GOOGLE_VISION_API_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

- `YOUR_GOOGLE_VISION_API_KEY`를 실제 Google Cloud Vision API 키로 대체합니다.
- `YOUR_GEMINI_API_KEY`를 실제 Google Generative AI (Gemini AI) API 키로 대체합니다.

**주의**: `.env` 파일은 민감한 정보를 포함하고 있으므로 절대로 버전 관리 시스템에 포함되지 않도록 `.gitignore`에 추가해야 합니다.

### 5. 애플리케이션 실행

아래 명령어를 사용하여 애플리케이션을 실행합니다.

```bash
python app.py
```

애플리케이션은 기본적으로 `http://localhost:5000`에서 실행됩니다.

### 6. 웹 애플리케이션 사용

웹 브라우저에서 `http://localhost:5000`으로 접속하여 애플리케이션을 사용합니다.

- 이미지를 업로드하면 이미지에서 텍스트를 추출하고, Gemini AI를 통해 분석한 결과를 보여줍니다.
- 업로드한 이미지의 미리보기와 OCR 결과, Gemini AI의 분석 결과를 확인할 수 있습니다.

### 7. Swagger UI를 통한 API 문서 확인

웹 브라우저에서 `http://localhost:5000/apidocs`로 접속하면 **Swagger UI**를 통해 API 문서를 확인하고 테스트할 수 있습니다.

- RESTful API 엔드포인트를 통한 OCR 및 Gemini AI 분석 기능을 제공합니다.
- Swagger UI에서 직접 API를 호출해 볼 수 있습니다.

## 활용할 수 있는 API

### 1. Google Cloud Vision API

- **역할**: 업로드된 이미지에서 텍스트를 추출하는 데 사용됩니다.
- **기능**: OCR(Optical Character Recognition)을 통해 이미지에서 한글을 포함한 다양한 언어의 텍스트를 인식합니다.
- **공식 문서**: [Google Cloud Vision API 문서](https://cloud.google.com/vision/docs/ocr)

### 2. Google Generative AI (Gemini AI)

- **역할**: 추출된 텍스트를 분석하여 가짜 여부를 판단하고 설명을 제공합니다.
- **기능**: 대규모 언어 모델(LLM)을 활용하여 텍스트 생성 및 이해를 수행합니다.
- **라이브러리**: `google-generativeai` 패키지를 사용
- **공식 문서**: [Google Generative AI 문서](https://developers.generativeai.google/)

## 프로젝트 구성

```
your_project/
├── app.py
├── requirements.txt
├── .env
├── templates/
│   └── index.html
├── static/
│   └── uploads/
├── swagger/
    └── api_ocr.yml
```

- `app.py`: Flask 애플리케이션 메인 파일
- `requirements.txt`: 프로젝트의 Python 패키지 의존성 목록
- `.env`: 환경 변수 파일 (API 키 저장)
- `templates/index.html`: 웹 페이지 템플릿
- `static/uploads/`: 업로드된 이미지를 저장하는 폴더
- `swagger/api_ocr.yml`: Swagger를 통한 API 문서화 파일

## 주요 파일 설명

### app.py

- Flask 애플리케이션의 엔트리 포인트이며, 다음의 기능을 포함합니다:
  - 이미지 업로드 및 저장
  - **Google Cloud Vision API**를 사용한 이미지 OCR
  - **Google Generative AI**를 사용한 텍스트 분석
  - 웹 인터페이스 제공
  - RESTful API 엔드포인트 제공 (`/api/ocr`)
  - Swagger를 통한 API 문서화 설정

### requirements.txt

- 프로젝트에서 필요한 Python 패키지의 목록이 포함되어 있습니다.
- `pip install -r requirements.txt` 명령어를 통해 일괄 설치할 수 있습니다.

### .env

- 환경 변수 파일로, API 키와 같은 민감한 정보를 저장합니다.
- **주의**: `.env` 파일은 절대로 버전 관리 시스템에 포함하지 않도록 `.gitignore`에 추가해야 합니다.

### templates/index.html

- 웹 페이지의 템플릿 파일로, 사용자 인터페이스를 정의합니다.
- **Tailwind CSS (CDN)**를 사용하여 스타일링되었습니다.
- 업로드한 이미지의 미리보기, OCR 결과, Gemini AI 분석 결과를 표시합니다.

### swagger/api_ocr.yml

- Swagger를 사용하여 RESTful API의 문서를 작성한 파일입니다.
- `/api/ocr` 엔드포인트의 매개변수, 응답 형식 등을 정의하고 있습니다.

## 주의 사항

- **API 키 보안**: `app.py`나 다른 코드에 API 키를 하드코딩하지 않도록 주의하고, `.env` 파일을 사용하여 관리합니다.
- **.env 파일 관리**: `.env` 파일은 절대로 버전 관리 시스템에 포함되지 않도록 **`.gitignore`**에 추가해야 합니다.
- **Python 버전 요구 사항**: `google-generativeai` 패키지는 **Python 3.9 이상**을 필요로 합니다.
- **사용량 제한 및 비용**: Google Cloud Vision API와 Google Generative AI는 사용량에 따라 비용이 발생할 수 있으므로, 사용 전에 각 서비스의 요금제를 확인하시기 바랍니다.
- **이미지 저장소 관리**: 업로드된 이미지는 `static/uploads/` 폴더에 저장되며, 필요에 따라 적절한 시점에 삭제하는 로직을 추가해야 합니다.