#!/bin/bash
# Script para configurar secrets de Clerk en Cloud Run
# Uso: ./set-cloudrun-secrets.sh <SERVICE_NAME> <REGION>
#
# Required env vars:
#   CLERK_SECRET_KEY
#   CLERK_PUBLISHABLE_KEY
#   CLERK_PEM_PUBLIC_KEY

set -e

SERVICE_NAME=${1:-"guardia-backend"}
REGION=${2:-"us-central1"}

# Validate required env vars
for var in CLERK_SECRET_KEY CLERK_PUBLISHABLE_KEY CLERK_PEM_PUBLIC_KEY; do
  if [ -z "${!var}" ]; then
    echo "ERROR: $var is not set. Export it before running this script."
    exit 1
  fi
done

echo "Configurando secrets para Cloud Run service: $SERVICE_NAME en region $REGION"

echo "Metodo 1: Usando Secret Manager (Recomendado)"
echo "================================================"
echo ""
echo "1. Crear secrets en Secret Manager:"
echo ""
echo "gcloud secrets create clerk-secret-key --data-file=- <<EOF"
echo "\$CLERK_SECRET_KEY"
echo "EOF"
echo ""
echo "gcloud secrets create clerk-publishable-key --data-file=- <<EOF"
echo "\$CLERK_PUBLISHABLE_KEY"
echo "EOF"
echo ""
echo "gcloud secrets create clerk-pem-public-key --data-file=- <<EOF"
echo "\$CLERK_PEM_PUBLIC_KEY"
echo "EOF"
echo ""
echo "2. Dar permisos a Cloud Run para acceder a los secrets:"
echo ""
echo "gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\"
echo "  --member=\"serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com\" \\"
echo "  --role=\"roles/secretmanager.secretAccessor\""
echo ""
echo "3. Actualizar Cloud Run service para usar los secrets:"
echo ""
echo "gcloud run services update $SERVICE_NAME \\"
echo "  --region=$REGION \\"
echo "  --update-secrets=CLERK_SECRET_KEY=clerk-secret-key:latest,CLERK_PUBLISHABLE_KEY=clerk-publishable-key:latest,CLERK_PEM_PUBLIC_KEY=clerk-pem-public-key:latest"
echo ""
echo ""
echo "Metodo 2: Usando variables de entorno directamente (Mas simple)"
echo "================================================================"
echo ""
echo "gcloud run services update $SERVICE_NAME \\"
echo "  --region=$REGION \\"
echo "  --set-env-vars=\"CLERK_SECRET_KEY=\$CLERK_SECRET_KEY\" \\"
echo "  --set-env-vars=\"CLERK_PUBLISHABLE_KEY=\$CLERK_PUBLISHABLE_KEY\" \\"
echo "  --set-env-vars=\"CLERK_PEM_PUBLIC_KEY=\$CLERK_PEM_PUBLIC_KEY\""
echo ""
echo "IMPORTANTE: El metodo 2 expone los secrets en la configuracion del servicio."
echo "El metodo 1 (Secret Manager) es mas seguro para produccion."
