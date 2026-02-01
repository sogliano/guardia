#!/bin/bash
# Script para configurar secrets de Clerk en Cloud Run
# Uso: ./set-cloudrun-secrets.sh <SERVICE_NAME> <REGION>

set -e

SERVICE_NAME=${1:-"guardia-backend"}
REGION=${2:-"us-central1"}

echo "Configurando secrets para Cloud Run service: $SERVICE_NAME en región $REGION"

# Clerk secrets
CLERK_SECRET_KEY="sk_test_7bqlW36YKQDjekg3RVzhbLfTD5qtX9w0CYJohDi1z4"
CLERK_PUBLISHABLE_KEY="pk_test_c2VjdXJlLXRlcnJhcGluLTUwLmNsZXJrLmFjY291bnRzLmRldiQ"
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwj9mewgohI72aKlaDhAa
u3RSuDr04FaVolZ+ujWf19NdSkTm/TSq8PNCIqiWhAFTI7pkdioobeBbaLzObajJ
r49qLZRq6+dpZtBtYLTPq/CPAjNqs+JTFe7KtL0pDx+kbbS5tvwC38/f0BzjU/5D
5XDRNBdLPl/AsB5CJ3dOY6rwiZupXggBbugnlchAA5FdmfRZ3ze1CCJzmtvL1sUO
UZIvrZQw5Wp27ZqXQNns5NJZZYP3xTFjDijxQ3uYnz3Vxl+nByVr5sH1kDt416UL
aB0pBNrFWdGwMNZG9JyQ07Q6CBaWO6jvij+iJ/mW4KT0cUXlfumd3CA7hL++GPTt
+wIDAQAB
-----END PUBLIC KEY-----"

echo "Método 1: Usando Secret Manager (Recomendado)"
echo "================================================"
echo ""
echo "1. Crear secrets en Secret Manager:"
echo ""
echo "gcloud secrets create clerk-secret-key --data-file=- <<EOF"
echo "$CLERK_SECRET_KEY"
echo "EOF"
echo ""
echo "gcloud secrets create clerk-publishable-key --data-file=- <<EOF"
echo "$CLERK_PUBLISHABLE_KEY"
echo "EOF"
echo ""
echo "gcloud secrets create clerk-pem-public-key --data-file=- <<EOF"
echo "$CLERK_PEM_PUBLIC_KEY"
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
echo "Método 2: Usando variables de entorno directamente (Más simple)"
echo "================================================================"
echo ""
echo "gcloud run services update $SERVICE_NAME \\"
echo "  --region=$REGION \\"
echo "  --set-env-vars=\"CLERK_SECRET_KEY=$CLERK_SECRET_KEY\" \\"
echo "  --set-env-vars=\"CLERK_PUBLISHABLE_KEY=$CLERK_PUBLISHABLE_KEY\" \\"
echo "  --set-env-vars=\"CLERK_PEM_PUBLIC_KEY=$CLERK_PEM_PUBLIC_KEY\""
echo ""
echo "IMPORTANTE: El método 2 expone los secrets en la configuración del servicio."
echo "El método 1 (Secret Manager) es más seguro para producción."
