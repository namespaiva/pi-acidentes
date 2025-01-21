# Como instalar e rodar o projeto

# Etapa 1 (no terminal)

```bash
# Passo 1: Navegue até o diretório do projeto
cd localdoprojeto

# Passo 2: Crie um ambiente virtual
python -m venv .venv

# Passo 3: Ative o ambiente virtual
# Windows (CMD):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Passo 4: Instale as dependências
pip install -r requirements.txt

# Passo 5: Execute o projeto
streamlit run Acidentes.py

# No terminal vai ter uma mensagem assim:
#   You can now view your Streamlit app in your browser.

#   Local URL: http://localhost:8501
#   Network URL: http://10.10.41.129:8501
```
# Etapa 2 (acesso e geocoding)

Faça o login com algum dos usuários existentes no arquivo config.yaml

Para adicionar usuários, edite o arquivo congif.yaml seguindo o padrão que já está lá.

Nenhuma senha está "hashada" (criptografada)

A página de adicionar não está funcionando, ela serve mais como um protótipo. 

O geocoder grátis não sabe o que é um cruzamento e o da Google é pago.

A leitura de arquivos considera arquivos .xls com uma coluna sem cabeçalho e as colunas:

DATA - HORA - TEMPO - TIPO_ACIDENTE - GRAVIDADE - LOGRADOURO - Nº - CRUZAMENTO

Nessa ordem, escrito dessa exata maneira. Mudanças nas colunas implicarão em mudanças no código de tratamento.

O formato dos dados deve ser (com exemplos):

DATA: (dd/mm/aaaa) 01/01/24

HORA: (hh/mm) 05:26

TEMPO: (texto) [BOM
                CHUVA
                S/I
                NEBLINA
                ]

TIPO_ACIDENTE: (texto) [COLISÃO
                        CHOQUE
                        ABALROAMENTO
                        ATROPELAMENTO
                        TOMBAMENTO
                        NÃO IDENTIFICADO
                        OUTROS
                        CAPOTAMENTO
                        ENGAVETAMENTO
                        ]

GRAVIDADE: (texto) [S/ LESÃO
                    C/ VÍTIMAS LEVES
                    C/ VÍTIMAS GRAVES
                    C/ VÍTIMAS FATAIS
                    ]

LOGRADOURO: (texto) Rua Conselheiro Ribas

Nº: (número inteiro) 0 

CRUZAMENTO: (texto) Rua Oswaldo Cochrane

# Etapa 3 (uso da página Adicionar Acidentes)

1- Primeiro, upe um arquivo .xls, como mencionado acima.

2- Depois, clique no botão "Realizar Geocoding". Espere o mapa e a tabela aparecerem.

3- Verifique se os dados da tabela estão localizados corretamente. Caso não estejam, clique no local onde deveriam estar no mapa, um pop-up aparecerá com a latitude e a longitude do ponto clicado. 

4- Feito isso, insira a latitude no campo "lat" e a longitude no campo "lon". IMPORTANTE: certificar que os dados inseridos possuem casa decimal delimitado por . (ponto final) na terceira casa, por exemplo:
-23.997 -46.338

5- Ao terminar as correções, clique em "Atualizar Mapa" e espere alguns segundos.

6- Verifique os dados novamente. Caso ainda hajam inconsistências, repita os passos 3, 4 e 5.

7- Ao finalizar, clique em "Concatenar" no fim da página. Um novo arquivo com todos os acidentes será gerado.

Em caso de erros (página quebrar, mensagem vermelha, etc) recarregue a página 