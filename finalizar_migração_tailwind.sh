#!/bin/bash

# Script para finalizar a migração Bootstrap → Tailwind CSS (11% restante)

echo "🚀 FINALIZANDO MIGRAÇÃO BOOTSTRAP → TAILWIND CSS"
echo "================================================"

# Função para migrar badges
migrate_badges() {
    echo "🎫 Migrando badges..."
    
    # Migrar badges bg-* para mm-badge-*
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-primary/mm-badge mm-badge-primary/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-secondary/mm-badge mm-badge-secondary/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-success/mm-badge mm-badge-success/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-danger/mm-badge mm-badge-danger/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-warning/mm-badge mm-badge-warning/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-info/mm-badge mm-badge-info/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-light text-dark/mm-badge mm-badge-secondary/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/badge bg-light/mm-badge mm-badge-secondary/g' {} \;
}

# Função para migrar alerts
migrate_alerts() {
    echo "🚨 Migrando alerts..."
    
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-primary/mm-alert mm-alert-primary/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-secondary/mm-alert mm-alert-secondary/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-success/mm-alert mm-alert-success/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-danger/mm-alert mm-alert-danger/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-warning/mm-alert mm-alert-warning/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-info/mm-alert mm-alert-info/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/alert alert-dismissible/mm-alert mm-alert-dismissible/g' {} \;
}

# Função para migrar layout classes
migrate_layout() {
    echo "📐 Migrando classes de layout..."
    
    # Flexbox
    find templates/ -name "*.html" -type f -exec sed -i '' 's/d-flex/flex/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/justify-content-center/justify-center/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/justify-content-between/justify-between/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/justify-content-end/justify-end/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/justify-content-start/justify-start/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/align-items-center/items-center/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/align-items-start/items-start/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/align-items-end/items-end/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/flex-grow-1/flex-grow/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/flex-wrap/flex-wrap/g' {} \;
}

# Função para migrar spacing classes
migrate_spacing() {
    echo "📏 Migrando classes de espaçamento..."
    
    # Margins
    find templates/ -name "*.html" -type f -exec sed -i '' 's/me-1/mr-1/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/me-2/mr-2/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/me-3/mr-3/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/me-4/mr-4/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/ms-1/ml-1/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/ms-2/ml-2/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/ms-3/ml-3/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/ms-4/ml-4/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mb-1/mb-1/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mb-2/mb-2/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mb-3/mb-3/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mb-4/mb-4/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mt-1/mt-1/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mt-2/mt-2/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mt-3/mt-3/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/mt-4/mt-4/g' {} \;
}

# Função para migrar text classes
migrate_text() {
    echo "📝 Migrando classes de texto..."
    
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-muted/text-gray-600/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-primary/text-purple-move/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-secondary/text-gray-600/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-success/text-green-600/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-danger/text-red-600/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-warning/text-yellow-600/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-info/text-blue-600/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-dark/text-gray-900/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/text-light/text-gray-100/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/fw-bold/font-bold/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/small/text-sm/g' {} \;
}

# Função para migrar outros elementos
migrate_misc() {
    echo "🔧 Migrando elementos diversos..."
    
    # Rounded
    find templates/ -name "*.html" -type f -exec sed -i '' 's/rounded-circle/rounded-full/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/rounded/rounded/g' {} \;
    
    # Border
    find templates/ -name "*.html" -type f -exec sed -i '' 's/border-b/border-b/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/border-t/border-t/g' {} \;
    
    # Display
    find templates/ -name "*.html" -type f -exec sed -i '' 's/d-none/hidden/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/d-block/block/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/d-inline/inline/g' {} \;
    find templates/ -name "*.html" -type f -exec sed -i '' 's/d-grid/grid/g' {} \;
}

# Executar migrações
migrate_badges
migrate_alerts
migrate_layout
migrate_spacing
migrate_text
migrate_misc

echo ""
echo "✅ MIGRAÇÃO CONCLUÍDA!"
echo "======================="

# Verificar resultado
BOOTSTRAP_REMAINING=$(grep -r "btn btn-\|badge bg-\|alert alert-\|d-flex\|justify-content-\|align-items-" templates/ --include="*.html" | wc -l)
TAILWIND_COUNT=$(grep -r "mm-btn\|mm-badge\|mm-alert\|flex\|justify-\|items-" templates/ --include="*.html" | wc -l)

echo "📈 ESTATÍSTICAS FINAIS:"
echo "   - Referências Bootstrap restantes: $BOOTSTRAP_REMAINING"
echo "   - Componentes Tailwind: $TAILWIND_COUNT"

if [ $BOOTSTRAP_REMAINING -eq 0 ]; then
    echo "🎉 MIGRAÇÃO 100% CONCLUÍDA!"
else
    echo "⚠️  Ainda há $BOOTSTRAP_REMAINING referências Bootstrap para revisar"
fi

echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "   1. Testar todas as funcionalidades"
echo "   2. Verificar responsividade"
echo "   3. Validar acessibilidade"
echo "   4. Fazer deploy em produção"
