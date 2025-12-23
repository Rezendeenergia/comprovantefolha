import streamlit as st
import PyPDF2
import re
import io
import zipfile
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Renomear Comprovantes",
    page_icon="📄",
    layout="wide"
)

# CSS customizado com as cores da empresa
st.markdown("""
    <style>
    .main {
        background-color: #FFFFFF;
    }
    .stApp {
        background-color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #000000;
    }
    .success-box {
        background-color: #F7931E;
        color: #000000;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #F7931E;
        color: #000000;
        border: none;
        font-weight: bold;
        padding: 10px 25px;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #D87D1A;
        color: #000000;
    }
    .divider {
        border-top: 3px solid #F7931E;
        margin: 30px 0;
    }
    </style>
""", unsafe_allow_html=True)


def extrair_nome_do_pdf(pdf_file):
    """
    Extrai o nome do destinatário do comprovante de pagamento PIX
    """
    try:
        # Ler o PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        texto = ""

        # Extrair texto de todas as páginas
        for page in pdf_reader.pages:
            texto += page.extract_text()

        # Procurar pelo nome do destinatário
        # Padrão: "Nome: " seguido do nome
        padrao_nome = r'Nome:\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|CPF)'
        match = re.search(padrao_nome, texto)

        if match:
            nome = match.group(1).strip()
            # Limpar espaços extras e caracteres especiais
            nome = re.sub(r'\s+', ' ', nome)
            return nome
        else:
            return None

    except Exception as e:
        st.error(f"Erro ao processar PDF: {str(e)}")
        return None


def processar_arquivos(arquivos_upload, tipo_pagamento):
    """
    Processa os arquivos PDF e retorna lista de arquivos renomeados
    """
    arquivos_renomeados = []
    erros = []

    for arquivo in arquivos_upload:
        try:
            # Resetar o ponteiro do arquivo
            arquivo.seek(0)

            # Extrair nome
            nome = extrair_nome_do_pdf(arquivo)

            if nome:
                # Criar novo nome de arquivo
                # Remover caracteres inválidos para nome de arquivo
                nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
                nome_limpo = nome_limpo.replace(' ', '_')

                # Adicionar tipo de pagamento
                novo_nome = f"{nome_limpo}_{tipo_pagamento}.pdf"

                # Resetar ponteiro e ler conteúdo
                arquivo.seek(0)
                conteudo = arquivo.read()

                arquivos_renomeados.append({
                    'nome_original': arquivo.name,
                    'nome_novo': novo_nome,
                    'nome_pessoa': nome,
                    'conteudo': conteudo
                })
            else:
                erros.append(f"❌ {arquivo.name}: Não foi possível extrair o nome")

        except Exception as e:
            erros.append(f"❌ {arquivo.name}: Erro - {str(e)}")

    return arquivos_renomeados, erros


