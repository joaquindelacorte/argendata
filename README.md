# Argentina Macro Dashboard

Dashboard interactivo para visualizar y monitorear los principales indicadores macroeconómicos, comerciales y logísticos de Argentina. Construido con Vanilla JavaScript, HTML5 y CSS3, integra gráficos dinámicos y conexiones interactivas con distintas APIs gubernamentales y privadas.

## 🚀 Características Principales

1. **Finanzas y Variables BCRA (`finanzas.html`)**
   - Evolución de las Reservas Internacionales, Base Monetaria, Circulación y Créditos.
   - Explorador estadístico en tiempo real interactuando con la **API v4.0 del BCRA**.
   - Cotizaciones del Dólar (Oficial, Blue, CCL).
   - Variables macro críticas: Riesgo País e Inflación Mensual.

2. **Comercio Exterior (`comex.html`)**
   - Resumen mensual de Exportaciones e Importaciones.
   - Visualización de la Balanza Comercial.

3. **Agro y Mercados Físicos (`mercados.html`)**
   - Volumen de Declaraciones Juradas de Ventas al Exterior (DJVE) para Trigo y Maíz.
   - Precios FOB de productos agropecuarios.
   - Cotizaciones promedio en distintos puertos argentinos.

4. **Logística y Puertos (`index.html`, `puertos4.html`)**
   - Monitor de arribos de camiones a puertos.
   - Mapas y dashboards del complejo agro-exportador.

## 📱 Diseño Responsivo (Mobile First)

Toda la aplicación está estilizada a partir del motor de `estilos_compartidos.css`. Recientemente se implementó **soporte completo para dispositivos móviles**:
- Menú lateral convertido en *off-canvas* navegable.
- Cuadrículas (Grids) dinámicas que apilan tarjetas según el espacio.
- Tamaños de letra y *paddings* flexibles adaptados a pantallas reducidas.
- Se ha logrado el concepto de interfaz de clase mundial usando *glassmorphism* y gradientes atractivos.

## ⚙️ Tecnologías y Librerías

- **Frontend Core:** HTML5, CSS3, Vanilla JavaScript.
- **Gráficos:** [Chart.js](https://www.chartjs.org/) para reportes en tiempo real.
- **Procesamiento de Datos:** [PapaParse](https://www.papaparse.com/) para leer y formatear archivos CSV remotos en las secciones de Agro y Comex.
- **Fuentes:** Google Fonts (Inter y Outfit).

## 📡 Fuentes de Datos (APIs)

Ver los detalles técnicos en `links_apis.md`. Entre ellas destacan:
- `api.bcra.gob.ar/estadisticas/v4.0`: Explorador de series monetarias e inflación.
- `api.argentinadatos.com`: Integrador con acceso a dólares múltiples y riesgo país consolidado.
- Fuentes varias provistas a través del sistema de datos del Estado de Argentina (BCRA, INDEC, SAGyP).

## 🌍 Uso y Ejecución

Al ser una arquitectura de archivos estáticos puros, su ejecución no requiere un servidor pesado:
1. Clonar el repositorio.
2. Abrir `dashboard.html` o iniciar un servidor web minúsculo como [Live Server] en VS Code.

---
*Desarrollado para mantener un pulso veloz y en vivo sobre la coyuntura económica argentina.*
