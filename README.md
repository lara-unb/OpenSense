# OpenSense IMU

Repositório de captura de dados inerciais para o **OpenSense** (OpenSim). 

Este projeto contém scripts em Python desenvolvidos para comunicar com sensores IMU, gravar dados em tempo real e exportá-los para o formato `.json` e `.sto`, permitindo a análise de cinemática inversa no OpenSim.

---

## Visão Geral

O fluxo de trabalho deste repositório é simples:
1. **Conexão:** O script conecta-se ao Dongle USB e recebe dados de múltiplos sensores simultaneamente.
2. **Captura:** Os dados brutos de orientação em quaternions são salvos em formato JSON.
3. **Processamento:** O script converte os dados para o formato `.sto` utilizado no OpenSense.

### Estrutura de Pastas
* [```lara_opensense/```](lara_opensense/): Pasta com os scripts definindo as funções utilizadas no pacote lara_opensense. 
* [```docs/```](docs/): Pasta com documentos e imagens referentes ao projeto.
* [```Models/```](Models/): Modelos opensim disponíveis.
* [```examples/```](examples/): Pasta com exemplos de utilização das funções do lara_opensense.
* [```Training/```](Training/): Pasta com treinamento para novos membros.
* [```Projects/```](Projects/): Pasta com os projetos específicos utilizando o Opensense no laboratório.

---

## Preparação do Ambiente

Siga estes passos para configurar o seu computador na primeira utilização.

### 1. Instalar o Python
É necessário ter o **Python 3.8** (ou superior) instalado.
* Verifique se já possui: Abra o terminal/CMD e digite `python --version`.
* Se não tiver, baixe e instale a partir de [python.org](https://www.python.org/downloads/).
    * *Nota (Windows):* Na instalação, marque a caixa **"Add Python to PATH"**.

### 2. Clone do projeto
Para iniciar utilizando, realize um clone do projeto em uma pasta local:

1. Abra o terminal (ou PowerShell/CMD) na pasta onde deseja fazer o clone.
2. Caso não tenha o git instalado em sua máquina, realize a instalação
3. Faça o clone com o seguinte comando no terminal:
   ```bash
   git clone https://github.com/lara-unb/OpenSense.git
   ```

### 3. Criar o Ambiente Virtual (Venv)
Para manter o projeto organizado e evitar conflitos de bibliotecas, usamos um ambiente virtual.

1. Abra o terminal (ou PowerShell/CMD) na pasta raiz deste projeto.
2. Crie o ambiente executando:
   ```bash
   python3 -m venv .envOpensense
   ```

3. Ative o ambiente:
   * **Windows:**
     ```powershell
     .envOpensense\Scripts\Activate
     ```
   * **Linux / Mac:**
     ```bash
     source .envOpensense/bin/activate
     ```
   *(Você verá `(.envOpensense)` no início da linha de comando quando estiver ativo).*

### 4. Instalar o pacote lara_opensense
Com o ambiente `.envOpensense` ativo e na pasta do projeto, digite com o comando:
```bash
pip install -e .
```

Juntamente com os scripts do pacote lara_opensense, serão instalados os seguintes pacotes:
```text
pyserial
numpy
pandas
scipy
openpyxl
streamlit
```
### 5. Instalação do OpenSim

O **OpenSim** é uma plataforma *open-source* para modelagem e simulação de sistemas biomecânicos. Para este projeto, utilizamos o **OpenSense**, um conjunto de ferramentas (integrado nativamente nas versões recentes) que permite a análise de movimentos a partir de dados de sensores inerciais (IMUs), mapeando-os em modelos musculoesqueléticos.

1.  **Download:** Acesse o site oficial [SimTK - OpenSim](https://simtk.org/frs/?group_id=91).
2.  **Versão Recomendada:** Utilize o **OpenSim 4.5** (versão base deste projeto). Versões superiores podem funcionar, mas esta garante compatibilidade total com os scripts de conversão.
3.  **Cadastro:** Será necessário criar uma conta gratuita no SimTK para baixar os arquivos.
4.  **Aprendizado Adicional:** Para entender a interface além deste guia, consulte os [Tutoriais Oficiais do OpenSim](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53114247/Introductory+Examples).

---

## Primeiros Passos

Para começar a utilizar o projeto, é recomendado realizar os tutoriais da pasta [```Training/```](Training/). 

Comece com o [Tutorial Básico](Training/TutorialBasico/) para aprender a processar uma captura e obter a cinemática inversa pela interface do OpenSim. 

Para realizar sua primeira captura, realize o [tutorial de captura](Training/Captura/).

Para entender melhor como funciona a cinemática inversa no contexto de biomecânica, realize o [tutorial de cinemática inversa](Training/CinematicaInversa/).

