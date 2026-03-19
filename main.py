import os
import telebot
import requests
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot Cloud Filmes Inline Ativo!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8692317223:AAFE76kBVYKkt85qv1wyR_deawLBnShwT0Q'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
MEU_ID = '6032657635'

bot = telebot.TeleBot(TOKEN)

# --- FUNÇÃO INLINE (A JANELINHA POPUP) ---
@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    try:
        nome_busca = inline_query.query
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome_busca}&language=pt-BR"
        res = requests.get(url).json()
        resultados = res.get('results', [])[:15] # Mostra até 15 resultados na janela

        res_inline = []
        for i, item in enumerate(resultados):
            titulo = item.get('title') or item.get('name')
            data = item.get('release_date') or item.get('first_air_date') or "----"
            ano = data[:4]
            tipo = "🎬 Filme" if item.get('media_type') == 'movie' else "📺 Série"
            
            # Imagem que aparece na janelinha (Poster pequeno)
            thumb = f"https://image.tmdb.org/t/p/w92{item.get('poster_path')}" if item.get('poster_path') else None
            
            # Monta o card da janelinha
            r = types.InlineQueryResultArticle(
                id=str(i),
                title=f"{titulo} ({ano})",
                description=f"{tipo} - Clique para pedir",
                thumbnail_url=thumb,
                input_message_content=types.InputTextMessageContent(
                    message_text=(
                        f"✅ **NOVO PEDIDO: CLOUD FILMES**\n\n"
                        f"📌 **Título:** {titulo}\n"
                        f"📅 **Ano:** {ano}\n"
                        f"📂 **Tipo:** {tipo}\n\n"
                        f"🚀 *Solicitação enviada! Analisaremos em breve.*"
                    ),
                    parse_mode="Markdown"
                )
            )
            res_inline.append(r)
        
        bot.answer_inline_query(inline_query.id, res_inline, cache_time=1)
    except Exception as e:
        print(f"Erro Inline: {e}")

# --- NOTIFICAÇÃO NO SEU PRIVADO ---
@bot.message_handler(func=lambda m: "NOVO PEDIDO: CLOUD FILMES" in (m.text or ""))
def notificar_dono(message):
    user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    # Repassa o pedido completo para o seu privado com a ID do usuário
    bot.send_message(MEU_ID, 
        f"🍿 **PEDIDO RECEBIDO (INLINE)**\n\n"
        f"{message.text}\n\n"
        f"👤 **Solicitado por:** {user}\n"
        f"🆔 **ID:** `{message.from_user.id}`", 
        parse_mode="Markdown")
    
    # Opcional: Apaga a confirmação do grupo depois de 1 minuto
    time.sleep(60)
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except: pass

# Comando Start normal caso alguém abra o bot
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Para pedir, digite `@NomeDoSeuBot` seguido do filme em qualquer chat!")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
            
