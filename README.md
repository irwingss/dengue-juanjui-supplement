# Dengue e indicadores entomológicos en Juanjuí

Material suplementario de la versión v5 del estudio *Asociación entre los casos de dengue e indicadores entomológicos de Aedes aegypti en una ciudad de la Amazonía peruana*, de Kepler N. Andrade-Herrera, Alvaro E. Tresierra-Aguilar e Irwing S. Saldaña. El estudio analizó 770 notificaciones de sospecha de dengue de enero a junio de 2025. La población analítica comprendió 252 pacientes, con 124 resultados positivos y 128 negativos por laboratorio.

## Contenido

| Carpeta | Archivos |
| --- | --- |
| [Tablas](Tablas) | Tablas 1–3 y S1–S2 en CSV, transcritas de la versión v5 en [español](Tablas/ES) e [inglés](Tablas/EN). También incluye seis archivos CSV del análisis en R. |
| [Figuras](Figuras) | Figuras 2–4 de la versión v5 en PNG y PDF, en [español](Figuras/ES) e [inglés](Figuras/EN). La Figura 1 es una versión vectorial de los mismos cinco sectores. La Figura S1 muestra la distribución agregada del intervalo en las 254 viviendas inspeccionadas. |
| [Datos](Datos) | Conteos agregados para el flujograma, la relación entre infestación y resultado de laboratorio y el intervalo de inspección. Incluye los polígonos de los sectores del estudio y el [diccionario de variables](Datos/diccionario_variables.csv) de la base analítica. |
| [Codigos](Codigos) | Preparación de datos, modelos en R y generación de figuras en Python. |

Las Figuras 2–4 corresponden a los archivos del paquete de envío. El mapa público usa los polígonos del estudio y prescinde de la imagen satelital de la Figura 1. La Figura S1 pública conserva el total de 254 viviendas inspeccionadas y el 99,2 % dentro de siete días. El intervalo mediano fue de 2 días (RIC 0–4). Para difusión pública, la figura agrupa los intervalos de 5 a 7 días, reúne los superiores a siete días en un total sin desglose por resultado y omite el panel de fechas exactas.

## Disponibilidad de datos y código

El repositorio contiene el código de análisis, resultados agregados y los insumos públicos de las figuras. Los registros individuales de vigilancia contienen información clínica, fechas y localización de las visitas. La autorización documentada en la versión v5 se refiere al acceso para la investigación. Las solicitudes de acceso a esos registros pueden dirigirse a los autores para su evaluación con la entidad custodiante, la Unidad de Gestión Territorial de Salud Mariscal Cáceres.

## Reproducción

Desde la raíz del repositorio, con Python 3.13 y Arial como fuente para las Figuras 2–4, los siguientes comandos generan las figuras en `Reproduccion/` con los insumos públicos. En otros sistemas la fuente de sustitución puede cambiar el aspecto del texto.

```bash
python -m pip install -r requirements.txt
python Codigos/29_mapa.py
python Codigos/33_figura_diseno.py es
python Codigos/33_figura_diseno.py en
python Codigos/32_figuras.py es
python Codigos/32_figuras.py en
```

Con acceso autorizado, indicar las rutas locales de los insumos. El primer paso usa el libro original con las hojas `FORMATO 10 - INVESTIGACIÓN` y `LOGISTICO`. Si ya se dispone de la base analítica autorizada, se puede empezar con el comando de R. El ajuste de los modelos usa R 4.6.1, `sandwich` 3.1-3, `lmtest` 0.9-40 y `zoo` 1.9-1.

```bash
python Codigos/30_base_770.py "/ruta/al/libro-autorizado.xlsx" Reproduccion/base_770.csv
Rscript --vanilla Codigos/31_analisis.R Reproduccion/base_770.csv Reproduccion/Tablas
python Codigos/28_datos_figuras.py Reproduccion/base_770.csv Reproduccion/Datos
```

Los CSV de `Reproduccion/Tablas` se comparan con los seis CSV en `Tablas/`. La Tabla 1 describe el diseño y se transcribió de la versión enviada. Las tablas con formato editorial se incluyen como CSV para consulta.

## English

Supplementary materials for v5 of *Association between dengue cases and entomological indicators of Aedes aegypti in a city in the Peruvian Amazon*. The repository includes the analysis code, aggregated data, Figures 1–4 and S1, and Tables 1–3 and S1–S2. The public Figure 1 shows the same study sector boundaries as the submitted map. The public Figure S1 shows grouped intervals for the 254 inspected households. Individual surveillance records contain clinical information, visit dates and locations. Access requests may be directed to the authors for review with the data custodian, the Mariscal Cáceres Territorial Health Management Unit.
