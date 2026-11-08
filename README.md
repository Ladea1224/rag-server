# 로컬 RAG API

Python 3.11 이상이 필요합니다. PDF 분할(500자/중복 100자), OpenAI 임베딩(`text-embedding-3-small`), OpenAI 채팅(`gpt-5-nano`), Chroma, MMR 검색(k=3, fetch_k=10)을 사용합니다.

## 1. 설치 (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`의 `OPENAI_API_KEY`에 OpenAI API 키를 입력합니다. `.env`에는 다음 설정을 사용합니다. 기존 `.env`는 자동으로 변경되지 않으므로 직접 수정하세요.

```dotenv
OPENAI_API_KEY=실제_OpenAI_API_키
CHROMA_DIR=data/chroma_openai
CHROMA_COLLECTION=company_policy_openai
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-5-nano
```

`requirements.txt`는 직접 사용하는 라이브러리 버전을 고정하고, `constraints.txt`는 현재 Windows/Python 3.11 환경에서 설치한 의존성 버전을 기록합니다. 두 파일을 함께 옮기세요. Linux에서만 필요한 의존성은 설치 시 별도로 선택되므로 모든 OS를 완전히 고정한 잠금 파일은 아닙니다. 설치 후 `python -m pip check`로 확인하세요.

채팅과 임베딩 모두 `langchain-openai`를 통해 OpenAI API를 사용합니다. 저비용 모델 조합으로 `gpt-5-nano`와 `text-embedding-3-small`을 기본값으로 사용하며, 채팅의 추론 수준은 `minimal`, 출력 제한은 추론 포함 2048토큰입니다. 다른 채팅 모델로 변경할 때는 해당 모델의 추론 옵션 지원 여부도 확인하세요. Windows에서는 프로젝트의 `.tmp`를 임시 폴더로 자동 사용합니다. 코드 변경 후 실행 중인 서버를 재시작하세요. 질문 임베딩은 60초, 답변 생성은 120초 제한이며 두 호출의 자동 재시도는 꺼져 있습니다. `/chat`은 두 호출을 순서대로 수행하므로 전체 요청의 제한 시간은 각 호출의 제한 시간보다 길게 잡아야 합니다.

2026-11-08 확인한 표준 API 단가는 채팅 입력 $0.05/출력 $0.40(100만 토큰당), 임베딩 $0.02(100만 토큰당)입니다. 실제 비용은 추론 토큰과 입력/출력량에 따라 달라집니다. `gpt-5-nano`는 2026-12-11 종료 예정이므로 이후에는 채팅 모델과 추론 설정을 변경해야 합니다. 채팅 모델만 바꾸면 재임베딩은 필요하지 않습니다. 가격/모델 수명은 OpenAI 공식 문서에서 확인하세요: https://developers.openai.com/api/docs/models/gpt-5-nano / https://developers.openai.com/api/docs/models/text-embedding-3-small / https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create

## 2. PDF 임베딩 (최초 한 번)

```powershell
.\.venv\Scripts\python.exe ingest.py "C:\Users\SJH\Downloads\fictional_company_policy.pdf"
```

OpenAI API 호출 비용이 발생할 수 있습니다. PDF는 데이터로만 처리합니다. 결과는 작업 디렉터리와 관계없이 이 프로젝트의 `data/chroma_openai`에 저장됩니다(`CHROMA_DIR`으로 변경 가능). 이미 DB가 있으면 중복 생성하지 않고 중단합니다. 새 PDF로 새 DB를 만들려면 `.env`의 `CHROMA_DIR`을 다른 경로로 지정합니다. 서버를 중지한 상태에서 생성하세요.

Gemini에서 전환할 때는 반드시 원본 PDF를 OpenAI로 다시 임베딩해야 합니다. 기존 Gemini DB의 벡터와 OpenAI 질문 벡터를 섞을 수 없습니다. `CHROMA_DIR`을 새 경로로 지정하면 기존 DB는 그대로 보존됩니다. `ingest.py`가 만들어 주는 `manifest.json`은 직접 수정하지 마세요.

## 3. 서버 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

브라우저에서 http://127.0.0.1:8000/docs 를 열고 `POST /chat`을 실행합니다.

```json
{"question": "재택근무는 일주일에 며칠까지 가능한가요?"}
```

응답에는 `answer`와 검색된 `sources`(문서명, 1부터 시작하는 페이지, 본문)가 포함됩니다. sources는 검색된 참고자료이며 답변 전체의 정확성을 보증하는 것은 아닙니다. `/health`는 서버 시작 및 DB 로드 상태를 확인하며 OpenAI 연결 확인은 `/chat`으로 수행합니다.

서버 재시작 시 문서를 다시 임베딩하지 않습니다. 질문 임베딩과 답변 생성에는 매 요청마다 OpenAI API가 사용됩니다. 원본 PDF는 실행 중 필요하지 않습니다. 준비된 DB를 옮길 때는 서버를 종료하고 `CHROMA_DIR`의 폴더 전체(manifest.json 포함)를 복사하고 동일한 의존성 및 임베딩 설정을 사용하세요. `data/`와 `.env`는 Git에서 제외되므로 별도로 전달해야 합니다.

## 4. EC2에서 실행 확인 (Ubuntu 24.04, 단일 프로세스)

다음은 EC2에 프로젝트를 복사한 뒤 실행할 절차입니다. 실제 EC2 배포 및 Linux에서의 설치 검증은 별도로 수행해야 합니다. Windows의 `.venv`, `.tmp`, `pip-*` 임시 파일은 복사하지 않습니다. 소스 코드, `requirements.txt`, `constraints.txt`, `.env.example`을 복사합니다.

