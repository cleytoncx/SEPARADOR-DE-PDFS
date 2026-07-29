import streamlit as st
import os
import re
import zipfile
import tempfile
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="Separador de Espelhos de Ponto", page_icon="📄")

st.title("📄 Separador de Espelhos de Ponto")
st.write("Faça o upload do PDF e o sistema irá separar por departamento e colaborador.")

# Função para limpar nomes de arquivos
def limpar_nome(texto):
    return re.sub(r'[\\/*?:"<>|]', "", texto).strip()

uploaded_file = st.file_uploader(
    "Selecione o arquivo PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    reader = PdfReader(uploaded_file)
    arquivos_por_colaborador = {}

    progresso = st.progress(0)
    status = st.empty()

    for i, page in enumerate(reader.pages):

        progresso.progress((i + 1) / len(reader.pages))
        status.text(f"Processando página {i+1}/{len(reader.pages)}")

        texto = page.extract_text()

        if not texto:
            st.warning(f"Página {i+1}: vazia ou ilegível.")
            continue

        nome_match = re.search(r"Nome:\s*(.+)", texto)
        depto_match = re.search(r"Departamento:\s*(.+)", texto)

        if not nome_match or not depto_match:
            st.warning(f"Página {i+1}: Nome ou Departamento não encontrado.")
            continue

        nome = limpar_nome(nome_match.group(1))
        departamento = limpar_nome(depto_match.group(1))

        chave = (departamento, nome)

        if chave not in arquivos_por_colaborador:
            arquivos_por_colaborador[chave] = PdfWriter()

        arquivos_por_colaborador[chave].add_page(page)

    status.text("Gerando arquivos...")

    # Criar pasta temporária
    with tempfile.TemporaryDirectory() as temp_dir:

        for (departamento, nome), writer in arquivos_por_colaborador.items():

            pasta = os.path.join(temp_dir, departamento)
            os.makedirs(pasta, exist_ok=True)

            caminho_pdf = os.path.join(pasta, f"{nome}.pdf")

            with open(caminho_pdf, "wb") as f:
                writer.write(f)

        # Criar ZIP em memória
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    caminho = os.path.join(root, file)
                    nome_zip = os.path.relpath(caminho, temp_dir)
                    zip_file.write(caminho, nome_zip)

        zip_buffer.seek(0)

    progresso.empty()
    status.empty()

    st.success(f"Processo concluído! Foram gerados {len(arquivos_por_colaborador)} arquivos.")

    st.download_button(
        label="📥 Baixar arquivos ZIP",
        data=zip_buffer,
        file_name="espelhos_separados.zip",
        mime="application/zip"
    )