import os
import rpyc
from rpyc import Service
from pathlib import Path
from threading import Timer

class FileServer(Service):
    def __init__(self, upload_dir):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.interests = {}
        self.timers = {}

    def on_connect(self, conn):
        print("Cliente conectado.")

    def on_disconnect(self, conn):
        print("Cliente desconectado.")

    def exposed_list_files(self):
        """Lista os arquivos disponíveis no servidor."""
        return self._list_files()

    def exposed_upload_file(self, file_name, file_data):
        """Faz o upload de um arquivo e notifica clientes interessados."""
        self._save_file(file_name, file_data)
        print(f"Arquivo '{file_name}' enviado com sucesso.")
        self._notify_interested_clients(file_name)

    def exposed_download_file(self, file_name):
        """Faz o download de um arquivo do servidor."""
        return self._read_file(file_name)

    def exposed_register_interest(self, file_name, client_ref, duration):
        """Registra o interesse de um cliente por um arquivo específico."""
        if file_name not in self._list_files():
            self._add_interest(file_name, client_ref, duration)

    def exposed_cancel_interest(self, file_name):
        """Cancela o interesse por um arquivo."""
        del self.interests[file_name]
        print(f"Interesse cancelado para o arquivo '{file_name}'.")
        self._cancel_timer(file_name)

    def _list_files(self):
        """Retorna a lista de arquivos disponíveis no servidor."""
        files = {}
        for file_name in os.listdir(self.upload_dir):
            file_path = self.upload_dir / file_name
            if file_path.is_file():
                files[file_name] = file_path.stat().st_size
        return list(files.items())

    def _save_file(self, file_name, file_data):
        file_path = self.upload_dir / file_name
        with open(file_path, 'wb') as f:
            f.write(file_data)

    def _read_file(self, file_name):
        file_path = self.upload_dir / file_name
        with open(file_path, 'rb') as f:
            return f.read()

    def _add_interest(self, file_name, client_ref, duration):
        self.interests[file_name] = (client_ref, duration)
        print(f"Interesse registrado para o arquivo '{file_name}'.")
        self._set_timer(file_name, duration)

    def _set_timer(self, file_name, duration):
        if file_name in self.timers:
            self.timers[file_name].cancel()
        timer = Timer(duration, lambda: self.exposed_cancel_interest(file_name))
        self.timers[file_name] = timer
        timer.start()

    def _cancel_timer(self, file_name):
        if file_name in self.timers:
            self.timers[file_name].cancel()
            del self.timers[file_name]

    def _notify_interested_clients(self, file_name):
        if file_name in self.interests:
            client_ref, _ = self.interests[file_name]
            client_ref.notify_event(file_name)
            self.exposed_cancel_interest(file_name)

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(FileServer(upload_dir='uploads'), port=18861)
    print("Servidor iniciado.")
    server.start()
