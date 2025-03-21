from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, LoginRequired, PrivateError, ClientError
import os
from urllib.request import urlretrieve
import time
from datetime import datetime
import re

# ============= CONFIGURAÇÕES =============
USERNAMES = ["canaldabelinha", "flavinhalouise", "gabrieleshirleyoficial",
             "ogatogalactico", "oisaacamendoim", "mcdivertida", "enaldinho",
             "luccasneto", "mariaclara_e_jp", "rafaeluizbroficial", "aingles._",
             "alice.e.juju", "cacauhaxkar", "stherediva", "heleninhadepapai", "jujuteofilo",
             "aperolareis", "ruanpereiraof", "valentinapontesofc", "vinibugoficial"]

PASTA_BASE = "F:\\instagrapi\\coleta2"
USERNAME = "rjlinsta"
PASSWORD = "G0sling!"

ARQUIVO_SETTINGS = "new.json"  # Arquivo para salvar a sessão

# ============= INICIALIZAÇÃO =============
cliente = Client()
cliente.delay_range = [3, 7]

# ============= FUNÇÕES DE LOGIN =============
def fazer_login():
    """Faz login e gerencia desafios de verificação"""
    try:
        # Tenta carregar sessão existente
        if os.path.exists(ARQUIVO_SETTINGS):
            settings = cliente.load_settings(ARQUIVO_SETTINGS)
            cliente.set_settings(settings)
            cliente.login(USERNAME, PASSWORD)
        else:
            cliente.login(USERNAME, PASSWORD)
            cliente.dump_settings(ARQUIVO_SETTINGS)
            
    except ChallengeRequired as e:
        print("Desafio de verificação necessário! Siga as instruções no app do Instagram.")
        cliente.challenge_resolve(e.challenge)
        cliente.dump_settings(ARQUIVO_SETTINGS)  # Salva a sessão após resolver o desafio
    except Exception as e:
        print(f"Erro fatal durante o login: {e}")
        exit()

def verificar_sessao():
    """Verifica se a sessão ainda está ativa"""
    try:
        cliente.get_timeline_feed()  # Requisição simples para testar a sessão
    except LoginRequired:
        print("Sessão expirada! Refazendo login...")
        fazer_login()

# ============= FUNÇÕES AUXILIARES =============
def formatar_texto(texto):
    """Remove quebras de linha e caracteres especiais"""
    if not texto: return ""
    return re.sub(r'\s+', ' ', texto.strip().replace('\n', ' '))

def criar_pasta_se_nao_existir(pasta):
    """Cria uma pasta se ela não existir"""
    if not os.path.exists(pasta):
        os.makedirs(pasta)

def salvar_midia(url, pasta, nome_arquivo):
    """Salva uma mídia (imagem/vídeo) na pasta especificada"""
    caminho = os.path.join(pasta, nome_arquivo)
    try:
        urlretrieve(str(url), caminho)
        return True
    except Exception as e:
        print(f"Erro ao salvar mídia: {e}")
        return False

def processar_comentarios(media_id, pasta):
    """Coleta e salva todos os comentários de uma mídia"""
    comentarios = []
    max_id = None
    
    try:
        while True:
            batch = cliente.media_comments(media_id, max_id=max_id)
            if not batch: break
            
            for comentario in batch:
                texto_formatado = formatar_texto(comentario.text)
                linha = (
                    f"{comentario.user.username};"
                    f"{texto_formatado};"
                    f"{comentario.created_at_utc.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                comentarios.append(linha)
            
            max_id = batch[-1].id if batch else None
            time.sleep(2)
            
    except ClientError as e:
        print(f"Erro ao coletar comentários: {e}")
    
    # Salva em arquivo
    if comentarios:
        caminho = os.path.join(pasta, f"comentarios_{media_id}.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(comentarios))

def salvar_metadados(media, data_coleta, caminho_arquivo):
    """Salva os metadados da mídia no arquivo do perfil"""
    legenda = formatar_texto(media.caption_text)
    
    linha = (
        f"{media.id};"
        f"{legenda};"
        f"{media.like_count};"
        f"{media.taken_at.strftime('%Y-%m-%d %H:%M:%S')};"
        f"{data_coleta}"
    )
    
    with open(caminho_arquivo, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

def salvar_info_perfil(perfil, caminho_arquivo):
    """Salva as informações do perfil em um arquivo"""
    info = (
        f"Nome: {perfil.full_name}\n"
        f"Seguidores: {perfil.follower_count}\n"
        f"Seguindo: {perfil.following_count}\n"
        f"Publicações: {perfil.media_count}\n"
        f"Bio: {formatar_texto(perfil.biography)}\n"
    )
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(info)

# ============= FLUXO PRINCIPAL =============
def main():
    # Login inicial
    fazer_login()
    
    for username in USERNAMES:
        print(f"\n=== Processando perfil: @{username} ===")
        
        try:
            # Verifica a sessão antes de cada perfil
            verificar_sessao()
            
            # Cria estrutura de pastas
            pasta_perfil = os.path.join(PASTA_BASE, username)
            criar_pasta_se_nao_existir(pasta_perfil)
            
            # Arquivo de metadados do perfil
            arquivo_metadados = os.path.join(pasta_perfil, "metadados.txt")
            
            # Coleta informações do perfil
            perfil = cliente.user_info_by_username_v1(username)
            if perfil.is_private:
                print(f"Perfil @{username} é privado. Pulando...")
                continue
            
            # Salva informações do perfil
            arquivo_info_perfil = os.path.join(pasta_perfil, "info_perfil.txt")
            salvar_info_perfil(perfil, arquivo_info_perfil)
            
            # Coleta todas as mídias
            medias = cliente.user_medias_v1(perfil.pk, amount=0)
            
            for media in medias:
                data_coleta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Processa diferentes tipos de mídia
                if media.media_type == 1:  # Imagem única
                    url = media.thumbnail_url
                    extensao = ".jpg"
                elif media.media_type == 2:  # Vídeo
                    url = media.video_url
                    extensao = ".mp4"
                elif media.media_type == 8:  # Carrossel
                    url = media.resources[0].thumbnail_url  # Pega a primeira mídia
                    extensao = ".jpg"
                else:
                    continue
                
                # Define nome do arquivo
                nome_arquivo = f"{media.id}{extensao}"
                
                # Baixa a mídia
                if salvar_midia(url, pasta_perfil, nome_arquivo):
                    # Salva metadados
                    salvar_metadados(media, data_coleta, arquivo_metadados)
                    
                    # Coleta comentários
                    processar_comentarios(media.id, pasta_perfil)
                    
                    print(f"Mídia {media.id} processada com sucesso!")
                
                time.sleep(5)  # Delay entre mídias
            
        except Exception as e:
            print(f"Erro no perfil @{username}: {e}")
            continue

if __name__ == "__main__":
    main()
    print("\nColeta concluída! Verifique a pasta:", PASTA_BASE)