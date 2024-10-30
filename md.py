import asyncio
import os
import pickle
import customtkinter as ctk
from tkinter import ttk, Toplevel, messagebox
from PIL import Image, ImageTk
import ctypes  
from telethon import TelegramClient, functions, types, errors
from logica import load_sessions
from main import create_generic_popup

async def send_message_from_session(api_id, api_hash, phone, username, message, num_messages):
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    await client.connect()
    if await client.is_user_authorized():
        try:
            for _ in range(num_messages):
                await client.send_message(username, message)
                print(f"Mensaje enviado a {username} desde {phone}")
        except Exception as e:
            print(f"Error al enviar mensaje desde {phone}: {e}")
    else:
        print(f"No autorizado para la sesión: {phone}")
    await client.disconnect()


async def send_messages_popup(entries):
    username = entries["Username or ID"].get()
    message = entries["Message"].get()
    num_sessions = entries["Number of Sessions (All, One, or Number)"].get()
    num_messages = int(entries["Number of Messages per Session"].get())
    sessions = load_sessions()

    if not username or not message or not num_sessions or not num_messages:
        messagebox.showwarning("Advertencia", "Por favor complete todos los campos y asegúrese de tener sesiones disponibles.")
        return

    if num_sessions.lower() == 'all':
        selected_sessions = sessions
    elif num_sessions.lower() == 'one':
        selected_sessions = [sessions[0]] if sessions else []
    else:
        try:
            num_sessions = int(num_sessions)
            selected_sessions = sessions[:num_sessions]
        except ValueError:
            messagebox.showwarning("Advertencia", "Número de sesiones no válido.")
            return

    tasks = [send_message_from_session(api_id, api_hash, phone, username, message, num_messages) for api_id, api_hash, phone in selected_sessions]
    await asyncio.gather(*tasks)



def send_message_popup():
    create_generic_popup("Send Message", "400x300", ["Username or ID", "Message", "Number of Sessions (All, One, or Number)", "Number of Messages per Session"], "Send Message", lambda entries: asyncio.run(send_messages_popup(entries)))

