from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, PrivateError, ClientError
import os
from urllib.request import urlretrieve
import time
from datetime import datetime

# Configurações
HASHTAGS = ["kids", "children", "family"]  # Lista de hashtags para pesquisar
NUM_POSTS = 30    # Número de imagens para coletar por hashtag
NUM_IMAGENS_PERFIL = 4  # Número de imagens para coletar por perfil
PASTA_POSTS = "posts"  # Pasta para salvar as imagens dos posts
PASTA_USUARIOS = "usuarios"  # Pasta para salvar as pastas dos usuários
ARQUIVO_DADOS = "dados_coleta.txt"  # Arquivo para salvar os dados da coleta
ARQUIVO_PERFIS = "dados_perfis.txt"  # Arquivo para salvar os dados dos perfis

# Cria as pastas de saída se não existirem
if not os.path.exists(PASTA_POSTS):
    os.makedirs(PASTA_POSTS)
if not os.path.exists(PASTA_USUARIOS):
    os.makedirs(PASTA_USUARIOS)

# Inicializa o cliente do Instagrapi
cliente = Client()
cliente.delay_range = [1, 3]  # Delay entre requisições

# Função para resolver desafios
def resolver_desafio(cliente, username):
    try:
        # Tenta resolver o desafio automaticamente
        cliente.challenge_resolve(cliente.last_json)
        print(f"Desafio resolvido para o usuário {username}.")
    except Exception as e:
        print(f"Erro ao resolver desafio: {e}")
        raise

# Faz login no Instagram (substitua com suas credenciais)
USERNAME = "app_teste_2023"
PASSWORD = "Lup22@fl4"

try:
    # Tenta carregar as configurações de sessão salvas
    cliente.load_settings("teste_luiz.json")
    cliente.login(USERNAME, PASSWORD)
except ChallengeRequired as e:
    print("Desafio necessário. Tentando resolver...")
    resolver_desafio(cliente, USERNAME)
except Exception as e:
    print(f"Erro ao fazer login: {e}")
    exit()

# Salva as configurações de sessão após o login bem-sucedido
cliente.dump_settings("teste_luiz.json")

# Função para salvar uma imagem
def salvar_imagem(url, pasta, nome_arquivo):
    caminho_arquivo = os.path.join(pasta, nome_arquivo)
    try:
        urlretrieve(str(url), caminho_arquivo)  # Convertendo o objeto Url para string
        print(f"Imagem salva: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar a imagem {nome_arquivo}: {e}")

# Função para formatar a legenda (substituir quebras de linha por espaços)
def formatar_legenda(legenda):
    return legenda.replace("\n", " ") if legenda else "Sem legenda"

def formatar_bio(bio):
    return bio.replace("\n", " ") if bio else "sem bio"

# Função para salvar os dados da coleta
def salvar_dados(nome_usuario, legenda, curtidas, data_download, origem, hashtag):
    with open(ARQUIVO_DADOS, "a", encoding="utf-8") as arquivo:
        linha = f"{nome_usuario};{legenda};{curtidas};{data_download};{origem};{hashtag}\n"
        arquivo.write(linha)
    print(f"Dados salvos: {linha.strip()}")

# Função para salvar os dados do perfil
def salvar_dados_perfil(nome_usuario, nome_completo, seguidores, seguindo, bio, data_coleta):
    with open(ARQUIVO_PERFIS, "a", encoding="utf-8") as arquivo:
        linha = f"{nome_usuario};{nome_completo};{seguidores};{seguindo};{bio};{data_coleta}\n"
        arquivo.write(linha)
    print(f"Dados do perfil salvos: {linha.strip()}")

