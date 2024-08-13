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
        self.timer = {}

    def on_connect(self, conn):
        print("Cliente conectado.")

    def on_disconnect(self, conn):
        print("Cliente desconectado.")

    def exposed_list_files(self):
        files = {}
        for file_name in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, file_name)
            if os.path.isfile(file_path):
                files[file_name] = os.path.getsize(file_path)
        return list(files.items())  # Retorna uma lista de tuplas

    def exposed_upload_file(self, file_name, file_data):
        file_path = os.path.join(self.upload_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        print(f"Arquivo '{file_name}' enviado com sucesso.")
        self.notify_interested_clients(file_name)

    def exposed_download_file(self, file_name):
        file_path = os.path.join(self.upload_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                data = f.read()
                if isinstance(data, bytes):
                    return data
                else:
                    raise ValueError("Os dados lidos não são bytes.")
        else:
            raise FileNotFoundError(f"O arquivo '{file_name}' não foi encontrado.")

    def exposed_register_interest(self, file_name, client_ref, duration):
        self.interests[file_name] = (client_ref, duration)
        print(f"Interesse registrado para o arquivo '{file_name}'.")

        # Cancelar o interesse após o tempo especificado
        if file_name in self.timer:
            self.timer[file_name].cancel()
        
        def remove_interest():
            self.exposed_cancel_interest(file_name)

        t = Timer(duration, remove_interest)
        self.timer[file_name] = t
        t.start()

    def exposed_cancel_interest(self, file_name):
        if file_name in self.interests:
            del self.interests[file_name]
            print(f"Interesse cancelado para o arquivo '{file_name}'.")
            if file_name in self.timer:
                self.timer[file_name].cancel()
                del self.timer[file_name]

    def notify_interested_clients(self, file_name):
        for name, (client_ref, _) in self.interests.items():
            if name == file_name:
                try:
                    client_ref.notify_event(file_name)
                except Exception as e:
                    print(f"Erro ao notificar cliente sobre o arquivo '{file_name}': {e}")

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(FileServer(upload_dir='uploads'), port=18861)
    print("Servidor iniciado.")
    server.start()
