import os
import telebot
import requests
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB (PARA MANTER VIVO NO RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "Servidor Cloud Filmes Online"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = 'SEU_TOKEN_AQUI'
TMDB_KEY = 'SUA_CHAVE_TMDB_AQUI'
MEU_ID = 'SEU_ID_AQUI'

bot = telebot.TeleBot(TOKEN)

# --- COMANDO START (ADICIONADO) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    texto_start = (
        "✨ **Bem-vindo ao CLOUD FILMES!**\n\n"
        "Para solicitar um conteúdo, basta digitar `@` seguido do nome do nosso bot "
        "e o nome do filme no campo de mensagem.\n\n"
        "Exemplo: `@nome_do_seu_bot Batman`"
    )
    bot.reply_to(message, texto_start, parse_mode="Markdown")

# --- MODO INLINE (A JANELINHA PROFISSIONAL) ---
@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    try:
        nome_busca = inline_query.query
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome_busca}&language=pt-BR"
        res = requests.get(url).json()
        resultados = res.get('results', [])[:15]

        res_inline = []
        for i, item in enumerate(resultados):
            titulo = item.get('title') or item.get('name')
            data = item.get('release_date') or item.get('first_air_date') or "----"
            ano = data[:4]
            tipo = "🎬 Filme" if item.get('media_type') == 'movie' else "📺 Série"
            
            thumb = f"https://image.tmdb.org/t/p/w92{item.get('poster_path')}" if item.get('poster_path') else None
            
            r = types.InlineQueryResultArticle(
                id=str(i),
                title=f"{titulo} ({ano})",
                description=f"{tipo} - Toque para solicitar",
                thumbnail_url=thumb,
                input_message_content=types.InputTextMessageContent(
                    # NOVA MENSAGEM QUE VOCÊ PEDIU PARA O GRUPO
                    message_text=f"🚀 **Solicitação recebida! Seu pedido vai ser adicionado em breve no aplicativo CLOUD FILMES.**\n\n_{titulo} ({ano})_",
                    parse_mode="Markdown"
                )
            )
            res_inline.append(r)
        
        bot.answer_inline_query(inline_query.id, res_inline, cache_time=1)
    except Exception as e:
        print(f"Erro Inline: {e}")

# --- PROCESSAMENTO DO PEDIDO E NOTIFICAÇÃO NO SEU PRIVADO ---
@bot.message_handler(func=lambda m: "Solicitação recebida!" in (m.text or ""))
def processar_pedido_profissional(message):
    try:
        # Extrai o título da mensagem curta
        conteudo = message.text.split('\n\n')[-1].strip('_')
        nome_limpo = conteudo.split(' (')[0]
        
        # Busca detalhes completos para o seu relatório (com Backdrop)
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome_limpo}&language=pt-BR"
        res_tmdb = requests.get(url).json().get('results', [])
        
        if res_tmdb:
            detalhes = res_tmdb[0]
            titulo = detalhes.get('title') or detalhes.get('name')
            data = detalhes.get('release_date') or detalhes.get('first_air_date') or "----"
            ano = data[:4]
            tipo = "🎬 Filme" if detalhes.get('media_type') == 'movie' else "📺 Série"
            sinopse = detalhes.get('overview', 'Sinopse não disponível.')
            
            # Backdrop (Imagem de fundo larga)
            img_path = detalhes.get('backdrop_path') or detalhes.get('poster_path')
            img_url = f"https://image.tmdb.org/t/p/w780{img_path}" if img_path else None

            # Identificação do Usuário
            user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            
            # --- RELATÓRIO PARA O SEU PRIVADO (ORGANIZADO) ---
            texto_admin = (
                f"🍿 **SISTEMA DE SOLICITAÇÃO - CLOUD FILMES**\n\n"
                f"📂 **Tipo:** {tipo}\n\n"
                f"📌 **Título:** {titulo}\n\n"
                f"📅 **Ano de Lançamento:** {ano}\n\n"
                f"📝 **Sinopse:** {sinopse}\n\n"
                f"👤 **Solicitante:** {user}\n\n"
                f"🆔 **ID do Usuário:** `{message.from_user.id}`"
            )

            # Envia para você com a imagem Backdrop
            if img_url:
                bot.send_photo(MEU_ID, img_url, caption=texto_admin, parse_mode="Markdown")
            else:
                bot.send_message(MEU_ID, texto_admin, parse_mode="Markdown")

        # --- FAXINA AUTOMÁTICA (30 SEGUNDOS NO GRUPO) ---
        time.sleep(30)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except: pass

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
            
