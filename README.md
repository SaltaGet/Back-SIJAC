# API Convivir

API para Convivir.

## Requisitos

- Python 3.12 o superior
- pip (gestor de paquetes de Python)
- SQLITE

### Crear .env
    Crear un archivo ".env" con los siguientes campos:
    ```sh
    DB_NAME = 'convivir'  "dejar por defecto este nombre"
    DB_HOST = 'host de la db'
    DB_USER = 'usuario de la base de datos'
    DB_PASSWORD = 'password de la base de datos'
    DB_PORT = 'puerto'

    SECRET_KEY = 'Tu Secret Key'

    SMTP_SERVER = 'direccion smtp'
    EMAIL_PORT = puerto 
    EMAIL = 'your_mail'
    EMAIL_PASSWORD = 'password'
    ```

## Instalación

### Linux

1. Clona el repositorio:

    ```sh
    git clone https://github.com/SaltaGet/Back-Georgina.git
    cd Back-Georgina
    ```

2. Crea y activa un entorno virtual:

    ```sh
    python3 -m venv env
    source env/bin/activate
    ```

3. Instala las dependencias:

    ```sh
    pip install -r requirements.txt
    ```

### Windows

1. Clona el repositorio:

    ```sh
    git clone https://github.com/SaltaGet/Back-Georgina.git
    cd Back-Georgina
    ```

2. Crea y activa un entorno virtual:

    ```sh
    python -m venv env
    .\env\Scripts\activate
    ```

3. Instala las dependencias:

    ```sh
    pip install -r requirements.txt
    ```

## Ejecución

Para iniciar la aplicación, ejecuta el siguiente comando:

### Linux

```sh
python3 main.py
```

### Windows

```sh
python main.py
```

## Acceder a Swagger

Una vez iniciada la aplicación dirigirse a para ver la documentacion:

Documentacion Swagger
```sh
http://127.0.0.1:8000
```

Documentación Redoc 
```sh
http://127.0.0.1:8000/redoc
```