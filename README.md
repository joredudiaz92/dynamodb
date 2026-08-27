# DynamoDB Local & Performance Testing Environment

Este repositorio proporciona un entorno unificado y preconfigurado para el desarrollo, migración y pruebas de rendimiento con **Amazon DynamoDB** de forma local.

## 🛠️ Estructura del Proyecto

* **`docker/dynamodb`**: Configuración e imágenes para ejecutar la base de datos localmente.
* **`migrations/`**: Scripts para la creación de tablas, esquemas e índices iniciales.
* **`k6/`**: Scripts de pruebas de carga y rendimiento para evaluar el comportamiento de la base de datos.
* **`logs/`**: Registro de operaciones y diagnóstico del entorno.
* **`docker-compose.yml`**: Orquestación de los contenedores de DynamoDB y herramientas asociadas.

## 🚀 Requisitos Previos

Asegúrate de tener instalado:
* Docker
* Docker Compose
* Python 3.x (opcional, para scripts auxiliares)

## 💻 Inicio Rápido

1. **Levantar el entorno local:**
   ```bash
   docker-compose up -d
   ```
2. **Ejecutar migraciones:**
   Aplica los esquemas iniciales ejecutando los scripts dentro de la carpeta `migrations/`.
