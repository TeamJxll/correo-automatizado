from telegram.ext import Updater, CommandHandler
import smtplib
from email.mime.text import MIMEText
import shlex
import time
from datetime import datetime

# --- Configuración del bot de Telegram ---
TELEGRAM_TOKEN = "8623388213:AAHtQQaedi1hDI9k_NKWyMiIEGyjFb5GkcA"

# --- Diccionario de keys generadas ---
keys_autorizadas = {}

# --- Usuarios validados con su rol, fecha/hora y datos de perfil ---
usuarios_validados = {}  # {user_id: {"rol": rol, "fecha": fecha, "username": username, "nombre": nombre}}

# --- ID del owner (tu ID de Telegram) ---
OWNER_ID = 8031278422

def start(update, context):
    update.message.reply_text("Bienvenido. Usa /auth <key> para autenticarte. Usa /cmd para ver comandos.")

# --- Comandos del owner para crear keys ---
def key_pro(update, context):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("No tienes permisos para generar keys.")
        return
    if not context.args:
        update.message.reply_text("Debes indicar la clave. Ejemplo: /keypro SUPERADMIN")
        return
    key = context.args[0]
    keys_autorizadas[key] = "pro"
    update.message.reply_text(f"Key PRO creada: {key}")

def key_user(update, context):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("No tienes permisos para generar keys.")
        return
    if not context.args:
        update.message.reply_text("Debes indicar la clave. Ejemplo: /keyuser EMPLEADO1")
        return
    key = context.args[0]
    keys_autorizadas[key] = "user"
    update.message.reply_text(f"Key USER creada: {key}")

# --- Autenticación de usuarios ---
def auth(update, context):
    if not context.args:
        update.message.reply_text("Debes ingresar una key. Ejemplo: /auth SUPERADMIN")
        return
    key = context.args[0]
    if key in keys_autorizadas:
        user = update.message.from_user
        nombre_completo = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Sin nombre"
        usuarios_validados[user.id] = {
            "rol": keys_autorizadas[key],
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": user.username or "Sin username",
            "nombre": nombre_completo
        }
        update.message.reply_text(f"Autenticado con rol: {keys_autorizadas[key]}")
    else:
        update.message.reply_text("Key inválida. Acceso denegado.")

def check_auth(user_id):
    return user_id in usuarios_validados

# --- Enviar mensajes a cualquier correo con animación ---
def enviar(update, context):
    if not check_auth(update.message.from_user.id):
        update.message.reply_text("No estás autorizado. Usa /auth <key> primero.")
        return
    
    try:
        args = shlex.split(update.message.text)  # divide respetando comillas
    except ValueError as e:
        update.message.reply_text(f"Error procesando argumentos: {e}")
        return
    
    if len(args) < 4:
        update.message.reply_text("Uso: /enviar <asunto> \"<mensaje completo>\" <correo1> <correo2> ...")
        return
    
    asunto = args[1]
    mensaje = args[2]
    destinatarios = args[3:]
    
    # Animación de cargando en el mismo mensaje
    anim_msg = update.message.reply_text("⏳ Cargando.")
    for dots in ["⏳ Cargando.", "⏳ Cargando..", "⏳ Cargando..."]:
        time.sleep(1)
        context.bot.edit_message_text(chat_id=update.message.chat_id,
                                      message_id=anim_msg.message_id,
                                      text=dots)
    
    # Enviar correos
    enviados = 0
    for correo in destinatarios:
        try:
            msg = MIMEText(mensaje)
            msg["Subject"] = asunto
            msg["From"] = "TU_CORREO"
            msg["To"] = correo

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login("TU_CORREO", "TU_PASSWORD")
                server.sendmail("TU_CORREO", correo, msg.as_string())
            
            enviados += 1
            update.message.reply_text(f"✅ Mensaje enviado a {correo}")
        except Exception as e:
            update.message.reply_text(f"❌ Error enviando a {correo}: {e}")
    
    # Mensaje final con firma
    update.message.reply_text(f"🎉 Todos los mensajes han sido enviados ({enviados} en total).\n\nHECHO BY @KEYBREAKER")

# --- Comandos del owner para gestión de usuarios ---
def list_users(update, context):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("No tienes permisos para ver usuarios.")
        return
    
    if not usuarios_validados:
        update.message.reply_text("No hay usuarios activos.")
        return
    
    mensaje = "Usuarios activos:\n"
    for uid, data in usuarios_validados.items():
        mensaje += f"- ID: {uid}, Nombre: {data['nombre']}, Username: @{data['username']}, Rol: {data['rol']}, Fecha: {data['fecha']}\n"
    update.message.reply_text(mensaje)

def revoke(update, context):
    if update.message.from_user.id != OWNER_ID:
        update.message.reply_text("No tienes permisos para revocar keys.")
        return
    
    if not context.args:
        update.message.reply_text("Uso: /revoke <key>")
        return
    
    key = context.args[0]
    if key in keys_autorizadas:
        del keys_autorizadas[key]
        usuarios_validados_copy = usuarios_validados.copy()
        for uid, data in usuarios_validados_copy.items():
            if data["rol"] == key:
                del usuarios_validados[uid]
        update.message.reply_text(f"Key {key} revocada y permisos eliminados.")
    else:
        update.message.reply_text("Esa key no existe.")

# --- Comando /cmd con ejemplos ---
def cmd(update, context):
    user_id = update.message.from_user.id
    
    if user_id == OWNER_ID:
        comandos = """
Comandos disponibles (OWNER):

- /keypro <clave> 
  Crea una key PRO con todos los permisos.
  Ejemplo: /keypro SUPERADMIN

- /keyuser <clave> 
  Crea una key USER con permisos básicos.
  Ejemplo: /keyuser EMPLEADO1

- /listusers 
  Muestra la lista de usuarios activos con ID, nombre completo, username y fecha/hora de autenticación.
  Ejemplo: /listusers

- /revoke <key> 
  Revoca una key y elimina permisos.
  Ejemplo: /revoke EMPLEADO1

- /auth <key> 
  Autentica al usuario con una key.
  Ejemplo: /auth SUPERADMIN

- /enviar <asunto> "<mensaje completo>" <correo1> <correo2> ...
  Envía un mensaje a uno o varios correos.
  Ejemplo: /enviar Reporte "Revisar informe adjunto" correo1@dominio.com correo2@dominio.com
"""
    elif user_id in usuarios_validados:
        comandos = """
Comandos disponibles (Usuario autenticado):

- /auth <key> 
  Autentica al usuario con una key.
  Ejemplo: /auth EMPLEADO1

- /enviar <asunto> "<mensaje completo>" <correo1> <correo2> ...
  Envía un mensaje a uno o varios correos.
  Ejemplo: /enviar Aviso "La reunión es a las 3pm en la sala 2" jefe@empresa.com equipo@empresa.com
"""
    else:
        comandos = """
Comandos disponibles (No autenticado):

- /auth <key> 
  Autentica al usuario con una key.
  Ejemplo: /auth EMPLEADO1
"""
    
    update.message.reply_text(comandos)

# --- Configuración del bot ---
updater = Updater(TELEGRAM_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("auth", auth))
dp.add_handler(CommandHandler("keypro", key_pro))
dp.add_handler(CommandHandler("keyuser", key_user))
dp.add_handler(CommandHandler("enviar", enviar))
dp.add_handler(CommandHandler("listusers", list_users))
dp.add_handler(CommandHandler("revoke", revoke))
dp.add_handler(CommandHandler("cmd", cmd))

updater.start_polling()
updater.idle()
