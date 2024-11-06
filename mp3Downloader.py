import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import yt_dlp
from pytube import Playlist
import os
import threading
import queue

# Cola para comunicar el progreso
progress_queue = queue.Queue()

# Evento para cancelar la descarga
cancel_event = threading.Event()

def progress_hook(d, index, total_videos):
    """Función de hook para obtener el progreso de la descarga."""
    if d['status'] == 'finished':
        print(f"Descarga completada: {d['filename']}")
        progress_queue.put((index + 1, total_videos))  # Indicar que se ha completado la descarga
    elif d['status'] == 'downloading':
        if 'downloaded_bytes' in d and 'total_bytes' in d:
            downloaded = d['downloaded_bytes']
            total = d['total_bytes']
            print(f"Descargando: {downloaded}/{total} bytes")

def descargar_video(url, output_path, index, total_videos):
    """Descarga un video de YouTube en formato MP3."""
    if cancel_event.is_set():
        return  # Exit if cancellation is requested

    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [lambda d: progress_hook(d, index, total_videos)],  # Añadir el hook de progreso
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            print(f"Error al descargar {url}: {e}")

def descargar_playlist(url, output_path):
    """Descarga todos los videos de una playlist de YouTube en formato MP3."""
    try:
        playlist = Playlist(url)
        total_videos = len(playlist.video_urls)
        for index, video_url in enumerate(playlist.video_urls):
            if cancel_event.is_set():
                print("Descarga cancelada")
                break  # Exit loop if cancellation is requested
            descargar_video(video_url, output_path, index, total_videos)
    except Exception as e:
        print(f"Error al descargar la playlist {url}: {e}")

def update_progress():
    """Actualiza la barra de progreso."""
    while not cancel_event.is_set():
        try:
            index, total = progress_queue.get(timeout=1)  # Esperar actualizaciones de progreso
            if total > 0:
                progress = (index / total) * 100
                progress_bar['value'] = progress
                label_progress.config(text=f"{index} de {total}")

        except queue.Empty:
            continue  # No hay actualizaciones, continuar

def iniciar_descarga():
    url = entry_url.get()
    output_path = entry_path.get()

    # Resetear el evento de cancelación
    cancel_event.clear()

    # Iniciar la descarga en un hilo separado
    if "playlist" in url:
        download_thread = threading.Thread(target=descargar_playlist, args=(url, output_path))
    else:
        download_thread = threading.Thread(target=descargar_video, args=(url, output_path, 0, 1))

    download_thread.start()

    # Iniciar el hilo para actualizar el progreso
    progress_thread = threading.Thread(target=update_progress, daemon=True)
    progress_thread.start()

def cancelar_descarga():
    """Cancela todas las descargas en curso."""
    cancel_event.set()  # Activar el evento de cancelación
    progress_queue.queue.clear()  # Limpiar la cola de progreso
    progress_bar['value'] = 0  # Resetear barra de progreso
    label_progress.config(text="Descarga cancelada")  # Actualizar el texto de estado

# Crear la ventana principal
root = tk.Tk()
root.title("Descargador de YouTube")
root.geometry("600x400")  # Tamaño de la ventana

# Crear widgets de la interfaz
label_url = tk.Label(root, text="URL del video o playlist:")
label_url.pack(pady=10)
entry_url = tk.Entry(root, width=50)
entry_url.pack(pady=10)

label_path = tk.Label(root, text="Ruta de salida:")
label_path.pack(pady=10)
entry_path = tk.Entry(root, width=50)
entry_path.pack(pady=10)

# Botón para seleccionar la ruta de salida
def seleccionar_ruta():
    ruta = filedialog.askdirectory()
    if ruta:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, ruta)

button_select_path = tk.Button(root, text="Seleccionar carpeta", command=seleccionar_ruta)
button_select_path.pack(pady=10)

# Botón para iniciar la descarga
button_download = tk.Button(root, text="Iniciar descarga", command=iniciar_descarga)
button_download.pack(pady=10)

# Botón para cancelar la descarga
button_cancel = tk.Button(root, text="Cancelar descarga", command=cancelar_descarga)
button_cancel.pack(pady=10)

# Barra de progreso
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=20)

# Etiqueta para mostrar el progreso
label_progress = tk.Label(root, text="Progreso: 0 de 0")
label_progress.pack(pady=10)

# Iniciar el bucle principal de la interfaz
root.mainloop()