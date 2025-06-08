import os
import sys
import shutil
import hashlib
import platform
import subprocess
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

# -------------------- Validação do CPF e CNPJ --------------------
def validar_cpf(cpf: str) -> bool:
    cpf_numeros = "".join([d for d in cpf if d.isdigit()])
    if len(cpf_numeros) != 11:
        return False
    if len(set(cpf_numeros)) == 1:
        return False
    soma = sum(int(cpf_numeros[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    dv1 = 11 - resto if resto > 1 else 0
    if dv1 != int(cpf_numeros[9]):
        return False
    soma = sum(int(cpf_numeros[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    dv2 = 11 - resto if resto > 1 else 0
    if dv2 != int(cpf_numeros[10]):
        return False
    return True

def validar_cnpj(cnpj: str) -> bool:
    cnpj_numeros = "".join([d for d in cnpj if d.isdigit()])
    if len(cnpj_numeros) != 14:
        return False
    if len(set(cnpj_numeros)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj_numeros[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if dv1 != int(cnpj_numeros[12]):
        return False
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj_numeros[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    if dv2 != int(cnpj_numeros[13]):
        return False
    return True

# -------------------- Classes de Entrada com Máscaras --------------------
class CPFEntry(ttk.Entry):
    def __init__(self, master=None, **kwargs):
        self.var = ttk.StringVar()
        super().__init__(master, textvariable=self.var, **kwargs)
        self.bind("<FocusOut>", self.apply_mask)

    def apply_mask(self, event=None):
        value = self.var.get()
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) == 11:
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            self.var.set(formatted)

class CNPJEntry(ttk.Entry):
    def __init__(self, master=None, **kwargs):
        self.var = ttk.StringVar()
        super().__init__(master, textvariable=self.var, **kwargs)
        self.bind("<FocusOut>", self.apply_mask)

    def apply_mask(self, event=None):
        value = self.var.get()
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) == 14:
            formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
            self.var.set(formatted)

# -------------------- Função para Abrir Pasta --------------------
def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.call(["open", path])
    elif platform.system() == "Linux":
        subprocess.call(["xdg-open", path])
    else:
        print("Sistema operacional não suportado para abrir pastas automaticamente.")

# -------------------- Classe Principal do Aplicativo --------------------
class HashReporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hash PM - Aquisição de Evidência Digital - Versão 1.0")
        self.root.geometry("1400x800")
        self.file_paths = []
        self.setup_ui()

    def setup_ui(self):
        self.style = ttk.Style("litera")
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill='both')

        title_label = ttk.Label(
            main_frame,
            text="AQUISIÇÃO DE EVIDÊNCIAS DIGITAIS",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        file_frame = ttk.Labelframe(main_frame, text="Arquivos para Análise", padding=10)
        file_frame.pack(fill='both', expand=True, pady=5)

        self.file_listbox = tk.Listbox(file_frame, width=80, height=10)
        self.file_listbox.pack(side="left", fill="both", expand=True, padx=5)

        scrollbar = ttk.Scrollbar(file_frame)
        scrollbar.pack(side="left", fill="y")
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)

        button_frame = ttk.Frame(file_frame)
        button_frame.pack(side="right", fill="y", padx=10, pady=5)
        ttk.Button(button_frame, text="Adicionar", command=self.browse_files, width=15).pack(pady=5)
        ttk.Button(button_frame, text="Remover", command=self.remove_selected, width=15).pack(pady=5)
        ttk.Button(button_frame, text="Limpar", command=self.clear_list, width=15).pack(pady=5)

        # Frame para conter os dados do apreensor e proprietário lado a lado
        data_container = ttk.Frame(main_frame)
        data_container.pack(fill="x", pady=5)
        data_container.grid_columnconfigure(0, weight=1)
        data_container.grid_columnconfigure(1, weight=1)

        # Frame para dados do apreensor
        apreensor_frame = ttk.Labelframe(data_container, text="Dados do Apreensor", padding=10)
        apreensor_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        apreensor_frame.grid_columnconfigure(1, weight=1)

        labels_apreensor = ["Nome", "Posto/Graduação", "CPF", "Função", "Orgão", "Portaria", "Unidade da Federação"]
        self.entries_apreensor = {}
        posto_options = ["Cel PM", "TCel PM", "Major PM", "Cap PM", "1ºTen PM", "2ºTen PM", "SubTen PM", "1ºSgt PM", "2ºSgt PM", "3ºSgt PM", "Cabo", "Sd PM"]
        funcao_options = ["Autoridade de PJM", "Autoridade Delegada de PJM", "Escrivão PJM"]
        uf_options = [
            "Acre", "Amapá", "Amazonas", "Pará", "Rondônia", "Roraima", "Tocantins",
            "Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba", "Pernambuco", "Piauí",
            "Rio Grande do Norte", "Sergipe", "Goiás", "Mato Grosso", "Mato Grosso do Sul",
            "Distrito Federal", "Espírito Santo", "Minas Gerais", "Rio de Janeiro", "São Paulo",
            "Paraná", "Santa Catarina", "Rio Grande do Sul"
        ]

        for i, label_text in enumerate(labels_apreensor):
            row = i
            ttk.Label(apreensor_frame, text=label_text + ":").grid(row=row, column=0, padx=5, pady=5, sticky='e')
            if label_text == "Posto/Graduação":
                entry = ttk.Combobox(apreensor_frame, values=posto_options, width=23, state="readonly")
            elif label_text == "Função":
                entry = ttk.Combobox(apreensor_frame, values=funcao_options, width=23, state="readonly")
            elif label_text == "CPF":
                entry = CPFEntry(apreensor_frame, width=25)
            elif label_text == "Unidade da Federação":
                entry = ttk.Combobox(apreensor_frame, values=uf_options, width=23, state="readonly")
            else:
                entry = ttk.Entry(apreensor_frame, width=25)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
            self.entries_apreensor[label_text] = entry

        # Frame para dados do proprietário
        proprietario_frame = ttk.Labelframe(data_container, text="Dados do Proprietário", padding=10)
        proprietario_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        proprietario_frame.grid_columnconfigure(1, weight=1)

        labels_proprietario = ["Nome", "Tipo", "CPF/CNPJ"]
        self.entries_proprietario = {}
        tipo_options = ["Pessoa Física", "Pessoa Jurídica", "Indeterminado"]

        for i, label_text in enumerate(labels_proprietario):
            row = i
            ttk.Label(proprietario_frame, text=label_text + ":").grid(row=row, column=0, padx=5, pady=5, sticky='e')
            if label_text == "Tipo":
                entry = ttk.Combobox(proprietario_frame, values=tipo_options, width=23, state="readonly")
                entry.bind("<<ComboboxSelected>>", self.update_document_entry)
            elif label_text == "CPF/CNPJ":
                entry = CPFEntry(proprietario_frame, width=25)
            else:
                entry = ttk.Entry(proprietario_frame, width=25)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
            self.entries_proprietario[label_text] = entry

        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.status_var = ttk.StringVar()
        self.status_var.set("Pronto.")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w", padding=5)
        self.status_bar.pack(side="bottom", fill="x")

        ttk.Button(
            main_frame,
            text="Gerar Certidão",
            command=self.thread_generate_report,
            bootstyle=SUCCESS,
            width=20
        ).pack(pady=10)

        sobre_frame = ttk.Frame(self.root)
        sobre_frame.pack(side="bottom", anchor="se", padx=10, pady=10)
        ttk.Button(sobre_frame, text="Sobre o HashBM", command=self.mostrar_sobre).pack()

    def update_document_entry(self, event=None):
        tipo = self.entries_proprietario["Tipo"].get()
        current_entry = self.entries_proprietario["CPF/CNPJ"]
        current_entry.destroy()
        if tipo == "Pessoa Física":
            entry = CPFEntry(self.entries_proprietario["Tipo"].master, width=25)
        elif tipo == "Pessoa Jurídica":
            entry = CNPJEntry(self.entries_proprietario["Tipo"].master, width=25)
        else:
            entry = ttk.Entry(self.entries_proprietario["Tipo"].master, width=25)
        entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.entries_proprietario["CPF/CNPJ"] = entry

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def browse_files(self):
        filepaths = filedialog.askopenfilenames()
        if filepaths:
            for filepath in filepaths:
                if filepath not in self.file_paths:
                    self.file_paths.append(filepath)
                    self.file_listbox.insert(tk.END, filepath)
            self.update_status(f"{len(self.file_paths)} arquivo(s) selecionado(s).")

    def remove_selected(self):
        selected = self.file_listbox.curselection()
        if selected:
            index = selected[0]
            del self.file_paths[index]
            self.file_listbox.delete(index)
            self.update_status("Arquivo removido.")

    def clear_list(self):
        self.file_paths = []
        self.file_listbox.delete(0, tk.END)
        self.update_status("Lista de arquivos limpa.")

    def calculate_hashes(self, file_paths, progress_callback=None):
        hashes = {}
        total_files = len(file_paths)
        for i, file_path in enumerate(file_paths):
            sha256 = hashlib.sha256()
            try:
                file_size = os.path.getsize(file_path)
                chunk_size = 8192
                bytes_read = 0
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        sha256.update(chunk)
                        bytes_read += len(chunk)
                        if progress_callback and file_size > 0:
                            progress = int(((i + (bytes_read / file_size)) / total_files) * 100)
                            progress_callback(progress)
                hashes[file_path] = {"SHA-256": sha256.hexdigest()}
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao calcular hash para {os.path.basename(file_path)}:\n{e}")
                return None
        return hashes

    def create_evidence_folders(self, portaria):
        base_folder = f"Evidencias_Adquiridas_Portaria_{portaria}"
        arquivos_folder = os.path.join(base_folder, "Arquivos")
        certidoes_folder = os.path.join(base_folder, "Certidões")
        os.makedirs(base_folder, exist_ok=True)
        os.makedirs(arquivos_folder, exist_ok=True)
        os.makedirs(certidoes_folder, exist_ok=True)
        return base_folder, arquivos_folder, certidoes_folder

    def copy_files_to_evidence(self, file_paths, destination_folder):
        copied_files = []
        for file_path in file_paths:
            try:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(destination_folder, filename)
                shutil.copy2(file_path, dest_path)
                copied_files.append(dest_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao copiar arquivo {filename}:\n{e}")
                return None
        return copied_files

    def generate_minuta_juntada(self, file_paths, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("MINUTA DE JUNTADA\n\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write("LISTA DE ARQUIVOS ADQUIRIDOS:\n\n")
            for i, file_path in enumerate(file_paths, 1):
                f.write(f"{i}. {os.path.basename(file_path)}\n")

    def generate_pdf(self, file_paths, user_data, proprietario_data, hashes, output_path):
        # Mapping of Unidade da Federação to header details
        state_headers = {
            "Acre": ("Estado do Acre", "Secretaria de Estado de Justiça e Segurança Pública", "Polícia Militar do Acre"),
            "Amapá": ("Estado do Amapá", "Secretaria de Estado da Justiça e Segurança Pública", "Polícia Militar do Amapá"),
            "Amazonas": ("Estado do Amazonas", "Secretaria de Estado de Segurança Pública", "Polícia Militar do Amazonas"),
            "Pará": ("Estado do Pará", "Secretaria de Estado de Segurança Pública e Defesa Social", "Polícia Militar do Pará"),
            "Rondônia": ("Estado de Rondônia", "Secretaria de Estado da Segurança, Defesa e Cidadania", "Polícia Militar do Estado de Rondônia"),
            "Roraima": ("Estado de Roraima", "Secretaria de Estado da Segurança Pública", "Polícia Militar de Roraima"),
            "Tocantins": ("Estado do Tocantins", "Secretaria da Segurança Pública", "Polícia Militar do Tocantins"),
            "Alagoas": ("Estado de Alagoas", "Secretaria de Estado da Segurança Pública", "Polícia Militar de Alagoas"),
            "Bahia": ("Estado da Bahia", "Secretaria de Segurança Pública", "Polícia Militar da Bahia"),
            "Ceará": ("Estado do Ceará", "Secretaria da Segurança Pública e Defesa Social", "Polícia Militar do Ceará"),
            "Maranhão": ("Estado do Maranhão", "Secretaria de Estado da Segurança Pública", "Polícia Militar do Maranhão"),
            "Paraíba": ("Estado da Paraíba", "Secretaria de Estado da Segurança e da Defesa Social", "Polícia Militar da Paraíba"),
            "Pernambuco": ("Estado de Pernambuco", "Secretaria de Defesa Social", "Polícia Militar de Pernambuco"),
            "Piauí": ("Estado do Piauí", "Secretaria de Estado da Segurança Pública", "Polícia Militar do Piauí"),
            "Rio Grande do Norte": ("Estado do Rio Grande do Norte", "Secretaria de Estado da Segurança Pública e da Defesa Social", "Polícia Militar do Rio Grande do Norte"),
            "Sergipe": ("Estado de Sergipe", "Secretaria de Estado da Segurança Pública", "Polícia Militar do Estado de Sergipe"),
            "Goiás": ("Estado de Goiás", "Secretaria de Estado de Segurança Pública", "Polícia Militar do Estado de Goiás"),
            "Mato Grosso": ("Estado de Mato Grosso", "Secretaria de Estado de Segurança Pública", "Polícia Militar do Estado de Mato Grosso"),
            "Mato Grosso do Sul": ("Estado de Mato Grosso do Sul", "Secretaria de Estado de Justiça e Segurança Pública", "Polícia Militar de Mato Grosso do Sul"),
            "Distrito Federal": ("Distrito Federal", "Secretaria de Estado de Segurança Pública do Distrito Federal", "Polícia Militar do Distrito Federal"),
            "Espírito Santo": ("Estado do Espírito Santo", "Secretaria de Estado da Segurança Pública e Defesa Social", "Polícia Militar do Espírito Santo"),
            "Minas Gerais": ("Estado de Minas Gerais", "Secretaria de Estado de Justiça e Segurança Pública", "Polícia Militar de Minas Gerais"),
            "Rio de Janeiro": ("Estado do Rio de Janeiro", "Secretaria de Estado de Polícia Militar", "Polícia Militar do Estado do Rio de Janeiro"),
            "São Paulo": ("Estado de São Paulo", "Secretaria da Segurança Pública", "Polícia Militar do Estado de São Paulo"),
            "Paraná": ("Estado do Paraná", "Secretaria de Estado da Segurança Pública", "Polícia Militar do Paraná"),
            "Santa Catarina": ("Estado de Santa Catarina", "Secretaria de Estado da Segurança Pública", "Polícia Militar de Santa Catarina"),
            "Rio Grande do Sul": ("Estado do Rio Grande do Sul", "Secretaria de Segurança Pública", "Brigada Militar")
        }

        selected_uf = user_data.get("Unidade da Federação", "Rio Grande do Sul")
        state, secretariat, police = state_headers.get(selected_uf, state_headers["Rio Grande do Sul"])

        now = datetime.now()
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        margin_left = 2 * cm
        margin_right = width - 1.5 * cm
        margin_top = height - 1.5 * cm
        margin_bottom = 1.5 * cm

        available_height = height - margin_top - margin_bottom

        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        certidao_style = ParagraphStyle('Certidao', parent=normal_style, fontSize=12, leading=14, alignment=4)
        title_style = ParagraphStyle('Title', parent=normal_style, fontName='Helvetica-Bold', fontSize=14, alignment=1)
        header_style = ParagraphStyle('Header', parent=normal_style, fontName='Helvetica', fontSize=12, alignment=1, leading=14)
        info_style = ParagraphStyle('Info', parent=normal_style, fontSize=10, leading=14, spaceAfter=5)
        file_info_style = ParagraphStyle('FileInfo', parent=normal_style, fontSize=10, leading=14, leftIndent=12)
        section_title_style = ParagraphStyle('SectionTitle', parent=normal_style, fontName='Helvetica-Bold', fontSize=10, leading=14)

        current_y = margin_top

        def check_space(required_height):
            nonlocal current_y
            if current_y - required_height < margin_bottom:
                self.add_footer(c, width, height, now)
                c.showPage()
                current_y = margin_top
                return True
            return False

        def draw_centered_text(text, style, y):
            available_width = margin_right - margin_left
            p = Paragraph(text, style)
            w, h = p.wrap(available_width, available_height)
            if check_space(h):
                y = margin_top
            x = margin_left + (available_width - w) / 2
            p.drawOn(c, x, y - h)
            return h

        try:
            brasao_path = self.get_resource_path("brasao.png")
            brasao_width = 2.5 * cm
            brasao_height = 3 * cm
            if check_space(brasao_height + 0.5 * cm):
                current_y = margin_top
            c.drawImage(brasao_path, (width - brasao_width) / 2, current_y - brasao_height,
                        width=brasao_width, height=brasao_height, preserveAspectRatio=True, mask='auto')
            current_y -= brasao_height + 0.5 * cm
        except Exception:
            pass

        current_y -= draw_centered_text(state, header_style, current_y)
        current_y -= 0.3 * cm  # Reduced spacing for single spacing
        current_y -= draw_centered_text(secretariat, header_style, current_y)
        current_y -= 0.3 * cm  # Reduced spacing for single spacing
        current_y -= draw_centered_text(police, header_style, current_y)
        current_y -= 1 * cm  # Reduced spacing after header

        current_y -= draw_centered_text("CERTIDÃO DE AQUISIÇÃO", title_style, current_y)
        current_y -= 0.3 * cm  # Reduced spacing for single spacing
        current_y -= draw_centered_text("DE EVIDÊNCIA DIGITAL", title_style, current_y)
        current_y -= 1 * cm  # Reduced spacing after title

        cert_text = (
            f"Certifico a aquisição da evidência digital abaixo relacionada em {now.strftime('%d/%m/%Y %H:%M')}, "
            f"por {user_data['Posto/Graduação']} {user_data['Nome']}, em conformidade com os Artigos 158-A a 158-D "
            "do CPP e Norma ABNT NBR ISO/IEC 27037:2013.<br/>"
            "O arquivo foi copiado para dispositivo seguro, com hash SHA-256 para integridade.<br/>"
            "Esta aquisição observa os princípios da cadeia de custódia, conforme a legislação vigente, para preservar "
            "a autenticidade e integridade da prova digital."
        )
        p = Paragraph(cert_text, certidao_style)
        w, h = p.wrap(margin_right - margin_left, available_height)
        if check_space(h + 0.5 * cm):
            current_y = margin_top
        p.drawOn(c, margin_left, current_y - h)
        current_y -= h + 0.5 * cm

        if check_space(0.1 * cm):
            current_y = margin_top
        c.line(margin_left, current_y, margin_right, current_y)
        current_y -= 0.5 * cm

        # Dados do apreensor e proprietário lado a lado com títulos alinhados
        column_width = (margin_right - margin_left - 1 * cm) / 2
        apreensor_title = "<b>Apreensor:</b>"
        proprietario_title = "<b>Proprietário das Evidências:</b>"
        apreensor_text = (
            f"<b>Nome:</b> {user_data['Posto/Graduação']} {user_data['Nome']}<br/>"
            f"<b>CPF:</b> {user_data['CPF']}<br/>"
            f"<b>Função:</b> {user_data['Função']}<br/>"
            f"<b>Orgão:</b> {user_data['Orgão']}<br/>"
            f"<b>Portaria:</b> {user_data['Portaria']}<br/>"
            f"<b>Data e hora:</b> {now.strftime('%d/%m/%Y %H:%M:%S')}"
        )
        proprietario_text = (
            f"<b>Nome:</b> {proprietario_data['Nome']}<br/>"
            f"<b>Tipo:</b> {proprietario_data['Tipo']}<br/>"
            f"<b>CPF/CNPJ:</b> {proprietario_data['CPF/CNPJ']}"
        )

        p_apreensor_title = Paragraph(apreensor_title, section_title_style)
        p_proprietario_title = Paragraph(proprietario_title, section_title_style)
        p_apreensor_content = Paragraph(apreensor_text, info_style)
        p_proprietario_content = Paragraph(proprietario_text, info_style)

        w, h_apre_title = p_apreensor_title.wrap(column_width, available_height)
        w, h_proprio_title = p_proprietario_title.wrap(column_width, available_height)
        w, h_apre_content = p_apreensor_content.wrap(column_width, available_height - h_apre_title)
        w, h_proprio_content = p_proprietario_content.wrap(column_width, available_height - h_proprio_title)

        title_height = max(h_apre_title, h_proprio_title)
        content_height = max(h_apre_content, h_proprio_content)
        total_height = title_height + content_height + 0.2 * cm

        if check_space(total_height + 0.5 * cm):
            current_y = margin_top

        p_apreensor_title.drawOn(c, margin_left, current_y - title_height)
        p_proprietario_title.drawOn(c, margin_left + column_width + 1 * cm, current_y - title_height)
        current_y -= title_height + 0.2 * cm

        p_apreensor_content.drawOn(c, margin_left, current_y - h_apre_content)
        p_proprietario_content.drawOn(c, margin_left + column_width + 1 * cm, current_y - h_proprio_content)
        current_y -= content_height + 0.5 * cm

        if check_space(0.1 * cm):
            current_y = margin_top
        c.line(margin_left, current_y, margin_right, current_y)
        current_y -= 0.5 * cm

        for file_path in file_paths:
            base = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            size_kb = round(file_size / 1024, 2)
            file_text = (
                f"<b>Nome:</b> {base}<br/>"
                f"<b>Tamanho:</b> {size_kb} KB<br/>"
                f"<b>Hash SHA-256:</b> {hashes[file_path]['SHA-256']}"
            )
            p = Paragraph(file_text, file_info_style)
            w, h = p.wrap(margin_right - margin_left, available_height)
            if check_space(h + 0.5 * cm):
                current_y = margin_top
            p.drawOn(c, margin_left, current_y - h)
            current_y -= h + 0.5 * cm

            if check_space(0.1 * cm):
                current_y = margin_top
            c.setDash([2, 2], 0)
            c.line(margin_left, current_y, margin_right, current_y)
            c.setDash([])
            current_y -= 0.5 * cm

        if check_space(0.1 * cm):
            current_y = margin_top
        c.line(margin_left, current_y, margin_right, current_y)
        current_y -= 0.5 * cm

        nota_text = (
            "<b>Nota Técnica de Extração:</b><br/>"
            "A extração de hash SHA-256 é utilizada para garantir a integridade de arquivos digitais. "
            "O software Hash BM utiliza linguagem Python e a biblioteca hashlib para ler o arquivo em blocos binários, "
            "gerando um hash que funciona como uma 'impressão digital' do arquivo."
        )
        p = Paragraph(nota_text, file_info_style)
        w, h = p.wrap(margin_right - margin_left, available_height)
        if check_space(h + 0.5 * cm):
            current_y = margin_top
        p.drawOn(c, margin_left, current_y - h)
        current_y -= h + 0.5 * cm

        if check_space(0.1 * cm):
            current_y = margin_top
        c.line(margin_left, current_y, margin_right, current_y)
        current_y -= 3 * cm

        assinatura_area = 3 * cm
        if check_space(assinatura_area):
            current_y = margin_top

        signature_y = margin_bottom + assinatura_area
        sig_width = 8 * cm
        line_left = width / 2 - 4 * cm
        line_right = width / 2 + 4 * cm
        c.line(line_left, signature_y, line_right, signature_y)

        p_assinatura = Paragraph(
            f"{user_data['Posto/Graduação']} {user_data['Nome']}",
            ParagraphStyle('Assinatura', parent=normal_style, fontSize=11, alignment=1)
        )
        w, h = p_assinatura.wrap(sig_width, available_height)
        x = width / 2 - w / 2
        p_assinatura.drawOn(c, x, signature_y - (h + 0.7 * cm))

        self.add_footer(c, width, height, now)
        c.showPage()
        c.save()

    def add_footer(self, c, width, height, now):
        c.setFont("Helvetica", 8)
        footer_text = f"Gerado por Hash PM - Aquisição em {now.strftime('%d/%m/%Y %H:%M')}"
        c.drawString(2 * cm, 1 * cm, footer_text)
        page_num = c.getPageNumber()
        c.drawRightString(width - 1.5 * cm, 1 * cm, f"Página {page_num}")

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.abspath(relative_path)

    def update_progress(self, value):
        self.progress["value"] = int(value)
        self.root.update_idletasks()

    def thread_generate_report(self):
        t = threading.Thread(target=self.generate_report)
        t.start()

    def generate_report(self):
        if not self.file_paths:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo!")
            return

        if isinstance(self.entries_apreensor["CPF"], CPFEntry):
            self.entries_apreensor["CPF"].apply_mask()
        if isinstance(self.entries_proprietario["CPF/CNPJ"], (CPFEntry, CNPJEntry)):
            self.entries_proprietario["CPF/CNPJ"].apply_mask()

        user_data = {key: entry.get().strip() or "Não informado" for key, entry in self.entries_apreensor.items()}
        proprietario_data = {key: entry.get().strip() or "Indeterminado" for key, entry in self.entries_proprietario.items()}

        if not validar_cpf(user_data['CPF']):
            messagebox.showerror("Erro", "CPF do Apreensor inválido! Verifique e tente novamente.")
            return

        if proprietario_data['Tipo'] == "Pessoa Física" and proprietario_data['CPF/CNPJ'] != "Indeterminado":
            if not validar_cpf(proprietario_data['CPF/CNPJ']):
                messagebox.showerror("Erro", "CPF do Proprietário inválido! Verifique e tente novamente.")
                return
        elif proprietario_data['Tipo'] == "Pessoa Jurídica" and proprietario_data['CPF/CNPJ'] != "Indeterminado":
            if not validar_cnpj(proprietario_data['CPF/CNPJ']):
                messagebox.showerror("Erro", "CNPJ do Proprietário inválido! Verifique e tente novamente.")
                return

        if (not user_data['Nome'] or not user_data['Posto/Graduação'] or
                not user_data['CPF'] or not user_data['Portaria']):
            messagebox.showwarning("Aviso", "Preencha todos os dados obrigatórios do Apreensor!")
            return

        portaria = user_data['Portaria']
        base_folder, arquivos_folder, certidoes_folder = self.create_evidence_folders(portaria)
        copied_files = self.copy_files_to_evidence(self.file_paths, arquivos_folder)
        if not copied_files:
            return

        self.update_status("Calculando hashes dos arquivos...")
        self.progress["value"] = 0
        hashes = self.calculate_hashes(copied_files, self.update_progress)
        if hashes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"Certidao_{timestamp}.pdf"
            pdf_path = os.path.join(certidoes_folder, pdf_filename)
            try:
                self.update_status("Gerando relatório PDF...")
                self.generate_pdf(copied_files, user_data, proprietario_data, hashes, pdf_path)
                ninuta_path = os.path.join(certidoes_folder, f"Minuta_de_Juntada_{timestamp}.txt")
                self.generate_minuta_juntada(copied_files, ninuta_path)
                self.update_status("Relatório gerado com sucesso!")
                if messagebox.askyesno("Sucesso", "Certidão e documentos gerados com sucesso!\nDeseja abrir a pasta com os arquivos?"):
                    open_folder(base_folder)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao gerar arquivos:\n{e}")
                self.update_status("Erro na geração do relatório.")

    def mostrar_sobre(self):
        sobre_janela = tk.Toplevel(self.root)
        sobre_janela.title("Sobre Hash PM")
        sobre_janela.geometry("800x600")
        x = (sobre_janela.winfo_screenwidth() - 500) // 2
        y = (sobre_janela.winfo_screenheight() - 500) // 2
        sobre_janela.geometry(f"500x500+{x}+{y}")

        texto = (
            """Hash PM - Aquisição de Evidência Digital - Versão 1.0

O Hash PM é uma ferramenta desenvolvida para auxiliar na extração segura e documentada de arquivos digitais em investigações e procedimentos técnicos. Ele permite que o usuário selecione arquivos do computador ou mídias externas e, ao final da coleta, gera um relatório em PDF completo com:

• Dados do apreensor e proprietário das evidências;
• Informações detalhadas do(s) arquivo(s);
• Hash SHA-256 de cada item coletado;
• Local, data e hora da ação;
• Espaço para validação formal.

Distribuído de forma livre sob a Licença MIT.
Criado por Capitão PM Robinson Lemos - Brigada Militar - RS
robinson-lemos@bm.rs.gov.br
"""
        )

        label = ttk.Label(sobre_janela, text=texto, wraplength=380, padding=10, justify="left")
        label.pack(expand=True, fill="both")

if __name__ == "__main__":
    root = ttk.Window()
    app = HashReporterApp(root)
    root.mainloop()