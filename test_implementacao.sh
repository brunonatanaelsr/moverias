#!/bin/bash

# Script de Teste das Funcionalidades Implementadas - Move Marias
# Data: $(date)

echo "🔍 Iniciando testes das funcionalidades implementadas..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para teste
test_function() {
    echo -e "${YELLOW}Testing: $1${NC}"
    if eval "$2"; then
        echo -e "${GREEN}✅ PASSOU: $1${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU: $1${NC}"
        return 1
    fi
}

# Contadores
passed=0
failed=0

echo ""
echo "📋 TESTES DE SISTEMA"
echo "===================="

# Teste 1: Verificação do Django
if test_function "Verificação básica do Django" "python manage.py check --deploy"; then
    ((passed++))
else
    ((failed++))
fi

# Teste 2: Verificação de templates
if test_function "Sintaxe de templates" "python manage.py check --tag templates"; then
    ((passed++))
else
    ((failed++))
fi

# Teste 3: Verificação de arquivos de navegação
if test_function "Existência do template de navegação" "[ -f 'templates/components/navigation_items.html' ]"; then
    ((passed++))
else
    ((failed++))
fi

if test_function "Existência do backup da navegação" "[ -f 'templates/components/navigation_items_backup.html' ]"; then
    ((passed++))
else
    ((failed++))
fi

# Teste 4: Verificação de migrations
if test_function "Verificação de migrations pendentes" "python manage.py showmigrations --plan | grep -q '\\[ \\]' && exit 1 || exit 0"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "🔗 TESTES DE URLS E ROTAS"
echo "========================="

# Teste 5: URLs principais
urls_to_test=(
    "members:list"
    "social:list"
    "social:anamnesis-create"
    "projects:list"
    "workshops:list"
    "certificates:list"
    "communication:list"
    "dashboard:index"
    "users:list"
)

for url in "${urls_to_test[@]}"; do
    if test_function "Resolução da URL: $url" "python manage.py shell -c \"from django.urls import reverse; print(reverse('$url'))\" > /dev/null 2>&1"; then
        ((passed++))
    else
        ((failed++))
    fi
done

echo ""
echo "📄 TESTES DE TEMPLATES"
echo "======================"

# Teste 6: Templates críticos
templates_to_test=(
    "templates/base_optimized.html"
    "templates/components/navigation_items.html"
    "templates/social/anamnesis_list.html"
    "templates/dashboard/index.html"
)

for template in "${templates_to_test[@]}"; do
    if test_function "Existência do template: $template" "[ -f '$template' ]"; then
        ((passed++))
    else
        ((failed++))
    fi
done

echo ""
echo "🎯 TESTES DE FUNCIONALIDADES ESPECÍFICAS"
echo "========================================"

# Teste 7: Sintaxe específica do template de anamnese
if test_function "Sintaxe do template anamnesis_list.html" "python -c \"
import re
with open('templates/social/anamnesis_list.html', 'r') as f:
    content = f.read()
    
# Verificar se há tags Django mal formadas
if re.search(r'{% else %}.*{% endif %}.*{% else %}', content, re.DOTALL):
    exit(1)
    
# Verificar se há blocos if/endif balanceados
if_count = len(re.findall(r'{% if ', content))
endif_count = len(re.findall(r'{% endif %}', content))
if if_count != endif_count:
    exit(1)
    
exit(0)
\""; then
    ((passed++))
else
    ((failed++))
fi

# Teste 8: Verificação de estrutura do sidebar
if test_function "Estrutura do sidebar otimizada" "grep -q 'Beneficiárias' templates/components/navigation_items.html && grep -q 'Ações Rápidas' templates/components/navigation_items.html"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "📊 RESUMO DOS TESTES"
echo "===================="
echo -e "✅ Testes passaram: ${GREEN}$passed${NC}"
echo -e "❌ Testes falharam: ${RED}$failed${NC}"
echo -e "📊 Total de testes: $((passed + failed))"

if [ $failed -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}TODOS OS TESTES PASSARAM!${NC}"
    echo "✅ Sistema está funcionando corretamente"
    exit 0
else
    echo -e "\n⚠️  ${YELLOW}ALGUNS TESTES FALHARAM${NC}"
    echo "❌ Verifique os erros acima e corrija antes de continuar"
    exit 1
fi
