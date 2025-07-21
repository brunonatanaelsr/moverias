#!/bin/bash

# Script para migração automatizada Bootstrap → Tailwind CSS
# Este script converte classes Bootstrap para Tailwind em todos os templates

echo "🔄 Iniciando migração Bootstrap → Tailwind CSS..."

# Função para substituir classes Bootstrap por Tailwind
migrate_bootstrap_classes() {
    local file="$1"
    echo "📝 Processando: $file"
    
    # Backup do arquivo original
    cp "$file" "$file.backup"
    
    # Substituições de botões
    sed -i '' 's/btn btn-primary/mm-btn mm-btn-primary/g' "$file"
    sed -i '' 's/btn btn-secondary/mm-btn mm-btn-secondary/g' "$file"
    sed -i '' 's/btn btn-success/mm-btn mm-btn-success/g' "$file"
    sed -i '' 's/btn btn-danger/mm-btn mm-btn-danger/g' "$file"
    sed -i '' 's/btn btn-warning/mm-btn mm-btn-warning/g' "$file"
    sed -i '' 's/btn btn-info/mm-btn mm-btn-info/g' "$file"
    sed -i '' 's/btn btn-light/mm-btn mm-btn-light/g' "$file"
    sed -i '' 's/btn btn-dark/mm-btn mm-btn-dark/g' "$file"
    
    # Substituições de botões outline
    sed -i '' 's/btn btn-outline-primary/mm-btn mm-btn-outline-primary/g' "$file"
    sed -i '' 's/btn btn-outline-secondary/mm-btn mm-btn-outline-secondary/g' "$file"
    sed -i '' 's/btn btn-outline-success/mm-btn mm-btn-outline-success/g' "$file"
    sed -i '' 's/btn btn-outline-danger/mm-btn mm-btn-outline-danger/g' "$file"
    sed -i '' 's/btn btn-outline-warning/mm-btn mm-btn-outline-warning/g' "$file"
    sed -i '' 's/btn btn-outline-info/mm-btn mm-btn-outline-info/g' "$file"
    sed -i '' 's/btn btn-outline-light/mm-btn mm-btn-outline-light/g' "$file"
    sed -i '' 's/btn btn-outline-dark/mm-btn mm-btn-outline-dark/g' "$file"
    
    # Substituições de tamanhos
    sed -i '' 's/btn-sm/mm-btn-sm/g' "$file"
    sed -i '' 's/btn-lg/mm-btn-lg/g' "$file"
    
    # Substituições de cards
    sed -i '' 's/card-body/mm-card-body/g' "$file"
    sed -i '' 's/card-header/mm-card-header/g' "$file"
    sed -i '' 's/card-footer/mm-card-footer/g' "$file"
    sed -i '' 's/card-title/mm-card-title/g' "$file"
    sed -i '' 's/card-text/mm-card-text/g' "$file"
    
    # Substituições de badges
    sed -i '' 's/badge bg-primary/mm-badge mm-badge-primary/g' "$file"
    sed -i '' 's/badge bg-secondary/mm-badge mm-badge-secondary/g' "$file"
    sed -i '' 's/badge bg-success/mm-badge mm-badge-success/g' "$file"
    sed -i '' 's/badge bg-danger/mm-badge mm-badge-danger/g' "$file"
    sed -i '' 's/badge bg-warning/mm-badge mm-badge-warning/g' "$file"
    sed -i '' 's/badge bg-info/mm-badge mm-badge-info/g' "$file"
    
    # Substituições de alerts
    sed -i '' 's/alert alert-primary/mm-alert mm-alert-primary/g' "$file"
    sed -i '' 's/alert alert-secondary/mm-alert mm-alert-secondary/g' "$file"
    sed -i '' 's/alert alert-success/mm-alert mm-alert-success/g' "$file"
    sed -i '' 's/alert alert-danger/mm-alert mm-alert-danger/g' "$file"
    sed -i '' 's/alert alert-warning/mm-alert mm-alert-warning/g' "$file"
    sed -i '' 's/alert alert-info/mm-alert mm-alert-info/g' "$file"
    
    # Substituições de layout Bootstrap → Tailwind
    sed -i '' 's/d-flex/flex/g' "$file"
    sed -i '' 's/justify-content-center/justify-center/g' "$file"
    sed -i '' 's/justify-content-between/justify-between/g' "$file"
    sed -i '' 's/justify-content-end/justify-end/g' "$file"
    sed -i '' 's/justify-content-start/justify-start/g' "$file"
    sed -i '' 's/align-items-center/items-center/g' "$file"
    sed -i '' 's/align-items-start/items-start/g' "$file"
    sed -i '' 's/align-items-end/items-end/g' "$file"
    
    # Substituições de espaçamento Bootstrap → Tailwind
    sed -i '' 's/me-1/mr-1/g' "$file"
    sed -i '' 's/me-2/mr-2/g' "$file"
    sed -i '' 's/me-3/mr-3/g' "$file"
    sed -i '' 's/ms-1/ml-1/g' "$file"
    sed -i '' 's/ms-2/ml-2/g' "$file"
    sed -i '' 's/ms-3/ml-3/g' "$file"
    
    # Substituições de texto Bootstrap → Tailwind
    sed -i '' 's/text-muted/text-gray-600/g' "$file"
    sed -i '' 's/text-primary/text-purple-move/g' "$file"
    sed -i '' 's/text-danger/text-red-600/g' "$file"
    sed -i '' 's/text-success/text-green-600/g' "$file"
    sed -i '' 's/text-warning/text-yellow-600/g' "$file"
    sed -i '' 's/text-info/text-blue-600/g' "$file"
    
    # Substituições de cores de fundo Bootstrap → Tailwind
    sed -i '' 's/bg-primary/bg-purple-move/g' "$file"
    sed -i '' 's/bg-secondary/bg-gray-600/g' "$file"
    sed -i '' 's/bg-success/bg-green-600/g' "$file"
    sed -i '' 's/bg-danger/bg-red-600/g' "$file"
    sed -i '' 's/bg-warning/bg-yellow-500/g' "$file"
    sed -i '' 's/bg-info/bg-blue-600/g' "$file"
    
    echo "✅ Concluído: $file"
}

