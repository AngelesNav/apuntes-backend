# Proyecto de Apuntes en Línea

Este proyecto es una aplicación de apuntes en línea con un backend basado en Flask y un frontend basado en React.

## Requisitos

- Node.js (v14 o superior)
- Python (v3.11 o superior)
- Docker (opcional para construir imágenes)

## Backend

### Instalación

1. Clona el repositorio del backend:

    ```bash
    git clone https://github.com/tu-usuario/apuntes-backend.git
    cd apuntes-backend
    ```

2. Crea un entorno virtual:

    ```bash
    python -m venv venv
    ```

3. Activa el entorno virtual:

    - En Windows:

        ```bash
        .\venv\Scripts\activate
        ```

    - En macOS/Linux:

        ```bash
        source venv/bin/activate
        ```

4. Instala las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

5. Configura la base de datos:

    ```bash
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

### Ejecución

1. Ejecuta la aplicación:

    ```bash
    flask run
    ```

2. La aplicación estará disponible en `http://127.0.0.1:5000`.
