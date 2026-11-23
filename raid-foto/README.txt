PROYECTO FINAL - TEORIA DE CODIGOS - Universidad del Norte
=====================================================================
Tema: RAID 5 y RAID 6 (recuperar una imagen tras la caida de discos)

INTEGRANTES
  - Anndres Plata
  - Elkin Celis
  - Camilo Castro
  - Andres Garcia

INSTRUCCIONES PARA EJECUTAR (Python 3.9 o superior)
  pip install -r requirements.txt
  python demo.py        (abre una pagina local en el navegador)
  Cargar una imagen, elegir RAID 5 o 6, elegir 0 a 3 discos caidos, ejecutar.
  Pruebas: python tests_core.py   y   python tests.py
  Cerrar el servidor: Ctrl+C.

CODIGO USADO
  Por franja de 4 discos de datos, con simbolos en GF(2^8) (polinomio 0x11D, g=2):
  - RAID 5: P = D0+D1+D2+D3 (XOR).       Codigo (n,k)=(5,4), d=2.
  - RAID 6: P igual y Q = sum g^i*Di.    Codigo (n,k)=(6,4), d=3. Ambos son MDS.
  RAID 5 detecta 1 error, corrige 0 y recupera 1 borrado.
  RAID 6 detecta 2 errores, corrige 1 (posicion desconocida) y recupera 2 borrados.
  Capacidad perdida: 1/n (RAID 5) y 2/n (RAID 6): 20% y 33,3% con 4 discos de datos.

RESULTADOS PRINCIPALES (probabilidad de perder datos, fallas independientes)
  p por disco | 1 disco  | RAID 5   | RAID 6
  2%          | 2,000%   | 0,384%   | 0,015%
  10%         | 10,0%    | 8,15%    | 1,59%
  Con p=2%, RAID 5 reduce la perdida unas 5 veces y RAID 6 unas 25 veces mas que
  RAID 5, a cambio de mas capacidad perdida (20% a 33,3%). Con la imagen: RAID 5
  recupera 1 disco caido y falla con 2; RAID 6 recupera 2 y falla con 3.

ARCHIVOS
  gf.py, raid.py        Nucleo propio: aritmetica GF(2^8), paridades y recuperacion
  disks.py              Reparto en discos, discos caidos, lectura degradada
  imageio_raid.py       Conversion de imagenes
  metrics.py            Capacidad y probabilidades
  demo.py, web/         Servidor local y pagina interactiva
  tests_core.py, tests.py   Pruebas

HERRAMIENTAS UTILIZADAS (declaracion)
  - OpenAI Codex: implementacion de la capa de imagen, la demo web, las metricas,
    las pruebas y mejoras del README.
  - Librerias: NumPy y Pillow (auxiliares); HTML/CSS/JavaScript y http.server.
  El nucleo (gf.py, raid.py) fue revisado y es explicado por los 4 integrantes.

FUENTES
  - H. P. Anvin, "The mathematics of RAID-6", kernel.org.
  - D. Patterson, G. Gibson, R. Katz, "A Case for Redundant Arrays of Inexpensive
    Disks (RAID)", SIGMOD 1988.
  - Apuntes de Teoria de Codigos.
