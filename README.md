# Presupuesto Personal

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)

Aplicación web para gestionar presupuesto personal, inspirada en "Ultimate Personal Budget" de Excel. Permite registrar ingresos, gastos, transferencias, gestionar cuentas en PEN y USD, configurar tipo de cambio manual, y visualizar un dashboard con KPIs y gráficos interactivos.

## Características Principales

- **Registro de Transacciones**: Ingresos, gastos, transferencias y pagos de tarjeta con categorías detalladas.
- **Gestión de Cuentas**: Efectivo, débito (con colchón de seguridad), crédito (con límite y deuda).
- **Soporte Multimoneda**: PEN y USD con conversión automática basada en tipo de cambio.
- **Presupuestos**: Configuración por período con metas de ingresos, gastos y ahorros en porcentaje.
- **Dashboard Interactivo**: KPIs y gráficos utilizando ApexCharts para visualización de datos.
- **Transacciones Recurrentes**: Comando de management para generar transacciones automáticas.
- **Interfaz en Español**: Diseño moderno con Tabler UI para una experiencia de usuario intuitiva.

## Tecnologías Utilizadas

- **Backend**: Django 5.2, SQLite (base de datos ligera y fácil de usar).
- **Frontend**: HTML/JS vanilla, Tabler UI (CDN), ApexCharts (CDN) para gráficos dinámicos.

## Prerrequisitos

- Python 3.12+.
- Git para clonar el repositorio.
- Un navegador web moderno para acceder a la aplicación.

## Instalación

Sigue estos pasos para configurar el proyecto en tu máquina local:

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/m1guel17/budget-tracker-django
   cd budget-tracker-django
   ```

2. **Crea un entorno virtual**:
   ```bash
   python -m venv env
   ```

3. **Activa el entorno virtual**:
   - En Windows: `env\Scripts\activate`
   - En macOS/Linux: `source env/bin/activate`

4. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Ejecuta las migraciones de la base de datos**:
   ```bash
   python manage.py migrate
   ```

6. **Carga datos iniciales** (opcional, para pruebas):
   ```bash
   python manage.py seed
   ```

7. **Ejecuta el servidor de desarrollo**:
   ```bash
   python manage.py runserver
   ```

   Accede a la aplicación en `http://localhost:8000`.

## Uso

- **Dashboard**: Visualiza KPIs y gráficos en `http://localhost:8000`.
- **Navegación**: Explora secciones como Transacciones, Cuentas, Presupuestos y Tipo de Cambio.
- **Registro de Transacciones**: Agrega nuevas transacciones desde la página de Transacciones.
- **Transacciones Recurrentes**: Ejecuta `python manage.py generate_recurring` periódicamente para generar transacciones automáticas.

<!-- ## Capturas de Pantalla

*(Agrega capturas de pantalla aquí si es posible)* -->

## Notas Importantes

- **Usuario Único**: La aplicación está diseñada para un solo usuario sin sistema de autenticación.
- **Moneda Predeterminada**: PEN (Soles Peruanos).
- **Tipo de Cambio**: Configurado manualmente por fecha para mayor control.
- **Validaciones**: Modelos con validaciones integradas para asegurar la integridad de los datos.

## Tests

Ejecuta las pruebas básicas con:
```bash
python manage.py test
```

## Contribución

¡Las contribuciones son bienvenidas! Por favor, sigue estos pasos:

1. Haz un fork del proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y confirma (`git commit -am 'Agrega nueva funcionalidad'`).
4. Empuja a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

<!-- ## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles. -->

## Contacto

Si tienes preguntas o sugerencias, abre un issue en el repositorio.