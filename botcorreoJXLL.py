from telegram.ext import Application, CommandHandler
import smtplib
from email.mime.text import MIMEText
import shlex
import time
from datetime import datetime

# --- Configuración del bot ---
TELEGRAM_TOKEN = "8623388213:AAHtQQaedi1hDI9k_NKWyMiIEGyjFb5GkcA"   # Reemplaza con tu token de BotFather
OWNER_ID = 8031278422                # Reemplaza con tu ID de Telegram

# --- Variables globales para correo ---
EMAIL_USER = None
EMAIL_PASS = None

# --- Diccionario de keys generadas ---
keys_autorizadas = {}
usuarios_validados = {}  # {user_id: {"rol": rol, "fecha": fecha, "username": username, "nombre": nombre}}

# --- Comando /start ---
async def start(update, context):
    await update.message.reply_text("Bienvenido. Usa /auth <key> para autenticarte. Usa /cmd para ver comandos.")

# --- Comando para vincular correo ---
async def setmail(update, context):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ No tienes permisos para configurar el correo.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /setmail <correo> <contraseña_app>")
        return
    global EMAIL_USER, EMAIL_PASS
    EMAIL_USER = context.args[0]
    EMAIL_PASS = context.args[1]
    await update.message.reply_text(f"✅ Correo vinculado: {EMAIL_USER}")

# --- Comandos del owner para crear keys ---
async def key_pro(update, context):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para generar keys.")
        return
    if not context.args:
        await update.message.reply_text("Debes indicar la clave. Ejemplo: /keypro SUPERADMIN")
        return
    key = context.args[0]
    keys_autorizadas[key] = "pro"
    await update.message.reply_text(f"Key PRO creada: {key}")

async def key_user(update, context):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para generar keys.")
        return
    if not context.args:
        await update.message.reply_text("Debes indicar la clave. Ejemplo: /keyuser EMPLEADO1")
        return
    key = context.args[0]
    keys_autorizadas[key] = "user"
    await update.message.reply_text(f"Key USER creada: {key}")

# --- Autenticación de usuarios ---
async def auth(update, context):
    if not context.args:
        await update.message.reply_text("Debes ingresar una key. Ejemplo: /auth SUPERADMIN")
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
        await update.message.reply_text(f"Autenticado con rol: {keys_autorizadas[key]}")
    else:
        await update.message.reply_text("Key inválida. Acceso denegado.")

def check_auth(user_id):
    return user_id in usuarios_validados

# --- Enviar correos con animación ---
async def enviar(update, context):
    if not check_auth(update.message.from_user.id):
        await update.message.reply_text("No estás autorizado. Usa /auth <key> primero.")
        return
    if EMAIL_USER is None or EMAIL_PASS is None:
        await update.message.reply_text("⚠️ No hay correo vinculado. Usa /setmail primero.")
        return
    
    try:
        args = shlex.split(update.message.text)
    except ValueError as e:
        await update.message.reply_text(f"Error procesando argumentos: {e}")
        return
    
    if len(args) < 4:
        await update.message.reply_text("Uso: /enviar <asunto> \"<mensaje completo>\" <correo1> <correo2> ...")
        return
    
    asunto = args[1]
    mensaje = args[2]
    destinatarios = args[3:]
    
    anim_msg = await update.message.reply_text("⏳ Cargando.")
    for dots in ["⏳ Cargando.", "⏳ Cargando..", "⏳ Cargando..."]:
        time.sleep(1)
        await context.bot.edit_message_text(chat_id=update.message.chat_id,
                                            message_id=anim_msg.message_id,
                                            text=dots)
    
    enviados = 0
    for correo in destinatarios:
        try:
            msg = MIMEText(mensaje)
            msg["Subject"] = asunto
            msg["From"] = EMAIL_USER
            msg["To"] = correo

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, correo, msg.as_string())
            
            enviados += 1
            await update.message.reply_text(f"✅ Mensaje enviado a {correo}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error enviando a {correo}: {e}")
    
    await update.message.reply_text(f"🎉 Todos los mensajes han sido enviados ({enviados} en total).\n\nHECHO BY @KEYBREAKER")

# --- Gestión de usuarios ---
async def list_users(update, context):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para ver usuarios.")
        return
    if not usuarios_validados:
        await update.message.reply_text("No hay usuarios activos.")
        return
    mensaje = "Usuarios activos:\n"
    for uid, data in usuarios_validados.items():
        mensaje += f"- ID: {uid}, Nombre: {data['nombre']}, Username: @{data['username']}, Rol: {data['rol']}, Fecha: {data['fecha']}\n"
    await update.message.reply_text(mensaje)

async def revoke(update, context):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para revocar keys.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /revoke <key>")
        return
    key = context.args[0]
    if key in keys_autorizadas:
        del keys_autorizadas[key]
        usuarios_validados_copy = usuarios_validados.copy()
        for uid, data in usuarios_validados_copy.items():
            if data["rol"] == key:
                del usuarios_validados[uid]
        await update.message.reply_text(f"Key {key} revocada y permisos eliminados.")
    else:
        await update.message.reply_text("Esa key no existe.")

# --- Comando /cmd ---
async def cmd(update, context):
    user_id = update.message.from_user.id
    if user_id == OWNER_ID:
        comandos = "Comandos OWNER: /keypro /keyuser /listusers /revoke /auth /setmail /enviar"
    elif user_id in usuarios_validados:
        comandos = "Comandos Usuario: /auth /enviar"
    else:
        comandos = "Comandos No autenticado: /auth"
    await update.message.reply_text(comandos)

# --- Main ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setmail", setmail))
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(CommandHandler("keypro", key_pro))
    app.add_handler(CommandHandler("keyuser", key_user))
    app.add_handler(CommandHandler("enviar", enviar))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("cmd", cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
