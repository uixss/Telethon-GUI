import asyncio
import os
import pickle
from telethon import TelegramClient, functions, types, errors
from telethon.errors import SessionPasswordNeededError

# Funciones de gestión de sesiones
async def create_session(api_id, api_hash, phone_number):
    client = TelegramClient(f'sessions/{phone_number}', api_id, api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            code = input("Enter the code you received: ")
            await client.sign_in(phone_number, code)
    except SessionPasswordNeededError:
        password = input("Enter your password: ")
        await client.sign_in(password=password)
    finally:
        await client.disconnect()
    save_session(api_id, api_hash, phone_number)

def save_session(api_id, api_hash, phone_number):
    with open('vars.txt', 'ab') as g:
        pickle.dump([api_id, api_hash, phone_number], g)

def load_sessions():
    sessions = []
    if os.path.exists('vars.txt'):
        with open('vars.txt', 'rb') as f:
            while True:
                try:
                    sessions.append(pickle.load(f))
                except EOFError:
                    break
    return sessions

def save_all_sessions(sessions):
    with open('vars.txt', 'wb') as f:
        for session in sessions:
            pickle.dump(session, f)

async def get_entity_data(api_id, api_hash, phone, entity_input):
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    await client.connect()
    if await client.is_user_authorized():
        try:
            entity = await client.get_entity(entity_input)
            if isinstance(entity, types.Channel) or isinstance(entity, types.Chat):
                full_chat = await client(functions.channels.GetFullChannelRequest(channel=entity))
                return {
                    "ban_status": "banned" if getattr(full_chat.full_chat, 'banned_rights', None) else "active",
                    "chat_id": entity.id,
                    "chat_name": full_chat.chats[0].title,
                    "members": full_chat.full_chat.participants_count
                }
            elif isinstance(entity, types.User):
                user_info = await client(functions.users.GetFullUserRequest(entity))
                user = user_info.users[0]
                return {
                    "name": f"{user.first_name} {user.last_name or ''}",
                    "user_id": user.id,
                    "username": f"@{user.username}" if user.username else "N/A"
                }
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": f"No autorizado para la sesión {phone}"}
    await client.disconnect()

