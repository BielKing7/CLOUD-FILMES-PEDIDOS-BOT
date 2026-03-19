import os
import telebot
import requests
import time
import re
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot Cloud Filmes Online!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8692317223:AAFE76kBVYKkt85qv1wyR_deawLBnShwT0Q'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
MEU_ID = '6032657635'

bot = telebot.TeleBot(TOKEN)

# --- COMANDO START (ADICIONADO) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    texto_start = (
        "Olá! Bem-vindo ao Bot de Pedidos do CLOUD FILMES\n\n"
        "Para solicitar o um conteúdo para o ser adicionado no app CLOUD FILMES "
        "basta usar o comando /pedido nome do Filme ou Série\n\n"
        "Exemplo: ` /pedido Homem-Aranha (2002) ` ou ` /pedido Stranger Things `"
    )
    bot.reply_to(message, texto_start, parse_mode="Markdown")

# --- COMANDO PEDIDO ---
@bot.message_handler(commands=['pedido'])
def fazer_pedido(message):
    entrada = message.text.replace('/pedido', '').strip()
    
    # Identifica o usuário (Pega o nome real mesmo sendo o dono do grupo)
    usuario_id = message.from_user.id
    if message.from_user.username:
        user_ref = f"@{message.from_user.username}"
    else:
        user_ref = message.from_user.first_name

    if entrada:
        # Extrai o ano se houver (ex: 2025)
        ano_digitado = re.search(r'\d{4}', entrada)
        ano_alvo = ano_digitado.group() if ano_digitado else None
        
        # Limpa o nome para a busca (remove ano e parênteses)
        nome_busca = re.sub(r'\(.*?\d{4}.*?\)', '', entrada).strip()
        nome_busca = re.sub(r'\d{4}', '', nome_busca).strip()

        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome_busca}&language=pt-BR"
        
        try:
            res = requests.get(url).json()
            resultados = res.get('results', [])
            
            if resultados:
                item_escolhido = None
                
                # Busca de Precisão por Ano
                if ano_alvo:
                    for r in resultados:
                        data = r.get('release_date') or r.get('first_air_date') or ""
                        if data.startswith(ano_alvo):
                            item_escolhido = r
                            break
                
                if not item_escolhido:
                    item_escolhido = resultados[0]

                titulo = item_escolhido.get('title') or item_escolhido.get('name')
                data_lanc = item_escolhido.get('release_date') or item_escolhido.get('first_air_date') or "----"
                ano = data_lanc[:4]
                tipo = "🎬 Filme" if item_escolhido.get('media_type') == 'movie' else "📺 Série"
                sinopse = item_escolhido.get('overview', 'Sinopse não disponível.')
                
                # Imagem Backdrop
                img_path = item_escolhido.get('backdrop_path') or item_escolhido.get('poster_path')
                img_url = f"https://image.tmdb.org/t/p/w780{img_path}" if img_path else None

                # 1. Resposta no Grupo
                texto_confirmacao = (
                    f"✅ **Pedido Recebido!**\n\n"
                    f"{tipo}: **{titulo} ({ano})**\n\n"
                    f"🚀 Nossa equipe foi notificada e em breve este conteúdo será adicionado ao **App CLOUD FILMES**!\n\n"
                    f"⚠️ *Limpando chat em 30s...*"
                )
                msg_bot = bot.reply_to(message, texto_confirmacao, parse_mode="Markdown")
                
                # 2. Detalhes para o seu PRIVADO (Com espaços e imagem)
                texto_privado = (
                    f"🍿 **SOLICITAÇÃO PARA O APP**\n\n"
                    f"📂 **Tipo:** {tipo}\n\n"
                    f"📌 **Título:** {titulo}\n\n"
                    f"📅 **Ano:** {ano}\n\n"
                    f"📝 **Sinopse:** {sinopse}\n\n"
                    f"👤 **User:** {user_ref}\n\n"
                    f"🆔 **ID:** `{usuario_id}`"
                )
                
                if img_url:
                    bot.send_photo(MEU_ID, img_url, caption=texto_privado, parse_mode="Markdown")
                else:
                    bot.send_message(MEU_ID, texto_privado, parse_mode="Markdown")

                # 3. Limpeza Automática
                time.sleep(30)
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.delete_message(message.chat.id, msg_bot.message_id)
                except: pass
            else:
                msg_erro = bot.reply_to(message, "🔍 **Título não localizado.**\n\nCertifique-se de que o nome está correto ou tente buscar sem o ano.")
                time.sleep(15)
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.delete_message(message.chat.id, msg_erro.message_id)
                except: pass
        except: pass
    else:
        # Comando de ajuda sem o link azul clicável
        msg_help = bot.reply_to(message, "💡 **Como pedir:**\nUse ` /pedido ` seguido do nome.\nExemplo: ` /pedido Batman (2022) `", parse_mode="Markdown")
        time.sleep(15)
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, msg_help.message_id)
        except: pass

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