Ubuntu 24.04에서 Python 및 가상환경 도구를 준비합니다.

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv
```

이후 프로젝트 폴더 안에서 실행합니다. Python 3.11 이상인지 먼저 확인하세요.

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
cp .env.example .env
```

EC2의 `.env`에 `OPENAI_API_KEY`와 위 OpenAI 모델 설정을 입력합니다. `CHROMA_DIR`은 EC2 안의 OpenAI DB 위치여야 합니다. 예를 들어 `data/chroma_openai`를 복사했다면 `.env`에도 `CHROMA_DIR=data/chroma_openai`로 지정하세요. DB 디렉터리는 서버를 실행하는 Linux 사용자에게 쓰기 권한이 있어야 합니다. Gemini로 생성한 이전 DB는 사용할 수 없습니다.

DB는 아래 두 방법 중 하나로 준비합니다.

- 이미 생성된 DB를 사용: 로컬 서버를 종료한 상태에서 현재 `CHROMA_DIR` 폴더 전체를 `manifest.json`과 함께 복사합니다. 복사 전후 모델/컬렉션 설정은 동일하게 유지합니다. OS가 달라지는 경우 로드 및 `/chat` 호출로 호환성을 확인하세요.
- EC2에서 새로 생성: 비어 있는 DB 경로를 `.env`에 지정하고, PDF를 복사한 뒤 `.venv/bin/python ingest.py "/실제/경로/fictional_company_policy.pdf"`를 실행합니다. OpenAI API 비용이 발생할 수 있습니다.

준비 후 서버를 실행합니다.

```bash
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

다른 SSH 세션에서 확인합니다.

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body --connect-timeout 5 --max-time 240 http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"재택근무는 일주일에 며칠까지 가능한가요?"}'
```

`/health`의 `status: ok`뿐 아니라 `/chat`의 `answer`, `sources`도 확인해야 OpenAI 호출까지 검증됩니다. EC2에서도 의존성 다운로드 및 설치에는 시간이 걸립니다. Windows 임시 경로 문제는 Windows 전용 설정으로 처리하고 Linux의 기본 임시 경로는 그대로 사용합니다.

서버 로그에 OpenAI 인증 오류(401), 요청 빈도 또는 사용량 한도 오류(429), 시간 초과가 표시되면 해당 API 오류를 확인하세요. 라이브러리 재설치나 EC2 이전으로 API 계정의 한도가 해제되지는 않습니다. 현재 API는 외부 호출 실패를 공통 HTTP 502로 반환하므로 구체적인 원인은 서버 로그에서 확인합니다. Spring/Nginx를 거치는 경우 두 서버의 응답 제한 시간도 따로 확인해야 합니다.

로컬 PC에서 EC2 서버를 시험하려면 SSH 터널을 사용할 수 있습니다. 아래 명령은 로컬 PC에서 키와 주소를 실제 값으로 바꿔 실행하세요.

```bash
ssh -i "ec2-key.pem" -L 18000:127.0.0.1:8000 ubuntu@EC2_PUBLIC_IP
```

연결을 유지한 채 `http://127.0.0.1:18000/docs`에 접속합니다. API 포트를 공개하지 않고 확인할 수 있습니다.

위 실행은 SSH 터미널에서 수행하는 시험 실행입니다. 상시 운영을 위한 자동 시작/재시작 서비스, 인증, HTTPS 및 백업 구성은 포함하지 않습니다. 현재 로컬 Chroma를 사용하는 단일 프로세스 구조이며, Chroma 공식 문서는 운영 환경에 서버 형태의 Chroma 사용을 권장합니다: https://docs.trychroma.com/reference/python

## 5. 기존 Gemini 서버에서 전환하는 순서

1. 실행 중인 FastAPI 서버를 종료합니다.
2. 수정된 `main.py`, `settings.py`, `requirements.txt`, `constraints.txt`를 EC2에도 반영합니다. `.env.example`은 참고용이고 실제 `.env`는 자동 갱신되지 않습니다.
3. 로컬과 EC2의 `.env`를 위 OpenAI 설정으로 직접 변경합니다. `OPENAI_API_KEY`를 실제 키로 넣고 새 경로 `CHROMA_DIR=data/chroma_openai`를 사용합니다. 키는 Git에 올리지 않습니다.
4. EC2에서 `.venv/bin/python -m pip install -r requirements.txt`를 실행하고 `.venv/bin/python -m pip check`로 확인합니다. 로컬은 `.venv\Scripts\python.exe -m pip install -r requirements.txt`를 사용합니다.
5. 서버가 종료된 상태에서 원본 PDF를 새로 임베딩합니다. 로컬에서 만든 OpenAI DB를 EC2로 복사하는 경우에는 EC2에서 다시 임베딩하지 않아도 됩니다. 로컬 서버를 종료하고 DB 폴더 전체를 복사하세요.
6. 서버를 재시작하고 `/health`, `/chat` 순서로 확인합니다. API의 경로와 질문/응답 JSON 형식은 그대로이므로 Spring/Nginx의 라우팅 변경은 필요하지 않습니다. 대기 시간은 별도로 점검하세요.

로컬 CMD의 PDF 임베딩 및 실행 명령:

```cmd
.venv\Scripts\python.exe ingest.py "C:\Users\SJH\Downloads\fictional_company_policy.pdf"
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

EC2의 PDF 임베딩 및 실행 명령(원본 PDF 경로는 실제 위치로 변경):

```bash
.venv/bin/python ingest.py "/실제/경로/fictional_company_policy.pdf"
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```
