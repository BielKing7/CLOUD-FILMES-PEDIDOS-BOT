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

@bot.message_handler(commands=['pedido'])
def fazer_pedido(message):
    # Pega o que o usuário digitou após o comando
    entrada = message.text.replace('/pedido', '').strip()
    
    if entrada:
        # Busca multi (filmes e séries ao mesmo tempo)
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={entrada}&language=pt-BR"
        try:
            res = requests.get(url).json()
            if res.get('results'):
                item = res['results'][0]
                
                # Identifica se é Filme ou Série para pegar os dados corretos
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
                    return # Ignora resultados que não sejam filmes/séries

                sinopse = item.get('overview', 'Sem sinopse disponível.')
                
                # 1. Resposta educativa para o usuário no grupo (Focando no APP)
                texto_confirmacao = (
                    f"✅ **Pedido Recebido!**\n\n"
                    f"{tipo_str}: **{titulo} ({ano})**\n"
                    f"🚀 Nossa equipe foi notificada e em breve este conteúdo será adicionado ao **App CLOUD FILMES**!\n\n"
                    f"⚠️ *Esta mensagem será apagada em 30s para manter o tópico limpo.*"
                )
                msg_bot = bot.reply_to(message, texto_confirmacao, parse_mode="Markdown")
                
                # 2. Detalhes técnicos para o seu PRIVADO (Com Sinopse para facilitar sua vida)
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

                # 3. Limpeza automática após 30 segundos
                time.sleep(30)
                try:
                    bot.delete_message(message.chat.id, message.message_id) # Apaga o comando do usuário
                    bot.delete_message(message.chat.id, msg_bot.message_id) # Apaga a resposta do bot
                except:
                    pass
            else:
                msg_erro = bot.reply_to(message, "❌ Título não encontrado. Verifique se o nome e o ano estão corretos.")
                time.sleep(10)
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.delete_message(message.chat.id, msg_erro.message_id)
                except: pass
        except:
            pass
    else:
        # Se o usuário digitar apenas /pedido
        msg_help = bot.reply_to(message, "💡 **Como pedir:**\nDigite `/pedido` seguido do nome e ano.\nEx: `/pedido Homem-Aranha (2002)`", parse_mode="Markdown")
        time.sleep(15)
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, msg_help.message_id)
        except:
            pass

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
            
