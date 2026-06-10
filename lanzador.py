import subprocess
import time
import webview
import os

if __name__ == '__main__':
    carpeta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_app = os.path.join(carpeta_actual, 'app.py')
    ruta_python = os.path.join(carpeta_actual, 'venv', 'Scripts', 'python.exe')
    
    # Arrancamos Streamlit apuntando al Python de tu venv
    comando = [ruta_python, "-m", "streamlit", "run", ruta_app, "--server.headless", "true"]
    proceso_streamlit = subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Esperamos 4 segundos a que conecte a Supabase
    time.sleep(4)
    
    # Abrimos la ventana limpia de la app
    webview.create_window("Sistema de Gestión y Facturación", "http://localhost:8501", width=1280, height=800)
    webview.start()
    
    # Al cerrar la ventana, matamos el proceso de Streamlit
    proceso_streamlit.terminate()