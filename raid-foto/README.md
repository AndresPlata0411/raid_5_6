# RAID Lab: recuperar una imagen con RAID 5 y RAID 6

Proyecto final de Teoría de Códigos (MAT 4215), Universidad del Norte. Tema 3.

**Integrantes:** completar nombres del grupo.

## Ejecutar el aplicativo

Requiere Python 3.9 o superior.

```bash
pip install -r requirements.txt
python demo.py
```

Se abrirá una página local en el navegador. Carga una imagen, selecciona entre cero y tres discos caídos y ejecuta la simulación. Todo el procesamiento ocurre en el mismo equipo. Para cerrar, detén el proceso con `Ctrl+C` en la terminal. No abras `web/index.html` con Live Server: la interfaz necesita la API de Python (`/api/analyze`), que Live Server no proporciona.

## Qué demuestra

El aplicativo codifica los bytes RGB en cuatro discos de datos y agrega paridad. Presenta la imagen original, la lectura degradada sin reconstrucción y el resultado de recuperación. Se puede comparar RAID 5 y RAID 6 en el diagrama de discos.

| Nivel | Discos totales | Paridades | Máximo de discos caídos | Capacidad útil | Conjuntos recuperables, contando el arreglo intacto |
|---|---:|---:|---:|---:|---:|
| RAID 5 | 5 | 1 | 1 | 80 % | 6 de 32 |
| RAID 6 | 6 | 2 | 2 | 66,7 % | 22 de 64 |

La probabilidad teórica de pérdida supone fallas independientes con una misma probabilidad por disco. El valor por defecto de la tabla es 2 % por disco. La gráfica compara RAID 5 y RAID 6 entre 0 % y 20 %; también se presenta una estimación Monte Carlo de 20.000 arreglos.

## Fundamento

En RAID 5, la paridad es `P = D0 XOR D1 XOR D2 XOR D3`. Si desaparece un disco de datos, su bloque se recupera con la paridad y los bloques sobrevivientes. RAID 6 agrega `Q = D0 + g·D1 + g²·D2 + g³·D3` sobre GF(2⁸), con polinomio `0x11D` y `g = 2`. Las dos ecuaciones permiten reconstruir cualquier par de discos caídos. La posición de las fallas es conocida: son borrados, no errores de ubicación desconocida.

La distancia mínima es `d = 2` para RAID 5 y `d = 3` para RAID 6; por tanto, recuperan respectivamente uno y dos borrados. Con cuatro discos de datos, RAID 5 pierde una quinta parte de la capacidad total para paridad y RAID 6 pierde dos sextas partes.

## Código y pruebas

| Archivo | Función |
|---|---|
| `gf.py`, `raid.py` | Aritmética GF(2⁸), paridades y reconstrucción RAID 5/6 |
| `disks.py` | Repartir y reunir franjas, simular discos caídos y lectura degradada |
| `imageio_raid.py` | Conversión de imágenes RGB y bytes PNG |
| `demo.py`, `web/index.html` | Servidor local y experiencia interactiva |
| `metrics.py` | Capacidad, conjuntos de fallas, probabilidad teórica y simulada |
| `tests_core.py`, `tests.py` | Pruebas del núcleo, métricas y demo de imagen |

Ejecuta las pruebas con:

```bash
python tests_core.py
python tests.py
```

## Herramientas y fuentes

Se usó OpenAI Codex como apoyo para implementar la capa de imagen, la demostración web, las métricas y pruebas, además de mejorar el README. El grupo debe revisar y comprender todo el código, en especial `gf.py` y `raid.py`, que implementan el núcleo del código corrector. Se usan NumPy para operar sobre bytes e Pillow para procesar imágenes. La interfaz web usa HTML, CSS y JavaScript estándar; el servidor HTTP usa la biblioteca estándar de Python.

- H. P. Anvin, [The mathematics of RAID-6](https://www.kernel.org/pub/linux/kernel/people/hpa/raid6.pdf).
- Documentación oficial de [NumPy](https://numpy.org/doc/) y [Pillow](https://pillow.readthedocs.io/).
