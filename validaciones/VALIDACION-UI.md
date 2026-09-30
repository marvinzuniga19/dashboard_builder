# Validación del rediseño de UI

Fecha: 2026-09-30.

## Alcance

Barra lateral y navegación móvil, breadcrumb, tarjetas, login y estado del sistema. El dashboard separa lectura de edición, con formularios bajo demanda. Se mantiene el guardado del layout al finalizar cada interacción y los gráficos de demostración de FASE 6.

Dependencia añadida: `lucide-react`, mediante imports de iconos individuales. No hay cambios de backend, endpoints ni migraciones.

## Comprobaciones ejecutadas

- `npm run lint`: correcto.
- `npm run typecheck`: correcto.
- `npm run build`: compilación de producción correcta.
- `npm run test:e2e`: 5 pruebas correctas en Chromium.
- Revisión de capturas de escritorio y móvil.

Las pruebas de navegador cubren gráficos, resize del canvas, arrastre y redimensionado, persistencia y recarga, eliminación de widgets, separación lectura/edición, alta de widgets, cambio de nombre, errores de creación y menú móvil. Se comprueba la ausencia de desbordamiento horizontal a 1440, 1024, 768, 390 y 320 px. Una regresión verifica que añadir widgets no genera errores de renderizado en la consola.

En este entorno se usó `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` con el Chromium disponible. Los endpoints de estas pruebas están simulados: no equivalen a una validación integral con FastAPI real. El backend no se modificó ni se volvió a probar en esta tarea.

## Cómo probar con la API real

1. Iniciar backend y frontend siguiendo el README e iniciar sesión.
2. Crear o abrir un dashboard: debe aparecer la vista de lectura.
3. Pulsar Añadir widget, elegir tipo y crear; comprobar que el formulario se cierra y aparece la tarjeta.
4. En edición, arrastrar y redimensionar; recargar para verificar el layout.
5. Cambiar el nombre en Propiedades del dashboard y terminar edición.
6. En móvil, abrir/cerrar navegación y comprobar las tarjetas a ancho completo en lectura.

## Límites

Los gráficos conservan datos de demostración; KPI y tabla conservan sus estados provisionales. Las fuentes de datos y consultas siguen pendientes. El apilado móvil se aplica solo a la lectura y no cambia las coordenadas persistidas del lienzo.
