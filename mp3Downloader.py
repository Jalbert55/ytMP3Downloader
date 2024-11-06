import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
import yt_dlp
from pytube import Playlist
import os
import threading
import queue
import subprocess
from PIL import Image, ImageTk

# Cola para comunicar el progreso
progress_queue = queue.Queue()

# Evento para cancelar la descarga
cancel_event = threading.Event()

def progress_hook(d, index, total_videos):
    """Función de hook para obtener el progreso de la descarga."""
    if cancel_event.is_set():
        raise Exception("Descarga cancelada")  # Lanzar una excepción para detener la descarga

    if d['status'] == 'finished':
        output_text.insert(tk.END, f"Descarga completada: {d['filename']}\n")
        output_text.see(tk.END)  # Desplaza el texto hacia el final
        progress_queue.put((index + 1, total_videos))  # Indicar que se ha completado la descarga
    elif d['status'] == 'downloading':
        if 'downloaded_bytes' in d and 'total_bytes' in d:
            downloaded = d['downloaded_bytes']
            total = d['total_bytes']
            output_text.insert(tk.END, f"Descargando: {downloaded}/{total} bytes\n")
            output_text.see(tk.END)  # Desplaza el texto hacia el final

def descargar_video(url, output_path, index, total_videos):
    """Descarga un video de YouTube en formato MP3."""
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
            if str(e) == "Descarga cancelada":
                output_text.insert(tk.END, "Descarga cancelada por el usuario.\n")
            else:
                output_text.insert(tk.END, f"Error al descargar {url}: {e}\n")
            output_text.see(tk.END)  # Desplaza el texto hacia el final

def descargar_playlist(url, output_path):
    """Descarga todos los videos de una playlist de YouTube en formato MP3."""
    try:
        playlist = Playlist(url)
        total_videos = len(playlist.video_urls)
        for index, video_url in enumerate(playlist.video_urls):
            if cancel_event.is_set():
                output_text.insert(tk.END, "Descarga cancelada\n")
                output_text.see(tk.END)  # Desplaza el texto hacia el final
                break  # Exit loop if cancellation is requested
            descargar_video(video_url, output_path, index, total_videos)
    except Exception as e:
        output_text.insert(tk.END, f"Error al descargar la playlist {url}: {e}\n")
        output_text.see(tk.END)  # Desplaza el texto hacia el final

def iniciar_descarga():
    url = entry_url.get()
    output_path = entry_path.get()

    # Resetear el evento de cancelación
    cancel_event.clear()
    output_text.delete(1.0, tk.END)  # Limpiar la salida de texto
    output_text.insert(tk.END, "INICIANDO DESCARGA\n")

    # Iniciar la descarga en un hilo separado
    if "playlist" or "list" in url:
        download_thread = threading.Thread(target=descargar_playlist, args=(url, output_path))
    else:
        download_thread = threading.Thread(target=descargar_video, args=(url, output_path, 0, 1))

    download_thread.start()

def cancelar_descarga():
    """Cancela todas las descargas en curso."""
    cancel_event.set()  # Activar el evento de cancelación
    output_text.insert(tk.END, "Descarga cancelada por el usuario.\n")
    output_text.see(tk.END)  # Desplaza el texto hacia el final

def abrir_carpeta():
    """Abre la carpeta de descargas en el explorador de archivos."""
    output_path = entry_path.get()
    if os.path.isdir(output_path):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(output_path)
            elif os.name == 'posix':  # macOS o Linux
                subprocess.Popen(['open', output_path] if sys.platform == 'darwin' else ['xdg-open', output_path])
        except Exception as e:
            output_text.insert(tk.END, f"Error al abrir la carpeta: {e}\n")
            output_text.see(tk.END)
    else:
        output_text.insert(tk.END, "La ruta de salida no es válida.\n")
        output_text.see(tk.END)

