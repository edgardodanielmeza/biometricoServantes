# Sistema de Gestión de Asistencia Biométrica - Colegio Cervantes

## Descripción General

Este es un sistema de escritorio diseñado para gestionar la asistencia de los empleados de una institución educativa. La aplicación se conecta a una base de datos SQLite existente (`ZKTimeNet.db`) para extraer los datos de marcaciones y generar una variedad de reportes detallados.

La aplicación está construida en Python utilizando la librería **Tkinter** para la interfaz gráfica.

## Características Principales

- **Autenticación Segura:** Inicio de sesión con usuario/contraseña y bloqueo de cuenta tras múltiples intentos fallidos.
- **Generación de Reportes Detallados:** Múltiples formatos de reporte para analizar la asistencia desde diferentes perspectivas.
- **Visualización y Exportación:** Previsualización de reportes en PDF directamente en la aplicación, con opciones para guardar en PDF, exportar a Excel e imprimir.
- **Lógica de Negocio Personalizada:** El sistema tiene en cuenta:
    - **Horarios Individuales:** Compara las marcaciones con el horario específico de cada empleado para cada día.
    - **Días Feriados:** Consulta una tabla de feriados para no marcarlos como ausencias.
    - **Excepciones (Vacaciones, etc.):** Consulta una tabla de excepciones para marcar correctamente los días de vacaciones, licencias, etc.
    - **Días Libres:** Identifica los días en que un empleado no tiene un horario asignado.

---

## Tipos de Reportes

1.  **Reporte de Asistencia (Individual):**
    *   Muestra un análisis detallado de la asistencia de un solo empleado en un rango de fechas.
    *   Columnas: `Fecha`, `Día`, `Horario`, `Entrada`, `Salida`, `Horas`, `Estado`.
    *   Incluye un resumen de incidencias (faltas, tardanzas, etc.) en el encabezado.

2.  **Reporte Mensual (Múltiples Empleados):**
    *   Permite seleccionar varios empleados y un mes/año.
    *   Genera un documento con una sección por cada empleado, con el mismo formato detallado que el reporte individual.

3.  **Registro de Marcaciones (Bruto):**
    *   Muestra una lista simple de todas las horas de marcación de un empleado en un rango de fechas, sin procesar.

4.  **Reporte de Incidencias Diario:**
    *   Para una fecha seleccionada, muestra una lista de todos los empleados que tuvieron alguna incidencia (Falta, Tardanza, Salida Temprana).

5.  **Resumen Diario General:**
    *   Para una fecha seleccionada, muestra una lista de **todos** los empleados y su estado de asistencia para ese día.

---

## Instalación y Ejecución

### 1. Prerrequisitos
-   Tener Python 3 instalado.
-   Acceso a la base de datos `ZKTimeNet.db`.

### 2. Configuración del Proyecto

**a) Clonar el Repositorio (si aplica):**
```bash
git clone <url-del-repositorio>
cd <nombre-del-directorio>
```

**b) (Recomendado) Crear un Entorno Virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

**c) Instalar Dependencias:**
Todas las librerías necesarias están listadas en el archivo `requirements.txt`. Para instalarlas, ejecuta:
```bash
pip install -r requirements.txt
```

### 3. Configurar la Base de Datos
Asegúrate de que la ruta a tu base de datos sea la correcta. La ruta se configura en el archivo: `src/gui/report_common.py` en la variable `DB_PATH`.

```python
# src/gui/report_common.py
DB_PATH = r'C:\Ruta\A\Tu\Base\De\Datos\ZKTimeNet.db'
```

### 4. Ejecutar la Aplicación
Una vez instaladas las dependencias, puedes ejecutar la aplicación con el siguiente comando:
```bash
python main.py
```
