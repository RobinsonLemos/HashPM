# Hash PM - Aquisição de Evidência Digital

Descrição
O Hash PM é uma ferramenta desenvolvida para auxiliar na extração segura e documentada de arquivos digitais em investigações e procedimentos técnicos policiais. Ele permite que o usuário:

- Selecione arquivos do computador ou mídias externas

- Documente os dados do apreensor e proprietário das evidências

- Gere automaticamente um relatório em PDF com:

- Informações detalhadas dos arquivos

- Hash SHA-256 de cada item coletado

- Local, data e hora da ação

- Espaço para validação formal

### Funcionalidades
Validação de documentos: CPF e CNPJ com máscara automática e validação

Geração de certificado: PDF profissional com cabeçalho do órgão

Cadeia de custódia: Organização automática em pastas por número de portaria

Cálculo de hash: SHA-256 para verificação de integridade

Interface intuitiva: Fácil utilização com comboboxes pré-definidos

### Requisitos do Sistema
Python 3.8 ou superior

Sistema operacional: Windows, Linux ou macOS

### Instalação
Clone o repositório:

bash
git clone https://github.com/seu-usuario/hash-pm.git
cd hash-pm
Crie e ative um ambiente virtual (recomendado):

bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
Instale as dependências:

bash
pip install -r requirements.txt

### Como Usar

Execute o aplicativo:

*python HashPM.py*

Na interface:

- Adicione arquivos para análise
- Preencha os dados do apreensor e proprietário
- Clique em "Gerar Certidão"

O sistema irá:

- Criar uma pasta organizada por portaria
- Copiar os arquivos originais
- Gerar a certidão em PDF e minuta de juntada

### Tecnologias Utilizadas

- Python 3
- Tkinter/ttkbootstrap para interface gráfica
- ReportLab para geração de PDF
- Hashlib para cálculo de hashes

### Licença

Distribuído sob a licença MIT. Veja o arquivo LICENSE para mais informações.
Desenvolvedor: Capitão PM Robinson Lemos - Brigada Militar - RS
Email: robinson-lemos@bm.rs.gov.br
