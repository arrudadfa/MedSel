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
# CONFIGURAÇÕES (HARDCODED)
# ================================

# OpenAI API Configuration
OPENAI_API_KEY = "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"
OPENAI_MODEL = "text-embedding-3-small"

#

# Supabase Configuration  
SUPABASE_URL = "https://pymrmkomehxiztwikssy.supabase.co"
SUPABASE_KEY = "sb_publishable_JIFl9hKhidXi2MueCHpwzw_mL87pE7W"

# Files Configuration
CHUNKS_FILE = "chunk.json"

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
