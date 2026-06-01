# Treinamento Básico

## Objetivo
O objetivo deste tutorial é demonstrar o processamento de dados de IMUs em formato ```.sto``` dentro da interface do OpenSim.

### Fluxo de Processamento no OpenSim

#### 1. Preparação do Modelo e Ambiente

No OpenSim, um **modelo** (`.osim`) representa a estrutura física (ossos, juntas e músculos) que será animada. 

> [!CAUTION]
> **Erro 106:** O OpenSim pode falhar ao carregar arquivos em pastas sem permissão de escrita (como dentro de `C:\Program Files`). Recomenda-se criar uma pasta própria em `Documents\OpenSim\4.5\Models\MeuProjeto` e colocar o arquivo `model.osim` e todos os arquivos gerados (`.sto`) nela.

* **Abrir o Modelo:** Use `Ctrl + O` ou vá em `File > Open Model` e selecione o arquivo `model.osim`.
* **Visualização:** Após o carregamento, a interface principal exibirá o modelo esquelético.

![Interface inicial com o modelo carregado](../../docs/imagens/modelo_aberto.png)

#### 2. Ajustes de Coordenadas

Antes de importar os dados, verifique a pose e as articulações na aba lateral esquerda:

* **Aba Navigator:** Lista os modelos ativos.
* **Aba Coordinates:** Permite controlar a angulação das juntas.
    * Clique em `Poses > Default` para garantir a postura padrão.
    * **Trava de Juntas:** Neste repositório, focamos nos movimentos de **Tíbia** e **Fêmur** direitos. Se você não estiver usando sensores para outros membros, clique no ícone de **cadeado** ao lado dos nomes das outras juntas para evitar movimentos indesejados.

#### 3. Posicionamento Virtual (IMU Placer)

O **IMU Placer** alinha a orientação dos sensores reais ao modelo virtual.

1.  Selecione o modelo desejado na aba *Navigator*.
2.  No menu superior, acesse `Tools > IMU Placer`.
3.  Em **"Orientation file at placement pose"**, clique no ícone de pasta e selecione o arquivo **`nome_arquivo_pos.sto`**.
    * *Dica de teste:* Use `examples/exampleLARA/example_filtered_pos.sto`.
4.  Clique em **Run**. Uma cópia do modelo aparecerá com cubos coloridos indicando o local dos sensores.

![Janela do IMU Placer](../../docs/imagens/imu_placer_config.png)

#### 4. Cinemática Inversa (IMU Inverse Kinematics)

Esta etapa aplica os dados de movimento contínuo ao modelo posicionado.

1.  Vá em `Tools > IMU Inverse Kinematics`.
2.  Em **"Sensor orientation file (quaternions)"**, carregue o arquivo **`nome_arquivo_mov.sto`**.
    * *Dica de teste:* Use `examples/exampleLARA/example_filtered_mov.sto`.
3.  Clique em **Run** e aguarde a barra de progresso no canto inferior.
4.  **Reprodução:** Use o slider de "Play" no topo da tela para visualizar o movimento.

![Animação do movimento final](../../docs/imagens/resultado_movimento.gif)
---