# Itera sobre a lista de hashtags
for hashtag in HASHTAGS:
    print(f"Buscando posts com a hashtag #{hashtag}...")
    imagens_coletadas = 0
    max_id = None  # Variável para paginação

    while imagens_coletadas < NUM_POSTS:
        try:
            # Coleta um "pedaço" (chunk) de posts da hashtag
            posts, max_id = cliente.hashtag_medias_v1_chunk(hashtag, max_id=max_id, tab_key="top")
            if not posts:
                print(f"Nenhum post encontrado para a hashtag #{hashtag}. Parando a coleta.")
                break

            # Itera sobre os posts coletados
            for post in posts:
                # Verifica se o post tem uma imagem
                if post.media_type == 1:  # Tipo 1 = imagem
                    # Obtém o nome de usuário do perfil que fez o post
                    usuario = post.user.username

                    # Obtém a legenda do post (se houver) e formata (substitui quebras de linha por espaços)
                    legenda = formatar_legenda(post.caption_text)

                    # Obtém o número de curtidas do post
                    curtidas = post.like_count

                    # Obtém a data de download (data atual)
                    data_download = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Salva os dados no arquivo de texto (origem: hashtag)
                    salvar_dados(usuario, legenda, curtidas, data_download, origem="hashtag", hashtag=hashtag)

                    # Salva a imagem do post na pasta "posts"
                    nome_arquivo_post = f"post_{hashtag}_{imagens_coletadas + 1}.jpg"
                    salvar_imagem(post.thumbnail_url, PASTA_POSTS, nome_arquivo_post)

                    # Cria uma pasta para o usuário dentro da pasta "usuarios"
                    pasta_usuario = os.path.join(PASTA_USUARIOS, usuario)
                    if not os.path.exists(pasta_usuario):
                        os.makedirs(pasta_usuario)

                    # Verifica se o perfil é público
                    try:
                        info_usuario = cliente.user_info_by_username(usuario)
                        if info_usuario.is_private:
                            print(f"O perfil {usuario} é privado. Pulando...")
                            continue
                    except Exception as e:
                        print(f"Erro ao verificar o perfil {usuario}: {e}")
                        continue

                    # Coleta as informações do perfil
                    nome_completo = info_usuario.full_name
                    seguidores = info_usuario.follower_count
                    seguindo = info_usuario.following_count
                    bio = formatar_bio(info_usuario.biography)
                    data_coleta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Salva os dados do perfil no arquivo de texto
                    salvar_dados_perfil(usuario, nome_completo, seguidores, seguindo, bio, data_coleta)

                    # Coleta as últimas 4 imagens do perfil do usuário
                    print(f"Coletando imagens do perfil: {usuario}")
                    try:
                        posts_usuario = cliente.user_medias(post.user.pk, amount=NUM_IMAGENS_PERFIL)
                    except PrivateError:
                        print(f"Erro: O perfil {usuario} é privado ou não pode ser acessado.")
                        continue
                    except Exception as e:
                        print(f"Erro ao coletar posts do perfil {usuario}: {e}")
                        continue

                    # Salva as imagens do perfil na pasta do usuário
                    for j, post_usuario in enumerate(posts_usuario):
                        if post_usuario.media_type == 1:  # Tipo 1 = imagem
                            # Obtém a legenda do post do perfil (se houver) e formata
                            legenda_perfil = formatar_legenda(post_usuario.caption_text)

                            # Obtém o número de curtidas do post do perfil
                            curtidas_perfil = post_usuario.like_count

                            # Obtém a data de download (data atual)
                            data_download_perfil = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            # Salva os dados no arquivo de texto (origem: perfil)
                            salvar_dados(usuario, legenda_perfil, curtidas_perfil, data_download_perfil, origem="perfil", hashtag=hashtag)

                            # Salva a imagem do perfil na pasta do usuário
                            nome_arquivo_perfil = f"imagem_{j + 1}.jpg"
                            salvar_imagem(post_usuario.thumbnail_url, pasta_usuario, nome_arquivo_perfil)

                    # Incrementa o contador de imagens coletadas
                    imagens_coletadas += 1

                    # Verifica se já coletamos imagens suficientes
                    if imagens_coletadas >= NUM_POSTS:
                        break

        except Exception as e:
            print(f"Erro ao coletar posts da hashtag #{hashtag}: {e}")
            break

        # Adiciona um delay entre as requisições para evitar bloqueios
        time.sleep(5)

print("Coleta de imagens e dados concluída!")