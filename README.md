# 로컬 RAG API

Python 3.11 이상이 필요합니다. 기존 노트북의 PDF 분할(500자/중복 100자), Gemini 임베딩, Chroma, MMR 검색(k=3, fetch_k=10)을 사용합니다.

## 1. 설치 (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`의 `GOOGLE_API_KEY`에 사용 가능한 키를 입력합니다. 노트북에 직접 기록된 키 대신 재발급한 키 사용을 권장합니다.

`requirements.txt`는 직접 사용하는 라이브러리 버전을 고정하고, `constraints.txt`는 정상 동작을 확인한 Windows/Python 3.11 환경의 하위 의존성 버전을 기록합니다. 두 파일을 함께 옮기세요. Linux에서만 필요한 의존성은 설치 시 별도로 선택되므로 모든 OS를 완전히 고정한 잠금 파일은 아닙니다. 설치 후 `python -m pip check`로 확인하세요.

Gemini API 버전은 채팅과 임베딩 모두 기본 `v1beta`를 명시적으로 사용합니다. SDK의 기본 버전 변경에 영향을 받지 않으며, 필요할 때 `.env`의 `GOOGLE_GENAI_API_VERSION`으로 변경할 수 있습니다. Windows에서는 프로젝트의 `.tmp`를 임시 폴더로 자동 사용합니다. CMD의 `set TEMP`, `set TMP`, `set GOOGLE_GENAI_API_VERSION` 명령은 더 이상 필요하지 않습니다. 코드 변경 후 실행 중인 서버를 재시작하세요.

## 2. PDF 임베딩 (최초 한 번)

```powershell
.\.venv\Scripts\python.exe ingest.py "C:\Users\SJH\Downloads\fictional_company_policy.pdf"
```

Gemini API 호출 비용이 발생할 수 있습니다. PDF는 데이터로만 처리합니다. 결과는 작업 디렉터리와 관계없이 이 프로젝트의 `data/chroma`에 저장됩니다. 이미 DB가 있으면 중복 생성하지 않고 중단합니다. 새 PDF로 새 DB를 만들려면 `.env`의 `CHROMA_DIR`을 다른 경로로 지정합니다. 서버를 중지한 상태에서 생성하세요.

## 3. 서버 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

브라우저에서 http://127.0.0.1:8000/docs 를 열고 `POST /chat`을 실행합니다.

```json
{"question": "재택근무는 일주일에 며칠까지 가능한가요?"}
```

응답에는 `answer`와 검색된 `sources`(문서명, 1부터 시작하는 페이지, 본문)가 포함됩니다. sources는 검색된 참고자료이며 답변 전체의 정확성을 보증하는 것은 아닙니다. `/health`는 서버 시작 및 DB 로드 상태를 확인하며 Gemini 연결 확인은 `/chat`으로 수행합니다.

서버 재시작 시 문서를 다시 임베딩하지 않습니다. 질문 임베딩과 답변 생성에는 매 요청마다 Gemini API가 사용됩니다. 원본 PDF는 실행 중 필요하지 않습니다. 준비된 DB를 옮길 때는 서버를 종료하고 `data/chroma` 폴더 전체(manifest.json 포함)를 복사하고 동일한 의존성 및 임베딩 설정을 사용하세요.

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

EC2의 `.env`에 API 키를 입력합니다. `CHROMA_DIR`은 EC2 안의 DB 위치여야 합니다. 예를 들어 `data/chroma_ready`를 복사했다면 `.env`에도 `CHROMA_DIR=data/chroma_ready`로 지정하세요. DB 디렉터리는 서버를 실행하는 Linux 사용자에게 쓰기 권한이 있어야 합니다.

DB는 아래 두 방법 중 하나로 준비합니다.

- 이미 생성된 DB를 사용: 로컬 서버를 종료한 상태에서 현재 `CHROMA_DIR` 폴더 전체를 `manifest.json`과 함께 복사합니다. 복사 전후 모델/컬렉션 설정은 동일하게 유지합니다. OS가 달라지는 경우 로드 및 `/chat` 호출로 호환성을 확인하세요.
- EC2에서 새로 생성: 비어 있는 DB 경로를 `.env`에 지정하고, PDF를 복사한 뒤 `.venv/bin/python ingest.py "/실제/경로/fictional_company_policy.pdf"`를 실행합니다. Gemini API 비용이 발생할 수 있습니다.

준비 후 서버를 실행합니다.

```bash
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

다른 SSH 세션에서 확인합니다.

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"재택근무는 일주일에 며칠까지 가능한가요?"}'
```

`/health`의 `status: ok`뿐 아니라 `/chat`의 `answer`, `sources`도 확인해야 Gemini 호출까지 검증됩니다. EC2에서도 의존성 다운로드 및 설치에는 시간이 걸립니다. Windows 임시 경로 문제는 Windows 전용 설정으로 처리하고 Linux의 기본 임시 경로는 그대로 사용합니다.

서버 로그에 Gemini `429 RESOURCE_EXHAUSTED`와 quota 초과가 표시되면 Google API 사용량 한도 문제입니다. 라이브러리 재설치나 EC2로 이전해도 같은 프로젝트의 한도는 해제되지 않습니다. 로그에 표시된 재시도 시간 및 Google AI Studio의 사용량을 확인하세요. 현재 API는 외부 호출 실패를 공통 HTTP 502로 반환하므로 구체적인 원인은 서버 로그에서 확인합니다.

로컬 PC에서 EC2 서버를 시험하려면 SSH 터널을 사용할 수 있습니다. 아래 명령은 로컬 PC에서 키와 주소를 실제 값으로 바꿔 실행하세요.

```bash
ssh -i "ec2-key.pem" -L 18000:127.0.0.1:8000 ubuntu@EC2_PUBLIC_IP
```

연결을 유지한 채 `http://127.0.0.1:18000/docs`에 접속합니다. API 포트를 공개하지 않고 확인할 수 있습니다.

위 실행은 SSH 터미널에서 수행하는 시험 실행입니다. 상시 운영을 위한 자동 시작/재시작 서비스, 인증, HTTPS 및 백업 구성은 포함하지 않습니다. 현재 로컬 Chroma를 사용하는 단일 프로세스 구조이며, Chroma 공식 문서는 운영 환경에 서버 형태의 Chroma 사용을 권장합니다: https://docs.trychroma.com/reference/python
