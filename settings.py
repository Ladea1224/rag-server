import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

ROOT = Path(__file__).resolve().parent
if os.name == 'nt':
    # Store Python/native SQLite can disagree on redirected system temp paths.
    temp_dir = ROOT / '.tmp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = str(temp_dir)
    os.environ['TMP'] = str(temp_dir)
    tempfile.tempdir = str(temp_dir)

load_dotenv(ROOT / '.env')
GEMINI_API_VERSION = os.getenv('GOOGLE_GENAI_API_VERSION', 'v1beta')
DB_DIR = Path(os.getenv('CHROMA_DIR', 'data/chroma'))
if not DB_DIR.is_absolute():
    DB_DIR = ROOT / DB_DIR
COLLECTION = os.getenv('CHROMA_COLLECTION', 'company_policy_gemini')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/gemini-embedding-001')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'gemini-2.5-flash')


def make_embeddings():
    if not os.getenv('GOOGLE_API_KEY'):
        raise RuntimeError('.env에 GOOGLE_API_KEY를 설정하세요.')
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL, api_version=GEMINI_API_VERSION,
    )
