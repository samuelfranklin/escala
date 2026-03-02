import os
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
        self.process = None
        self.start_script()

    def start_script(self):
        print(f"Iniciando {self.script_path}...")
        self.process = subprocess.Popen([sys.executable, self.script_path])

    def stop_script(self):
        if self.process:
            print(f"Encerrando {self.script_path}...")
            self.process.terminate()
            self.process.wait()
            self.process = None

    def on_any_event(self, event):
        if event.is_directory:
            return
        # Monitora apenas arquivos .py
        if event.src_path.endswith(".py"):
            print(
                f"Alteração detectada em {event.src_path}. Recarregando a aplicação..."
            )
            self.stop_script()
            self.start_script()


if __name__ == "__main__":
    # Define o diretório a ser monitorado (o diretório atual onde watcher.py está)
    path = "."
    # Define o script Python principal a ser executado e reiniciado
    script_to_run = "app.py"

    event_handler = MyEventHandler(script_to_run)
    observer = Observer()
    # Agenda o monitoramento para o caminho especificado, recursivamente
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)  # Mantém o observador ativo
    except KeyboardInterrupt:
        observer.stop()  # Para o observador ao pressionar Ctrl+C
    observer.join()  # Espera o encerramento da thread do observador
