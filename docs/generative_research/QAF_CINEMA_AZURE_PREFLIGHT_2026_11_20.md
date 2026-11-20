# QAF Cinema — auditoría de Azure antes de entrenar
**Estado: inventario de solo lectura, no entrenamiento** · 20 de noviembre de 2026

## Problemas separados
1. **Acceso a Studio.** Un Private Endpoint requiere conectividad del cliente hacia la VNet y resolución DNS privada. La ausencia de una VM conectada a la subred no prueba por sí sola toda la causa del error en macOS. No abrir Studio a Internet como atajo.
2. **Entrenamiento.** La cuota Azure ML por familia GPU, la disponibilidad del tamaño concreto, la VRAM y la cuota general de VM son verificaciones diferentes. Un valor cero para la A100 conocido anteriormente no confirma las cuotas actuales de las otras familias.
3. **Patrocinio y presupuesto.** Los créditos Azure no prueban que una GPU esté habilitada para la oferta Sponsorship; tampoco confirman el costo final, que podría incluir red, Firewall, disco y almacenamiento.

## Ejecutar el preflight
En una sesión autenticada de Azure CLI (Cloud Shell si el directorio permite usarlo, o una máquina autorizada, sin necesidad de VS Code):

    az account show --query '{id:id,name:name,state:state}' -o table
    az extension show --name ml
    # Si hace falta, instalar localmente con: az extension add --name ml
    python scripts/qaf_cinema_azure_preflight.py \
      --subscription <ID_SUSCRIPCION> \
      --resource-group rg-qaf-cinema-training \
      --workspace aml-qaf-cinema-training \
      --region eastus2 \
      --vnet vnet-pe-eastus2 \
      --out qaf-cinema-azure-private-report.json

El informe es privado y no se debe adjuntar automáticamente a un PR público sin revisar los nombres y la topología que contiene. El script no instala extensiones ni altera la suscripción activa. Si la suscripción activa no coincide con la indicada, se detiene.

Ejecutar las pruebas sin acceder a Azure:

    python -m unittest tests.test_qaf_cinema_azure_preflight -v

## Criterios de decisión
- BLOCKED_*: no crear recursos ni iniciar entrenamiento.
- INCOMPLETE_*: falta autenticación, permisos o datos; no inferir que hay GPU.
- POSSIBLE_GPU_QUOTA_*: es necesario confirmar capacidad del SKU, VRAM suficiente, autorización de Sponsorship, costos, datos y permisos de modelo antes de entrenar. Tener cores libres no garantiza disponibilidad real.
- La auditoría solo describe redes y conexiones privadas; no prueba el DNS privado ni conectividad del Mac. Verificar los FQDN reales del Private Endpoint y las zonas DNS desde una ruta privada.
- Azure ML AllowOnlyApprovedOutbound puede necesitar reglas adicionales para acceder a paquetes y pesos. Las reglas FQDN pueden activar cargos de Azure Firewall. No modificar aislamiento antes de presupuestarlo.

## Plan tras el preflight
1. Asegurar ruta de acceso: VPN Point-to-Site con DNS privado o host de salto protegido y acceso remoto; comparar el costo total. Bastion y VPN no son gratuitos por definición.
2. Solicitar a Microsoft verificación escrita de elegibilidad GPU de la suscripción patrocinada. Confirmar cuota de Azure ML, SKU y capacidad de memoria en la región.
3. Auditar por FFprobe los 106 candidatos MP4 del inventario y revisar consentimiento, derechos, identidad y splits por actor/prenda. El inventario de archivos no implica autorización suficiente para entrenamiento generativo comercial.
4. Preparar dataset privado, modelo/LoRA con licencia apta para el uso comercial y límite de horas/costo. Usar el ejecutor existente gpu_training_runner.py en dry-run primero.
5. Entrenar una prueba pequeña de video de 5 segundos, inspeccionar el checkpoint y el MP4 real. Comparar calidad, consistencia temporal, movimiento, prendas y coste con el backbone sin adaptar y baselines equivalentes. Solicitar revisión humana previa a publicación.

## Referencias oficiales
- https://learn.microsoft.com/azure/machine-learning/how-to-troubleshoot-secure-connection-workspace
- https://learn.microsoft.com/azure/machine-learning/how-to-managed-network
- https://learn.microsoft.com/azure/machine-learning/how-to-manage-quotas
- https://learn.microsoft.com/cli/azure/ml/compute
- https://learn.microsoft.com/azure/virtual-machines/quotas
