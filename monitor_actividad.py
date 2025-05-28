import os
import time
import cv2
import sounddevice as sd
import scipy.io.wavfile as wav
from datetime import datetime
from PIL import ImageGrab
import pygetwindow as gw
import threading
import speech_recognition as sr
from win10toast import ToastNotifier

# Carpetas
BASE_FOLDER = r"C:\Users\51947\Documents\IMAGENES\29979"
CAPTURAS_FOLDER = os.path.join(BASE_FOLDER, "CapturasPantalla")
WEBCAM_FOLDER = os.path.join(BASE_FOLDER, "Webcam")
AUDIO_FOLDER = os.path.join(BASE_FOLDER, "Audio")
TEXT_FOLDER = os.path.join(BASE_FOLDER, "Texto")

os.makedirs(CAPTURAS_FOLDER, exist_ok=True)
os.makedirs(WEBCAM_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(TEXT_FOLDER, exist_ok=True)

CONVERSACION_FILE = os.path.join(TEXT_FOLDER, "conversacion.txt")

# Configuración
AUDIO_DURATION = 30  # segundos
estado = "reanudar"

notifier = ToastNotifier()

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Función para mostrar notificaciones
def mostrar_notificacion(titulo, mensaje):
    notifier.show_toast(titulo, mensaje, duration=5, threaded=True)

# Captura de pantalla
def capture_screenshot():
    img = ImageGrab.grab()
    img.save(os.path.join(CAPTURAS_FOLDER, f"screenshot_{timestamp()}.png"))

# Foto con webcam
def capture_webcam_photo():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(os.path.join(WEBCAM_FOLDER, f"webcam_{timestamp()}.jpg"), frame)
    cap.release()

# Grabar audio cada 30 segundos
def audio_loop():
    while True:
        if estado == "reanudar":
            fs = 44100
            audio = sd.rec(int(AUDIO_DURATION * fs), samplerate=fs, channels=2)
            sd.wait()
            wav.write(os.path.join(AUDIO_FOLDER, f"audio_{timestamp()}.wav"), fs, audio)
        else:
            time.sleep(1)

# Guardar texto transcrito en archivo
def guardar_transcripcion(texto):
    with open(CONVERSACION_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {texto}\n")

# Interpretar comandos de voz para controlar estado
def interpretar_comando(texto):
    global estado
    t = texto.lower()
    if "miguel pausar" in t:
        estado = "pausar"
        print("🛑 Miguel ha pausado todo.")
        guardar_transcripcion("[SISTEMA PAUSADO POR VOZ]")
        mostrar_notificacion("Miguel", "Sistema pausado")
        return True
    elif "miguel reanudar" in t:
        estado = "reanudar"
        print("▶️ Miguel ha reanudado.")
        guardar_transcripcion("[SISTEMA REANUDADO POR VOZ]")
        mostrar_notificacion("Miguel", "Sistema reanudado")
        return True
    elif "miguel salir" in t:
        estado = "salir"
        print("⏸️ Miguel ha detenido todas las actividades (modo salir).")
        guardar_transcripcion("[SISTEMA DETENIDO POR VOZ]")
        mostrar_notificacion("Miguel", "Sistema detenido. Di 'Miguel reanudar' para continuar.")
        return True
    return False

# Transcribir voz en tiempo real
def transcribir_voz():
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = r.listen(source, timeout=5)
                texto = r.recognize_google(audio, language="es-ES")
                print(f"🗣️ {texto}")
                if interpretar_comando(texto):
                    continue
                if estado == "reanudar":
                    guardar_transcripcion(texto)
            except sr.UnknownValueError:
                continue
            except sr.WaitTimeoutError:
                continue
            except sr.RequestError as e:
                print("❌ Error con el servicio de voz:", e)
            time.sleep(1)

# Verifica si la ventana activa es relevante para capturar
def ventana_relevante(nombre_ventana):
    nombre = nombre_ventana.lower()
    keywords = [
        "explorador", "file explorer", "google chrome", "firefox",
        "edge", "opera", "safari", "buscar", "search"
    ]
    return any(k in nombre for k in keywords)

# Monitorear ventanas activas y hacer capturas
def monitorear_ventanas():
    ultima_ventana = ""
    while True:
        if estado != "reanudar":
            time.sleep(1)
            continue
        try:
            ventana = gw.getActiveWindow()
            if ventana:
                titulo = ventana.title
                if titulo != ultima_ventana:
                    ultima_ventana = titulo
                    if ventana_relevante(titulo):
                        print(f"📸 Actividad detectada: {titulo}")
                        capture_screenshot()
                        capture_webcam_photo()
        except Exception as e:
            print("Error ventana:", e)
        time.sleep(2)

# Ejecución principal
if __name__ == "__main__":
    print("🔧 Iniciando sistema Miguel...")
    threading.Thread(target=monitorear_ventanas, daemon=True).start()
    threading.Thread(target=audio_loop, daemon=True).start()
    transcribir_voz()
