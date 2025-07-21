#!/bin/bash

# Script para corrigir as últimas 16 referências Bootstrap

echo "🔧 CORRIGINDO ÚLTIMAS REFERÊNCIAS BOOTSTRAP"
echo "==========================================="

# Corrigir erros de digitação d-mflex
echo "📝 Corrigindo d-mflex para flex..."
find templates/ -name "*.html" -type f -exec sed -i '' 's/d-mflex/flex/g' {} \;

# Corrigir classes justify-content-md-*
echo "📝 Corrigindo justify-content-md-*..."
find templates/ -name "*.html" -type f -exec sed -i '' 's/justify-content-md-center/md:justify-center/g' {} \;
find templates/ -name "*.html" -type f -exec sed -i '' 's/justify-content-md-end/md:justify-end/g' {} \;

# Corrigir badges específicos que sobraram
echo "🎫 Corrigindo badges específicos..."
find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-{/mm-badge mm-badge-{/g' {} \;

# Corrigir alert específico
echo "🚨 Corrigindo alert específico..."
find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-\${type}/mm-alert mm-alert-\${type}/g' {} \;

# Corrigir fs-6 class
echo "📏 Corrigindo fs-6..."
find templates/ -name "*.html" -type f -exec sed -i '' 's/fs-6/text-base/g' {} \;

echo ""
echo "✅ CORREÇÕES CONCLUÍDAS!"

# Verificar resultado final
BOOTSTRAP_REMAINING=$(grep -r "btn btn-\|badge bg-\|alert alert-\|d-flex\|justify-content-\|align-items-" templates/ --include="*.html" | wc -l)

echo "📈 VERIFICAÇÃO FINAL:"
echo "   - Referências Bootstrap restantes: $BOOTSTRAP_REMAINING"

if [ $BOOTSTRAP_REMAINING -eq 0 ]; then
    echo "🎉 MIGRAÇÃO 100% CONCLUÍDA!"
else
    echo "⚠️  Restam $BOOTSTRAP_REMAINING referências para revisar manualmente"
fi
