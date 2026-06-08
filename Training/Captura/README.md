### Como Realizar uma Coleta

#### Passo 1: Configuração dos Sensores
Antes de rodar o código, você deve informar quais sensores está usando. Abra o arquivo `motion_capture.py` numa IDE (VS Code, PyCharm, etc) e edite as variáveis iniciais:

```python
# IDs lógicos dos sensores (verifique o número escrito no hardware do sensor)
imu_ids = [9, 10]

# Nomes dos segmentos no OpenSim
# A ordem deve corresponder exatamente aos IDs acima
imu_labels = ["femur_r_imu", "tibia_r_imu"]

# Caminho e nome do arquivo a ser salvo sem extensão
file_name = "examples/Coleta_Sujeito01/caminhada_teste"
```

#### Passo 2: Inicialização e Referencial
Esta etapa define a orientação global dos sensores.

1. Posicionamento na Mesa: Antes de iniciar o programa, coloque os IMUs em uma mesa plana, um ao lado do outro. Aponte o lado do LED dos sensores para a direção em que o movimento será capturado.

2. Conecte o Dongle USB ao computador e ligue os sensores IMU.

3. No terminal (com o `.envOpensense` ativado), execute:
    ```bash
    python runOpenSenseCapture.py
    ```
    Aguarde o terminal exibir a mensagem "IMU ready to use". Neste momento, o script fará uma pausa aguardando que o usuário pressione Enter. Ainda não pressione!

#### Passo 3: Posicionamento das IMUs no Sujeito e Gravação
1. Fixação: Com o script pausado, pegue os IMUs da mesa e posicione-os firmemente nos segmentos corporais do sujeito. Não há orientação específica necessária

2. Pose de Referência: O sujeito deve se posicionar na mesma postura do modelo utilizado no OpenSim (geralmente uma pose estática com os braços relaxados).

3. Alinhamento do Corpo: É crucial que o sujeito esteja virado exatamente para a mesma direção em que os LEDs dos IMUs estavam apontando na mesa durante o Passo 2.
    * *Nota:* Este passo é desnecessário caso haja um imu no torso ou pelvis que sirva como heading direction.

4. Iniciar Gravação: Com o sujeito posicionado e imóvel, pressione a tecla Enter no terminal para iniciar de fato a gravação do arquivo.

5. Realize o protocolo de movimentos desejado.

6. Finalizar: Para encerrar a coleta, clique na janela do terminal e pressione Ctrl + C. O script irá parar o streaming, salvar o .json e gerar automaticamente o arquivo .sto processado.


#### Arquivos de Saída

Para cada coleta, serão gerados três arquivos na pasta configurada:

1. **`nome_arquivo.json`**:
   * Contém os dados brutos (Timestamp e Quaternions).
   * Útil para backup ou reprocessamento futuro.

2. **`nome_arquivo_pos.sto`**:
   * Arquivo de posicionamento do OpenSim.
   * Contém cabeçalho do OpenSim, dados filtrados (Butterworth Lowpass) e reamostrados.
   * **Este é o arquivo que você deve carregar na ferramenta "IMU Placer" do OpenSim.**

3. **`nome_arquivo_mov.sto`**:
   * Arquivo final processado.
   * Contém cabeçalho do OpenSim, dados filtrados (Butterworth Lowpass) e reamostrados.
   * **Este é o arquivo que você deve carregar na ferramenta "IMU Inverse Kinematics" do OpenSim.**