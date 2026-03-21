#!/usr/bin/env python3
"""
Script para inserir chunks do chunk.json na tabela documents do Supabase
com embeddings da OpenAI (text-embedding-3-small)
"""

import json
import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from openai import OpenAI
import logging

# ================================
# CONFIGURAÇÕES (ENV)
# ================================

def load_dotenv(dotenv_path: str = ".env") -> None:
    """Carrega variáveis do arquivo .env para o ambiente."""
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")

# Supabase Configuration  
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Files Configuration
CHUNKS_FILE = os.getenv("CHUNKS_FILE", "chunk.json")

missing_env = [
    var_name
    for var_name, var_value in {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
    }.items()
    if not var_value
]

if missing_env:
    missing_list = ", ".join(missing_env)
    raise RuntimeError(
        f"Variáveis obrigatórias ausentes no ambiente/.env: {missing_list}"
    )

# ================================
# SETUP
# ================================

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_chunks() -> List[Dict]:
    """Carrega os chunks do arquivo JSON"""
    try:
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Fix escaped characters in JSON
            content = content.replace('\\_', '_').replace('\\[', '[').replace('\\]', ']')
            return json.loads(content)
    except FileNotFoundError:
        logger.error(f"Arquivo {CHUNKS_FILE} não encontrado")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        return []

def generate_embedding(text: str) -> List[float]:
    """Gera embedding usando OpenAI text-embedding-3-small"""
    try:
        response = openai_client.embeddings.create(
            model=OPENAI_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Erro ao gerar embedding: {e}")
        raise

def check_existing_documents() -> int:
    """Verifica quantos documentos já existem na tabela"""
    try:
        result = supabase.table('documents').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Erro ao verificar documentos existentes: {e}")
        return 0

def clear_all_documents() -> bool:
    """Remove todos os documentos da tabela"""
    try:
        result = supabase.table('documents').delete().neq('id', 0).execute()
        logger.info(f"Removidos todos os documentos da tabela")
        return True
    except Exception as e:
        logger.error(f"Erro ao limpar tabela: {e}")
        return False

def insert_document(chunk: Dict) -> bool:
    """Insere um chunk como documento na tabela Supabase"""
    try:
        # Prepara o conteúdo para embedding
        content = chunk.get('content', '')
        
        # Gera embedding
        logger.info(f"Gerando embedding para chunk {chunk.get('chunk_id', 'unknown')}")
        embedding = generate_embedding(content)
        
        # Prepara metadata
        metadata = {
            'chunk_id': chunk.get('chunk_id'),
            'section_path': chunk.get('section_path'),
            'token_count': chunk.get('token_count'),
            'content_type': chunk.get('content_type'),
            'priority_level': chunk.get('priority_level'),
            'keywords': chunk.get('keywords'),
            'is_actionable': chunk.get('is_actionable')
        }
        
        # Insere no Supabase
        result = supabase.table('documents').insert({
            'content': content,
            'metadata': metadata,
            'embedding': embedding
        }).execute()
        
        logger.info(f"Inserido chunk {chunk.get('chunk_id')} com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inserir chunk {chunk.get('chunk_id', 'unknown')}: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Script de Upload de Documentos para Supabase")
    print("=" * 50)
    
    # Carrega chunks
    chunks = load_chunks()
    if not chunks:
        print("❌ Nenhum chunk encontrado. Verifique o arquivo chunk.json")
        return
    
    print(f"📄 Encontrados {len(chunks)} chunks para processar")
    
    # Verifica documentos existentes
    existing_count = check_existing_documents()
    print(f"📊 Documentos existentes na tabela: {existing_count}")
    
    # Pergunta sobre limpeza se há documentos existentes
    if existing_count > 0:
        print("\n🤔 A tabela já contém documentos.")
        choice = input("Deseja (L)impar tudo ou (A)crescentar aos existentes? [L/A]: ").upper()
        
        if choice == 'L':
            print("🗑️  Limpando tabela...")
            if not clear_all_documents():
                print("❌ Erro ao limpar tabela. Abortando.")
                return
            print("✅ Tabela limpa com sucesso")
        elif choice == 'A':
            print("➕ Acrescentando aos documentos existentes")
        else:
            print("❌ Opção inválida. Abortando.")
            return
    
    # Processa chunks
    print(f"\n🔄 Processando {len(chunks)} chunks...")
    success_count = 0
    
    for i, chunk in enumerate(chunks, 1):
        print(f"📝 Processando chunk {i}/{len(chunks)}: {chunk.get('chunk_id', 'unknown')}")
        
        if insert_document(chunk):
            success_count += 1
        else:
            print(f"❌ Falha no chunk {chunk.get('chunk_id', 'unknown')}")
    
    # Resultado final
    print("\n" + "=" * 50)
    print(f"✅ Processamento concluído!")
    print(f"📊 Sucessos: {success_count}/{len(chunks)}")
    print(f"❌ Falhas: {len(chunks) - success_count}")
    
    if success_count == len(chunks):
        print("🎉 Todos os chunks foram inseridos com sucesso!")
    elif success_count > 0:
        print("⚠️  Alguns chunks falharam. Verifique os logs acima.")
    else:
        print("💥 Nenhum chunk foi inserido. Verifique as configurações.")

if __name__ == "__main__":
    main()
