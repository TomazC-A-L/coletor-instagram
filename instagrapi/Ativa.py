from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, PrivateError, ClientError
import os
from urllib.request import urlretrieve
import time
from datetime import datetime

USERNAMES = ["canaldabelinha", "flavinhalouise", "gabrieleshirleyoficial",
             "ogatogalactico", "oisaacamendoim", "mcdivertida", "enaldinho",
             "luccasneto", "mariaclara_e_jp", "rafaeluizbroficial", "aingles._",
             "alice.e.juju", "cacauhaxkar", "stherediva", "heleninhadepapai",
             "jujuteofilo", "aperolareis", "ruanpereiraof", "valentinapontesofc",
             "vinibugoficial"]

PASTA_BASE = "F:\\instagrapi\\perfis_coletados"
ARQUIVO_PERFIS = "F:\\instagrapi\\dados_perfis.txt"

if not os.path.exists(PASTA_BASE):
    os.makedirs(PASTA_BASE)

# Inicializa o cliente do Instagrapi
cliente = Client()
cliente.delay_range = [2, 5]  # Aumente o delay para evitar bloqueios

# Função para resolver desafios
def resolver_desafio(cliente, username):
    try:
        cliente.challenge_resolve(cliente.last_json)
        print(f"Desafio resolvido para o usuário {username}.")
    except Exception as e:
        print(f"Erro ao resolver desafio: {e}")
        raise

USERNAME = "rjlinta"
PASSWORD = "G0sling!"

try:
    settings = cliente.load_settings("instagrapi\\rjlinsta.json")
    if not settings:
        cliente.login(USERNAME, PASSWORD)
    else:
        cliente.set_settings(settings)
        cliente.login(USERNAME, PASSWORD)
except ChallengeRequired as e:
    print("Desafio necessário. Tentando resolver...")
    resolver_desafio(cliente, USERNAME)
except Exception as e:
    print(f"Erro ao fazer login: {e}")
    exit()

# Salva as configurações de sessão
cliente.dump_settings("instagrapi\\rjlinsta.json")

# Função para salvar mídia
def salvar_midia(url, pasta, nome_arquivo):
    caminho_arquivo = os.path.join(pasta, nome_arquivo)
    try:
        urlretrieve(str(url), caminho_arquivo)
        print(f"Mídia salva: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar a mídia {nome_arquivo}: {e}")

# Função para salvar dados do perfil
def salvar_dados_perfil(nome_usuario, nome_completo, seguidores, seguindo, bio, data_coleta):
    with open(ARQUIVO_PERFIS, "a", encoding="utf-8") as arquivo:
        linha = f"{nome_usuario};{nome_completo};{seguidores};{seguindo};{bio};{data_coleta}\n"
        arquivo.write(linha)
    print(f"Dados do perfil salvos: {linha.strip()}")

# Itera sobre a lista de perfis
for username in USERNAMES:
    print(f"\nColetando mídias do perfil: @{username}")
    
    try:
        # Obtém informações do perfil usando a API privada
        perfil = cliente.user_info_by_username_v1(username)
        
        if perfil.is_private:
            print(f"O perfil @{username} é privado. Pulando...")
            continue
        
        # Cria a pasta do perfil
        pasta_perfil = os.path.join(PASTA_BASE, username)
        os.makedirs(pasta_perfil, exist_ok=True)
        
        # Salva os dados do perfil
        salvar_dados_perfil(
            username,
            perfil.full_name,
            perfil.follower_count,
            perfil.following_count,
            perfil.biography,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Coleta as mídias usando a API privada
        medias = cliente.user_medias_v1(perfil.pk, amount=0)  # amount=0 coleta todas
        
        for i, media in enumerate(medias, 1):
            try:
                # Trata diferentes tipos de mídia
                if media.media_type == 1:  # Imagem
                    url = media.thumbnail_url
                    extensao = ".jpg"
                elif media.media_type == 2:  # Vídeo
                    url = media.video_url
                    extensao = ".mp4"
                elif media.media_type == 8:  # Carrossel
                    for j, resource in enumerate(media.resources, 1):
                        if resource.media_type == 1:
                            url = resource.thumbnail_url
                            extensao = ".jpg"
                        elif resource.media_type == 2:
                            url = resource.video_url
                            extensao = ".mp4"
                        else:
                            continue
                        salvar_midia(url, pasta_perfil, f"post_{i}_parte_{j}{extensao}")
                    continue  # Pula para a próxima mídia após processar o carrossel
                else:
                    print(f"Tipo de mídia não suportado: {media.media_type}")
                    continue
                
                salvar_midia(url, pasta_perfil, f"post_{i}{extensao}")
                time.sleep(3)  # Delay maior entre cada mídia
                
            except Exception as e:
                print(f"Erro ao processar mídia {i}: {e}")
                continue
                
    except ClientError as e:
        print(f"Erro na API: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    
    time.sleep(10)  # Delay maior entre perfis

print("\nColeta concluída com sucesso!")