import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

ROOT = Path(__file__).resolve().parent
if os.name == 'nt':
    # Store Python/native SQLite can disagree on redirected system temp paths.
    temp_dir = ROOT / '.tmp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = str(temp_dir)
    os.environ['TMP'] = str(temp_dir)
    tempfile.tempdir = str(temp_dir)

load_dotenv(ROOT / '.env')
DB_DIR = Path(os.getenv('CHROMA_DIR', 'data/chroma_openai'))
if not DB_DIR.is_absolute():
    DB_DIR = ROOT / DB_DIR
COLLECTION = os.getenv('CHROMA_COLLECTION', 'company_policy_openai')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'gpt-5-nano')


def make_embeddings():
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('.env에 OPENAI_API_KEY를 설정하세요.')
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL, request_timeout=60, max_retries=0,
    )
