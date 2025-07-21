#!/bin/bash

# Script para corrigir importações do sistema de permissões

echo "🔧 Corrigindo importações do sistema de permissões..."

# Encontrar todos os arquivos Python que precisam ser corrigidos
find . -name "*.py" -type f -exec grep -l "from core.unified_permissions import" {} \; | while read file; do
    echo "📝 Corrigindo: $file"
    
    # Fazer backup
    cp "$file" "$file.backup"
    
    # Corrigir importações
    sed -i '' 's/user_has_permission,//g' "$file"
    sed -i '' 's/require_technician_permission,/requires_technician,/g' "$file"
    sed -i '' 's/require_staff_permission,/requires_admin,/g' "$file"
    sed -i '' 's/require_coordinator_permission,/requires_coordinator,/g' "$file"
    sed -i '' 's/StaffRequiredMixin/AdminRequiredMixin/g' "$file"
    sed -i '' 's/@require_technician_permission/@requires_technician/g' "$file"
    sed -i '' 's/@require_staff_permission/@requires_admin/g' "$file"
    sed -i '' 's/@require_coordinator_permission/@requires_coordinator/g' "$file"
    
    echo "✅ Concluído: $file"
done

echo "🎉 Correções concluídas!"
