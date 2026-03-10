import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot de Pedidos Cloud Filmes Online!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8692317223:AAFE76kBVYKkt85qv1wyR_deawLBnShwT0Q'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
MEU_ID = '6032657635'

bot = telebot.TeleBot(TOKEN)

# --- COMANDO START ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    texto_start = (
        "Olá! Bem-vindo ao Bot de Pedidos do CLOUD FILMES\n\n"
        "Para solicitar o um conteúdo para o ser adicionado no app CLOUD FILMES "
        "basta usar o comando /pedido nome do Filme ou Série\n\n"
        "Exemplo: `/pedido Homem-Aranha (2002)` ou `/pedido Stranger Things`"
    )
    bot.reply_to(message, texto_start, parse_mode="Markdown")

# --- COMANDO PEDIDO ---
@bot.message_handler(commands=['pedido'])
def fazer_pedido(message):
    entrada = message.text.replace('/pedido', '').strip()
    
    if entrada:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={entrada}&language=pt-BR"
        try:
            res = requests.get(url).json()
            if res.get('results'):
                item = res['results'][0]
                
                tipo_media = item.get('media_type')
                if tipo_media == 'movie':
                    titulo = item.get('title')
                    ano = (item.get('release_date') or "----")[:4]
                    tipo_str = "🎬 Filme"
                elif tipo_media == 'tv':
                    titulo = item.get('name')
                    ano = (item.get('first_air_date') or "----")[:4]
                    tipo_str = "📺 Série"
                else:
                    return

                sinopse = item.get('overview', 'Sem sinopse disponível.')
                
                # 1. Resposta no grupo (Focando no APP)
                texto_confirmacao = (
                    f"✅ **Pedido Recebido!**\n\n"
                    f"{tipo_str}: **{titulo} ({ano})**\n"
                    f"🚀 Nossa equipe foi notificada e em breve este conteúdo será adicionado ao **App CLOUD FILMES**!\n\n"
                    f"⚠️ *Esta mensagem será apagada em 30s para manter o tópico limpo.*"
                )
                msg_bot = bot.reply_to(message, texto_confirmacao, parse_mode="Markdown")
                
                # 2. Detalhes para o seu PRIVADO
                texto_privado = (
                    f"🍿 **SOLICITAÇÃO PARA O APP**\n\n"
                    f"🗂️ **Tipo:** {tipo_str}\n"
                    f"📌 **Título:** {titulo}\n"
                    f"📅 **Ano:** {ano}\n"
                    f"📝 **Sinopse:** {sinopse}\n\n"
                    f"👤 **User:** @{message.from_user.username or 'Sem Username'}\n"
                    f"🆔 **ID:** `{message.from_user.id}`"
                )
                bot.send_message(MEU_ID, texto_privado, parse_mode="Markdown")

                # 3. Limpeza automática
                time.sleep(30)
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.delete_message(message.chat.id, msg_bot.message_id)
                except:
                    pass
            else:
                msg_erro = bot.reply_to(message, "❌ Título não encontrado. Tente nome + ano.")
                time.sleep(10)
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.delete_message(message.chat.id, msg_erro.message_id)
                except: pass
        except:
            pass
    else:
        msg_help = bot.reply_to(message, "💡 **Como pedir:**\nUse `/pedido` nome e ano.\nEx: `/pedido Batman (2022)`")
        time.sleep(15)
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, msg_help.message_id)
        except: pass

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
                
