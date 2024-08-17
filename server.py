import os
import rpyc
from rpyc import Service
from pathlib import Path
from threading import Timer

class FileServer(Service):
    def __init__(self, upload_dir):
        self.upload_dir = Path(upload_dir)  # Define o diretório para armazenar os arquivos enviados
        self.upload_dir.mkdir(parents=True, exist_ok=True)  # Cria o diretório se ele não existir
        self.interests = {}  # Dicionário para manter o registro de interesses dos clientes
        self.timers = {}  # Dicionário para armazenar os timers para remover interesses

    def on_connect(self, conn):
        print("Cliente conectado.")  # Mensagem exibida quando um cliente se conecta

    def on_disconnect(self, conn):
        print("Cliente desconectado.")  # Mensagem exibida quando um cliente se desconecta

    def exposed_list_files(self):
        """Lista os arquivos disponíveis no servidor."""
        files = {}
        for file_name in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, file_name)
            if os.path.isfile(file_path):
                files[file_name] = os.path.getsize(file_path)  # Adiciona o arquivo e seu tamanho ao dicionário
        return list(files.items())  # Retorna a lista de arquivos e tamanhos

    def exposed_upload_file(self, file_name, file_data):
        """Faz o upload de um arquivo e notifica clientes interessados."""
        file_path = os.path.join(self.upload_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_data)  # Salva o arquivo no diretório especificado
        print(f"Arquivo '{file_name}' enviado com sucesso.")
        self.notify_interested_clients(file_name)  # Notifica clientes que têm interesse no arquivo

    def exposed_download_file(self, file_name):
        """Faz o download de um arquivo do servidor."""
        file_path = os.path.join(self.upload_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                data = f.read()  # Lê o conteúdo do arquivo
                return data
        else:
            raise FileNotFoundError(f"O arquivo '{file_name}' não foi encontrado.")  # Levanta exceção se o arquivo não existir

    def exposed_register_interest(self, file_name, client_ref, duration):
        """Registra o interesse de um cliente por um arquivo específico."""
        if file_name not in self.files_on_server():
            self.interests[file_name] = (client_ref, duration)  # Adiciona o interesse ao dicionário
            print(f"Interesse registrado para o arquivo '{file_name}'.")

            # Cancela o interesse após o tempo especificado
            if file_name in self.timers:
                self.timers[file_name].cancel()
            
            def remove_interest():
                self.exposed_cancel_interest(file_name)

            t = Timer(duration, remove_interest)  # Cria um timer para cancelar o interesse
            self.timers[file_name] = t
            t.start()
        else:
            client_ref.notify_event(file_name)  # Notifica imediatamente se o arquivo já estiver disponível

    def exposed_cancel_interest(self, file_name):
        """Cancela o interesse por um arquivo."""
        if file_name in self.interests:
            del self.interests[file_name]  # Remove o interesse do dicionário
            print(f"Interesse cancelado para o arquivo '{file_name}'.")
            if file_name in self.timers:
                self.timers[file_name].cancel()
                del self.timers[file_name]  # Remove o timer associado ao interesse

    def notify_interested_clients(self, file_name):
        """Notifica clientes interessados quando o arquivo se torna disponível."""
        if file_name in self.interests:
            client_ref, _ = self.interests[file_name]
            try:
                client_ref.notify_event(file_name)  # Notifica o cliente
            except Exception as e:
                print(f"Erro ao notificar cliente sobre o arquivo '{file_name}': {e}")
            finally:
                self.exposed_cancel_interest(file_name)  # Cancela o interesse após notificação

    def files_on_server(self):
        """Retorna a lista de arquivos disponíveis no servidor."""
        return os.listdir(self.upload_dir)

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(FileServer(upload_dir='uploads'), port=18861)  # Inicia o servidor na porta 18861
    print("Servidor iniciado.")
    server.start()