def criar_zip(arquivos_renomeados, tipo_pagamento):
    """
    Cria um arquivo ZIP com os arquivos renomeados
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for arquivo in arquivos_renomeados:
            zip_file.writestr(arquivo['nome_novo'], arquivo['conteudo'])

    zip_buffer.seek(0)
    return zip_buffer


# Título principal
st.title("📄 Renomear Comprovantes de Pagamento")
st.markdown("### Sistema de renomeação automática de comprovantes PIX")
st.markdown("---")

# Criar duas colunas para os dois tipos de pagamento
col1, col2 = st.columns(2)

# ============= COLUNA 1: SALÁRIO =============
with col1:
    st.markdown("### 💰 Comprovantes de Salário")
    st.markdown("Faça upload dos comprovantes de pagamento de salário")

    arquivos_salario = st.file_uploader(
        "Selecione os PDFs de salário",
        type=['pdf'],
        accept_multiple_files=True,
        key="salario"
    )

    if arquivos_salario:
        st.info(f"📊 {len(arquivos_salario)} arquivo(s) carregado(s)")

        if st.button("🔄 Processar Salários", key="btn_salario"):
            with st.spinner("Processando comprovantes de salário..."):
                arquivos_processados, erros = processar_arquivos(arquivos_salario, "SALARIO")

                if arquivos_processados:
                    st.markdown('<div class="success-box">✅ Processamento concluído!</div>', unsafe_allow_html=True)

                    # Mostrar resultados
                    st.markdown("#### 📋 Arquivos Renomeados:")
                    for arq in arquivos_processados:
                        st.success(f"✓ **{arq['nome_pessoa']}**\n\n`{arq['nome_novo']}`")

                    # Criar ZIP
                    zip_buffer = criar_zip(arquivos_processados, "SALARIO")

                    # Botão de download
                    st.download_button(
                        label="⬇️ Baixar Todos os Salários (.zip)",
                        data=zip_buffer,
                        file_name=f"Comprovantes_Salario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="download_salario"
                    )

                if erros:
                    st.markdown("#### ⚠️ Erros Encontrados:")
                    for erro in erros:
                        st.warning(erro)

# ============= COLUNA 2: AJUDA DE CUSTO =============
with col2:
    st.markdown("### 🎯 Comprovantes de Ajuda de Custo")
    st.markdown("Faça upload dos comprovantes de ajuda de custo")

    arquivos_ajuda = st.file_uploader(
        "Selecione os PDFs de ajuda de custo",
        type=['pdf'],
        accept_multiple_files=True,
        key="ajuda_custo"
    )

    if arquivos_ajuda:
        st.info(f"📊 {len(arquivos_ajuda)} arquivo(s) carregado(s)")

        if st.button("🔄 Processar Ajuda de Custo", key="btn_ajuda"):
            with st.spinner("Processando comprovantes de ajuda de custo..."):
                arquivos_processados, erros = processar_arquivos(arquivos_ajuda, "AJUDA_CUSTO")

                if arquivos_processados:
                    st.markdown('<div class="success-box">✅ Processamento concluído!</div>', unsafe_allow_html=True)

                    # Mostrar resultados
                    st.markdown("#### 📋 Arquivos Renomeados:")
                    for arq in arquivos_processados:
                        st.success(f"✓ **{arq['nome_pessoa']}**\n\n`{arq['nome_novo']}`")

                    # Criar ZIP
                    zip_buffer = criar_zip(arquivos_processados, "AJUDA_CUSTO")

                    # Botão de download
                    st.download_button(
                        label="⬇️ Baixar Todas as Ajudas de Custo (.zip)",
                        data=zip_buffer,
                        file_name=f"Comprovantes_Ajuda_Custo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="download_ajuda"
                    )

                if erros:
                    st.markdown("#### ⚠️ Erros Encontrados:")
                    for erro in erros:
                        st.warning(erro)

# Divisor
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Instruções
with st.expander("📖 Como usar o sistema"):
    st.markdown("""
    ### Instruções de Uso:

    1. **Selecione a categoria:**
       - Use a coluna da esquerda para comprovantes de **Salário**
       - Use a coluna da direita para comprovantes de **Ajuda de Custo**

    2. **Faça o upload dos arquivos:**
       - Clique no botão de upload correspondente
       - Selecione um ou múltiplos arquivos PDF
       - Os arquivos devem ser comprovantes de pagamento PIX do Omie

    3. **Processe os arquivos:**
       - Clique no botão "Processar" da categoria escolhida
       - O sistema irá extrair automaticamente o nome do destinatário
       - Os arquivos serão renomeados no formato: `Nome_Pessoa_TIPO.pdf`

    4. **Baixe os resultados:**
       - Clique no botão de download para obter todos os arquivos em um ZIP
       - Os arquivos estarão organizados e prontos para uso

    ### Formato dos Nomes:
    - Salário: `Eder_Melo_dos_Santos_SALARIO.pdf`
    - Ajuda de Custo: `Eder_Melo_dos_Santos_AJUDA_CUSTO.pdf`

    ### Requisitos:
    - Os PDFs devem conter o padrão de comprovante do Omie Cash
    - O nome do destinatário deve estar visível no documento
    """)

# Rodapé
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>Rezende Energia</strong> | Sistema de Gestão de Comprovantes</p>
    </div>
""", unsafe_allow_html=True)