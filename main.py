import os
import telebot
import requests
from flask import Flask
from threading import Thread

# --- PARTE 1: SERVIDOR WEB PARA MANTER O BOT VIVO ---
app = Flask('')

@app.route('/')
def home():
    return "Bot CLOUD FILMES está online 24h!"

def run():
    # O Render exige que o bot escute em uma porta específica
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- PARTE 2: CONFIGURAÇÃO DO BOT DE PEDIDOS ---
# Substitua as informações abaixo entre as aspas:
TOKEN = '8692317223:AAFE76kBVYKkt85qv1wyR_deawLBnShwT0Q'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
MEU_ID = '6032657635' 

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def boas_vindas(message):
    bot.reply_to(message, "Olá! Sou o assistente de pedidos do CLOUD FILMES.\n\nPara pedir um filme ou série, use o comando:\n`/pedido Nome do Filme`", parse_mode="Markdown")

@bot.message_handler(commands=['pedido'])
def fazer_pedido(message):
    nome_filme = message.text.replace('/pedido', '').strip()
    
    if not nome_filme:
        bot.reply_to(message, "Por favor, digite o nome do filme. Exemplo: `/pedido Matrix`", parse_mode="Markdown")
        return

    # Busca no catálogo do TMDB
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome_filme}&language=pt-BR"
    
    try:
        res = requests.get(url).json()
        if res.get('results'):
            item = res['results'][0]
            titulo = item.get('title') or item.get('name')
            tipo = "Filme" if item.get('media_type') == 'movie' else "Série"
            ano = (item.get('release_date') or item.get('first_air_date') or "0000")[:4]

            # Resposta para o usuário no grupo
            bot.reply_to(message, f"✅ **Pedido Recebido!**\n\n🎬 **{tipo}:** {titulo}\n📅 **Ano:** {ano}\n\nO administrador já foi notificado e verificará a disponibilidade em breve.", parse_mode="Markdown")
            
            # Envio do pedido para o seu privado (Dono)
            bot.send_message(MEU_ID, f"🍿 **NOVO PEDIDO NO CLOUD FILMES**\n\n📌 **Tipo:** {tipo}\n🎬 **Título:** {titulo}\n📅 **Lançamento:** {ano}\n👤 **Solicitado por:** @{message.from_user.username or 'Sem Username'}\n🆔 **ID do User:** `{message.from_user.id}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Não encontrei esse título no TMDB. Verifique se o nome está correto.")
    except Exception as e:
        bot.reply_to(message, "⚠️ Ocorreu um erro ao processar seu pedido. Tente novamente mais tarde.")

# --- PARTE 3: INICIALIZAÇÃO ---
if __name__ == "__main__":
    keep_alive() # Inicia o servidor Flask em paralelo
    print("Bot iniciado com sucesso!")
    bot.infinity_polling() # Mantém o bot verificando mensagens
  