# Encontrar todos os templates HTML
echo "🔍 Buscando templates com classes Bootstrap..."

# Migrar templates por módulo
MODULES=("communication" "hr" "certificates" "chat" "core" "projects")

for module in "${MODULES[@]}"; do
    if [ -d "templates/$module" ]; then
        echo "📁 Processando módulo: $module"
        find "templates/$module" -name "*.html" -type f | while read -r file; do
            # Verificar se o arquivo contém classes Bootstrap
            if grep -q "btn btn-\|card-\|badge bg-\|alert alert-" "$file"; then
                migrate_bootstrap_classes "$file"
            fi
        done
    fi
done

# Processar templates na raiz
echo "📁 Processando templates na raiz..."
find templates/ -maxdepth 1 -name "*.html" -type f | while read -r file; do
    if grep -q "btn btn-\|card-\|badge bg-\|alert alert-" "$file"; then
        migrate_bootstrap_classes "$file"
    fi
done

# Processar templates de componentes
echo "📁 Processando templates de componentes..."
if [ -d "templates/components" ]; then
    find templates/components/ -name "*.html" -type f | while read -r file; do
        if grep -q "btn btn-\|card-\|badge bg-\|alert alert-" "$file"; then
            migrate_bootstrap_classes "$file"
        fi
    done
fi

echo "🎉 Migração concluída!"
echo "📊 Verificando resultados..."

# Contar referências restantes
BOOTSTRAP_REMAINING=$(grep -r "btn btn-" templates/ | wc -l)
TAILWIND_COUNT=$(grep -r "mm-btn" templates/ | wc -l)

echo "📈 Estatísticas pós-migração:"
echo "   - Referências Bootstrap restantes: $BOOTSTRAP_REMAINING"
echo "   - Componentes Tailwind: $TAILWIND_COUNT"

if [ $BOOTSTRAP_REMAINING -eq 0 ]; then
    echo "🎉 Migração 100% concluída!"
else
    echo "⚠️  Ainda há $BOOTSTRAP_REMAINING referências Bootstrap para revisar manualmente"
fi

echo "💡 Para reverter as mudanças, use os arquivos .backup criados"
