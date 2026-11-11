# Regla Bolsa — fuentes adicionales (11/11/2026)

Alcance: todos los estudios, laboratorios, estrategias, validadores, scanners y paneles bursátiles de este repositorio, cuando corresponda al instrumento y a la variable analizada. Excluir por completo repositorios cuyo nombre termine en SoloG/solog.

## Fuentes incorporadas
- **Datos912**: fuente adicional candidata de datos de mercado argentino. Antes de consumirla automáticamente, identificar URL oficial, condiciones de acceso, cobertura, formato, periodicidad y licencias; no asumir una API pública ni datos disponibles.
- **BYMA Data**: fuente adicional de información del mercado BYMA. Verificar el producto/end-point autorizado, cobertura, frecuencia, licencia y acceso antes de integrar. Distinguir datos oficiales de cotización, históricos, puntas y operaciones; no asumir que todos son gratuitos o en tiempo real.

## Política de selección y contraste
1. Mantener Yahoo Finance como fuente primaria de cierres históricos diarios *cuando sus registros sean válidos*; IOL como contraste o respaldo validado, y como consulta intradiaria. Datos912 y BYMA Data son nuevas fuentes complementarias y candidatas para contraste o sustitución puntual ante datos inválidos/faltantes, sujetas a verificación de cobertura y acceso.
2. Priorizar fuentes directas de BYMA para información específica de negociación local cuando el dato concreto esté disponible y validado. No confundir subyacentes extranjeros con CEDEAR argentinos; ajustar ratio, CCL, moneda, horario y eventos corporativos.
3. Registrar por observación fuente, fecha/hora y zona horaria, símbolo, mercado, moneda, ajuste, latencia y evidencia de origen. Conservar datos crudos y discrepancias; no sobrescribir silenciosamente.
4. Validar OHLC, duplicados, calendario, precios y volúmenes, unidades, ajustes y consistencia entre fuentes. Si ninguna pasa, marcar insuficiente; no inventar ni arrastrar datos.
5. Para operaciones y costos efectivos, manda el comprobante real de Bull Market; no reemplazarlo por cotizaciones de fuentes externas. Mantener las reglas de costos reales vigentes.
6. **Estado de implementación**: incorporación documental de fuentes; no significa conexión API, descarga ni validación de disponibilidad. Todo conector debe probarse y registrar sus resultados antes de anunciarse operativo.

Esta política es complementaria a las reglas Bolsa existentes y no las reemplaza.