# Función para habilitar/deshabilitar el botón de descarga
def verificar_campos():
    if entry_url.get().strip() and entry_path.get().strip():
        button_download.config(state=tk.NORMAL)
    else:
        button_download.config(state=tk.DISABLED)

# Crear la ventana principal
root = tk.Tk()
root.title("Descargador de YouTube")

# Centrar la ventana en la pantalla
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 700
window_height = 400
x = (screen_width/2) - (window_width/2)
y = (screen_height/2) - (window_height/2)
root.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")


# Hacer que la ventana se ajuste al contenido
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Configurar el fondo y color de fuente
root.configure(bg="#000000")  # Fondo rojo
label_color = "white"  # Color de fuente de los labels

# Crear widgets de la interfaz
label_url = tk.Label(root, text="URL del video o playlist:", bg="#000000", fg=label_color, font=('Times 20'))
label_url.grid(row=0, column=0, padx=10, pady=10, sticky='w')
entry_url = tk.Entry(root, width=50)
entry_url.grid(row=0, column=1, columnspan=2, padx=10, pady=10)
entry_url.bind("<KeyRelease>", lambda event: verificar_campos())  # Llama a verificar_campos cuando se escribe en URL

label_path = tk.Label(root, text="Ruta de salida:", bg="#000000", fg=label_color, font=('Times 20'))
label_path.grid(row=1, column=0, padx=10, pady=10, sticky='w')
entry_path = tk.Entry(root, width=35)
entry_path.grid(row=1, column=1, padx=10, pady=10, sticky='w')
entry_path.bind("<KeyRelease>", lambda event: verificar_campos())  # Llama a verificar_campos cuando se escribe en Ruta

# Cargar el icono
icon = Image.open("icono.png")
photo = ImageTk.PhotoImage(icon)
root.iconphoto(False, photo)

# Botón para seleccionar la ruta de salida
def seleccionar_ruta():
    ruta = filedialog.askdirectory()
    if ruta:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, ruta)
    verificar_campos()  # Verificar los campos después de seleccionar la ruta

# Función para cargar y redimensionar imágenes
def cargar_imagen(ruta, ancho, alto):
    imagen = Image.open(ruta)  # Abrir la imagen
    imagen_redimensionada = imagen.resize((ancho, alto), resample=Image.LANCZOS)  # Redimensionar la imagen
    return ImageTk.PhotoImage(imagen_redimensionada)  # Convertir a PhotoImage

# Cargar imágenes y redimensionarlas a 50x50 píxeles
img_select_path = cargar_imagen("buscar.png", 50, 50)
img_open_folder = cargar_imagen("carpeta.png", 50, 50)
img_cancel = cargar_imagen("cancelar.png", 50, 50)
img_download = cargar_imagen("descargar.png", 50, 50)

# Botón para seleccionar la ruta de salida
button_select_path = tk.Button(root, image=img_select_path, command=seleccionar_ruta)
button_select_path.grid(row=1, column=2, padx=5, pady=10, sticky='w')

# Botón para abrir la carpeta de descargas
button_open_folder = tk.Button(root, image=img_open_folder, command=abrir_carpeta)
button_open_folder.grid(row=1, column=3, padx=5, pady=10, sticky='w')

# Botón para iniciar la descarga y cancelar la descarga en la misma línea
button_download = tk.Button(root, image=img_download, command=iniciar_descarga, state=tk.DISABLED)
button_download.grid(row=2, column=1, padx=10, pady=10, sticky='e')

button_cancel = tk.Button(root, image=img_cancel, command=cancelar_descarga)
button_cancel.grid(row=2, column=2, padx=10, pady=10, sticky='w')

# Recuadro de texto para mostrar la salida de la consola
output_text = scrolledtext.ScrolledText(root, width=70, height=10)
output_text.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

# Configurar el cierre de la ventana para cancelar la descarga
def on_closing():
    cancelar_descarga()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Iniciar el bucle principal de la interfaz
root.mainloop()