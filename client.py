import rpyc
from tkinter import Tk, Label, Button, Listbox, END, Entry, messagebox
from tkinter import filedialog
import os

class FileClient:
    def __init__(self, root):
        self.root = root
        self.conn = rpyc.connect("localhost", 18861)
        self.download_folder = None  # Inicialmente, não há pasta selecionada
        self.setup_ui()

    def setup_ui(self):
        self.label = Label(self.root, text="Cliente de Arquivo")
        self.label.pack()

        self.upload_button = Button(self.root, text="Fazer Upload de Arquivo", command=self.upload_file)
        self.upload_button.pack()

        self.list_button = Button(self.root, text="Listar Arquivos", command=self.list_files)
        self.list_button.pack()

        self.download_label = Label(self.root, text="Baixar Arquivo")
        self.download_label.pack()

        self.download_name_entry = Entry(self.root)
        self.download_name_entry.pack()
        self.download_name_entry.insert(0, "Nome do Arquivo para Download")

        self.download_button = Button(self.root, text="Baixar Arquivo", command=self.download_file)
        self.download_button.pack()

        self.file_listbox = Listbox(self.root)
        self.file_listbox.pack()

        self.interest_label = Label(self.root, text="Registrar Interesse")
        self.interest_label.pack()

        self.file_name_entry = Entry(self.root)
        self.file_name_entry.pack()
        self.file_name_entry.insert(0, "Nome do Arquivo")

        self.duration_entry = Entry(self.root)
        self.duration_entry.pack()
        self.duration_entry.insert(0, "Duração em segundos")

        self.register_button = Button(self.root, text="Registrar Interesse", command=self.register_interest)
        self.register_button.pack()

        self.cancel_button = Button(self.root, text="Cancelar Interesse", command=self.cancel_interest)
        self.cancel_button.pack()

        self.exit_button = Button(self.root, text="Sair", command=self.root.quit)
        self.exit_button.pack()

        self.select_folder_button = Button(self.root, text="Selecionar Pasta de Download", command=self.select_download_folder)
        self.select_folder_button.pack()

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = file_path.split("/")[-1]
            with open(file_path, 'rb') as file:
                file_data = file.read()
            try:
                self.conn.root.upload_file(file_name, file_data)
                messagebox.showinfo("Sucesso", "Arquivo enviado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível fazer o upload: {e}")

    def list_files(self):
        try:
            files = self.conn.root.list_files()
            if not isinstance(files, (list, tuple)):
                raise TypeError("Formato inesperado de dados recebido do servidor.")

            files_dict = {}
            for item in files:
                if isinstance(item, (tuple, list)) and len(item) == 2:
                    file_name, file_size = item
                    files_dict[file_name] = file_size
                else:
                    raise ValueError("Formato de item inesperado na lista de arquivos.")

            files_str = "\n".join([f"{name}: {size} bytes" for name, size in files_dict.items()])
            self.file_listbox.delete(0, END)
            self.file_listbox.insert(END, files_str)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível listar os arquivos: {e}")

    def download_file(self):
        file_name = self.download_name_entry.get()
        if not file_name:
            messagebox.showwarning("Aviso", "Por favor, insira o nome do arquivo.")
            return

        if not self.download_folder:
            messagebox.showwarning("Aviso", "Por favor, selecione a pasta para salvar o arquivo.")
            return

        try:
            file_data = self.conn.root.download_file(file_name)
            if file_data:
                file_path = os.path.join(self.download_folder, file_name)
                with open(file_path, 'wb') as file:
                    file.write(file_data)
                messagebox.showinfo("Sucesso", "Arquivo baixado com sucesso!")
            else:
                messagebox.showerror("Erro", f"Arquivo '{file_name}' não encontrado no servidor.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível fazer o download: {e}")

    def register_interest(self):
        file_name = self.file_name_entry.get()
        try:
            duration = float(self.duration_entry.get())
            if duration <= 0:
                raise ValueError("A duração deve ser um número positivo.")
        except ValueError as e:
            messagebox.showerror("Erro", f"Entrada inválida: {e}")
            return

        try:
            self.conn.root.register_interest(file_name, self, duration)
            messagebox.showinfo("Sucesso", "Interesse registrado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível registrar o interesse: {e}")

    def cancel_interest(self):
        file_name = self.file_name_entry.get()
        try:
            self.conn.root.cancel_interest(file_name)
            messagebox.showinfo("Sucesso", "Interesse cancelado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível cancelar o interesse: {e}")

    def notify_event(self, file_name):
        messagebox.showinfo("Notificação", f"O arquivo '{file_name}' está disponível.")

    def select_download_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder = folder
            messagebox.showinfo("Pasta Selecionada", f"Pasta para downloads definida como: {folder}")

if __name__ == "__main__":
    root = Tk()
    client = FileClient(root)
    root.mainloop()
