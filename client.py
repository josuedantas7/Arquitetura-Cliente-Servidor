import rpyc
from tkinter import Tk, Label, Button, Listbox, END, Entry, messagebox, filedialog, Frame, Scrollbar, RIGHT, Y, BOTH, X, LEFT, TOP
import os

class FileClientService(rpyc.Service):
    def __init__(self, file_client):
        self.file_client = file_client  # Referência ao cliente para notificação

    def exposed_notify_event(self, file_name):
        self.file_client.notify_event(file_name)  # Chama o método de notificação do cliente

class FileClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente de Arquivo")
        self.root.geometry("600x600")  # Define o tamanho da janela principal
        self.conn = rpyc.connect("localhost", 18861)  # Conecta ao servidor RPyC
        self.download_folder = None  # Pasta de download inicial (nenhuma selecionada)
        self.setup_ui()  # Configura a interface do usuário

    def setup_ui(self):
        # Frame para Upload e Listagem
        frame_top = Frame(self.root, pady=10)
        frame_top.pack(fill=X)

        self.label = Label(frame_top, text="Cliente de Arquivo", font=("Helvetica", 16))
        self.label.pack(side=TOP, pady=10)

        self.upload_button = Button(frame_top, text="Fazer Upload de Arquivo", command=self.upload_file)
        self.upload_button.pack(side=LEFT, padx=10)

        self.list_button = Button(frame_top, text="Listar Arquivos", command=self.list_files)
        self.list_button.pack(side=LEFT, padx=10)

        # Frame para Listbox de arquivos
        frame_middle = Frame(self.root)
        frame_middle.pack(fill=BOTH, expand=True, pady=10)

        self.file_listbox = Listbox(frame_middle, height=10)
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(frame_middle)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)

        # Frame para Download e Registrar Interesse
        frame_bottom = Frame(self.root, pady=10)
        frame_bottom.pack(fill=X)

        # Download
        download_frame = Frame(frame_bottom)
        download_frame.pack(fill=X, padx=10, pady=5)

        self.download_label = Label(download_frame, text="Nome do Arquivo para Download:")
        self.download_label.pack(side=LEFT)

        self.download_name_entry = Entry(download_frame)
        self.download_name_entry.pack(side=LEFT, fill=X, expand=True)

        self.download_button = Button(download_frame, text="Baixar Arquivo", command=self.download_file)
        self.download_button.pack(side=LEFT, padx=5)

        # Selecionar pasta de download
        self.select_folder_button = Button(download_frame, text="Selecionar Pasta de Download", command=self.select_download_folder)
        self.select_folder_button.pack(side=LEFT)

        # Registrar Interesse
        interest_frame = Frame(frame_bottom)
        interest_frame.pack(fill=X, padx=10, pady=5)

        self.file_name_entry = Entry(interest_frame)
        self.file_name_entry.pack(side=LEFT, fill=X, expand=True)
        self.file_name_entry.insert(0, "Nome do Arquivo")

        self.duration_entry = Entry(interest_frame)
        self.duration_entry.pack(side=LEFT, padx=5)
        self.duration_entry.insert(0, "Duração (s)")

        self.register_button = Button(interest_frame, text="Registrar Interesse", command=self.register_interest)
        self.register_button.pack(side=LEFT, padx=5)

        self.cancel_button = Button(interest_frame, text="Cancelar Interesse", command=self.cancel_interest)
        self.cancel_button.pack(side=LEFT)

        # Botão de sair
        self.exit_button = Button(self.root, text="Sair", command=self.root.quit)
        self.exit_button.pack(fill=BOTH, side=TOP, pady=10, padx=10)

    def upload_file(self):
        file_path = filedialog.askopenfilename()  # Abre o diálogo para selecionar um arquivo
        if file_path:
            file_name = os.path.basename(file_path)  # Obtém o nome do arquivo
            with open(file_path, 'rb') as file:
                file_data = file.read()  # Lê o conteúdo do arquivo
            try:
                self.conn.root.upload_file(file_name, file_data)  # Envia o arquivo para o servidor
                messagebox.showinfo("Sucesso", "Arquivo enviado com sucesso!")  # Exibe mensagem de sucesso
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível fazer o upload: {e}")  # Exibe mensagem de erro

    def list_files(self):
        try:
            files = self.conn.root.list_files()  # Solicita a lista de arquivos ao servidor
            self.file_listbox.delete(0, END)  # Limpa a lista de arquivos existente
            for file_name, file_size in files:
                self.file_listbox.insert(END, f"{file_name}: {file_size} bytes")  # Adiciona os arquivos à lista
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível listar os arquivos: {e}")  # Exibe mensagem de erro

    def download_file(self):
        file_name = self.download_name_entry.get()  # Obtém o nome do arquivo a ser baixado
        if not file_name:
            messagebox.showwarning("Aviso", "Por favor, insira o nome do arquivo.")  # Exibe aviso se o nome do arquivo estiver vazio
            return

        if not self.download_folder:
            messagebox.showwarning("Aviso", "Por favor, selecione a pasta para salvar o arquivo.")  # Exibe aviso se a pasta não estiver selecionada
            return

        try:
            file_data = self.conn.root.download_file(file_name)  # Solicita o download do arquivo ao servidor
            if file_data:
                file_path = os.path.join(self.download_folder, file_name)
                with open(file_path, 'wb') as file:
                    file.write(file_data)  # Salva o arquivo na pasta selecionada
                messagebox.showinfo("Sucesso", "Arquivo baixado com sucesso!")  # Exibe mensagem de sucesso
            else:
                messagebox.showerror("Erro", f"Arquivo '{file_name}' não encontrado no servidor.")  # Exibe mensagem de erro se o arquivo não for encontrado
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível fazer o download: {e}")  # Exibe mensagem de erro

    def register_interest(self):
        file_name = self.file_name_entry.get()  # Obtém o nome do arquivo para registrar interesse
        try:
            duration = float(self.duration_entry.get())  # Obtém e valida a duração
            if duration <= 0:
                raise ValueError("A duração deve ser um número positivo.")
        except ValueError as e:
            messagebox.showerror("Erro", f"Entrada inválida: {e}")  # Exibe mensagem de erro se a duração for inválida
            return

        try:
            client_service = FileClientService(self)  # Cria uma instância do serviço de cliente para notificação
            self.conn.root.register_interest(file_name, client_service, duration)  # Registra o interesse no servidor
            messagebox.showinfo("Sucesso", "Interesse registrado com sucesso!")  # Exibe mensagem de sucesso
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível registrar o interesse: {e}")  # Exibe mensagem de erro

    def cancel_interest(self):
        file_name = self.file_name_entry.get()  # Obtém o nome do arquivo para cancelar o interesse
        try:
            self.conn.root.cancel_interest(file_name)  # Solicita o cancelamento do interesse ao servidor
            messagebox.showinfo("Sucesso", "Interesse cancelado com sucesso!")  # Exibe mensagem de sucesso
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível cancelar o interesse: {e}")  # Exibe mensagem de erro

    def notify_event(self, file_name):
        messagebox.showinfo("Notificação", f"O arquivo '{file_name}' está disponível.")  # Notifica o cliente sobre a disponibilidade do arquivo

    def select_download_folder(self):
        folder = filedialog.askdirectory()  # Abre o diálogo para selecionar a pasta de download
        if folder:
            self.download_folder = folder
            messagebox.showinfo("Pasta Selecionada", f"Pasta para downloads definida como: {folder}")  # Exibe mensagem de sucesso

if __name__ == "__main__":
    root = Tk()
    client = FileClient(root)  # Cria a instância do cliente
    root.mainloop()  # Inicia o loop principal da interface gráfica
