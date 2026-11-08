"""PDF를 한 번 임베딩해 프로젝트 내부 Chroma DB에 저장한다."""
import argparse
import hashlib
import json
from pathlib import Path

from settings import COLLECTION, DB_DIR, EMBEDDING_MODEL, make_embeddings

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error('PDF 파일을 찾을 수 없습니다.')
    # 기존 DB를 실수로 덮어쓰거나 중복 임베딩하지 않는다.
    if DB_DIR.exists() and any(DB_DIR.iterdir()):
        parser.error(f'DB가 이미 존재합니다: {DB_DIR}. 새 DB는 CHROMA_DIR을 변경하세요.')
    docs = PyPDFLoader(str(args.pdf)).load()
    for doc in docs:
        doc.metadata['source'] = args.pdf.name
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100,
    ).split_documents(docs)
    chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
    if not chunks:
        parser.error('추출된 텍스트가 없습니다. 스캔 PDF는 OCR 처리가 필요합니다.')
    embeddings = make_embeddings()
    DB_DIR.mkdir(parents=True, exist_ok=True)
    Chroma.from_documents(
        documents=chunks, embedding=embeddings,
        ids=[f'policy-chunk-{i}' for i in range(len(chunks))],
        collection_name=COLLECTION, persist_directory=str(DB_DIR),
    )
    manifest = {
        'embedding_model': EMBEDDING_MODEL, 'collection': COLLECTION,
        'chunks': len(chunks), 'source': args.pdf.name,
        'sha256': hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
    }
    (DB_DIR / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8',
    )
    print(f'저장 완료: {DB_DIR} ({len(chunks)}개 청크)')


if __name__ == '__main__':
    main()
