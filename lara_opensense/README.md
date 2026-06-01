## LARA Opensense

Esta pasta contém o projeto LARA Opensense completo com todas as funções que são utilizadas para captura de dados de IMU, processamento dos dados e implementação do pipeline do Opensense em código.

Os scripts são os seguintes:
1. ```serial_operations.py```: Lista de funções mais básicas de comunicação serial com o Dongle e com as IMUs.
2. ```imu_class.py```: Classe que define um sistema de IMUs com funções de alto nível para configuração das IMUs e leitura de dados enviados por streaming.
3. ```imu_capture.py```: Funções de alto nível para instanciar a classe IMU (```imu_class.py```) e realizar uma captura de dados, salvando os dados em ```.json``` e ```.sto``` (para utilização no OpenSim).
4. ```file_operations.py```: Lista de funções de tratamento de dados para gerar o ```.json``` e o ```.sto```.
5. ```data_filters.py```: Funções para filtragem de dados.
6. ```euler_angle_operations.py```: Funções para trabalhar com ângulos de euler.
7. ```quaternion_operations.py```: Funções para trabalhar com quaternions.
8. ```opensense_pipeline.py```: Funções para implementação em código do pipeline de processamento de dados de IMU no Opensense.
9. ```imu_simulator.py```: Funções para leitura e processamento de dados de IMUs em ```.json``` e visualização do movimento com uma animação dos segmentos e do trajeto percorrido.
10. ```segment.py```: Classe que define um segmento do corpo com IMU e realiza o processamento dos dados daquela IMU e calcula o movimento na referência global e os ângulos relativos a um segmento proximal (ex.: um segmento da tíbia calcula os ângulos referentes ao femur, representando o ângulo do joelho).