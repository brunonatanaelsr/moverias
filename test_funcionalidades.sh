#!/bin/bash

# Script para testar funcionalidades do sistema Move Marias
# Executa testes básicos para verificar se o backend e frontend estão funcionando

echo "==================================="
echo "TESTE DE FUNCIONALIDADES - MOVE MARIAS"
echo "==================================="

# Verificar se estamos no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do projeto Django"
    exit 1
fi

echo "🔍 Iniciando testes..."

# 1. Verificar se o servidor Django está rodando
echo "1. Testando servidor Django..."
python manage.py check --deploy &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Django configurado corretamente"
else
    echo "❌ Problemas na configuração do Django"
fi

# 2. Verificar migrações
echo "2. Verificando migrações..."
python manage.py showmigrations --plan | grep -q "[ ]"
if [ $? -eq 0 ]; then
    echo "⚠️  Migrações pendentes encontradas"
else
    echo "✅ Todas as migrações aplicadas"
fi

# 3. Verificar se existem erros nos templates
echo "3. Verificando templates..."
find templates/ -name "*.html" -type f | wc -l
echo "✅ $(find templates/ -name "*.html" -type f | wc -l) templates encontrados"

# 4. Verificar se Bootstrap foi removido
echo "4. Verificando migração Bootstrap → Tailwind..."
BOOTSTRAP_COUNT=$(grep -r "btn btn-" templates/ | wc -l)
echo "📊 $BOOTSTRAP_COUNT referências Bootstrap encontradas"

TAILWIND_COUNT=$(grep -r "mm-btn" templates/ | wc -l)
echo "📊 $TAILWIND_COUNT componentes Tailwind encontrados"

# 5. Verificar URLs
echo "5. Verificando URLs..."
python manage.py show_urls --format=json &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ URLs configuradas corretamente"
else
    echo "❌ Problemas nas URLs"
fi

# 6. Verificar permissões
echo "6. Verificando sistema de permissões..."
if [ -f "core/unified_permissions.py" ]; then
    echo "✅ Sistema de permissões unificado encontrado"
else
    echo "❌ Sistema de permissões não encontrado"
fi

# 7. Verificar APIs
echo "7. Verificando APIs..."
if [ -f "api/views.py" ]; then
    API_COUNT=$(grep -c "class.*ViewSet" api/views.py)
    echo "✅ $API_COUNT ViewSets encontrados"
else
    echo "❌ Arquivo API não encontrado"
fi

# 8. Verificar static files
echo "8. Verificando arquivos estáticos..."
if [ -d "static/" ]; then
    CSS_COUNT=$(find static/ -name "*.css" | wc -l)
    JS_COUNT=$(find static/ -name "*.js" | wc -l)
    echo "✅ $CSS_COUNT arquivos CSS, $JS_COUNT arquivos JS"
else
    echo "❌ Diretório static/ não encontrado"
fi

# 9. Verificar documentação
echo "9. Verificando documentação..."
if [ -d "docs/" ]; then
    DOC_COUNT=$(find docs/ -name "*.md" | wc -l)
    echo "✅ $DOC_COUNT documentos encontrados"
else
    echo "❌ Diretório docs/ não encontrado"
fi

# 10. Verificar funcionalidades principais
echo "10. Verificando módulos principais..."
MODULES=("members" "workshops" "projects" "users" "social" "coaching" "evolution" "notifications" "dashboard" "hr")

for module in "${MODULES[@]}"; do
    if [ -f "${module}/views.py" ]; then
        VIEW_COUNT=$(grep -c "class.*View" "${module}/views.py")
        echo "✅ Módulo $module: $VIEW_COUNT views"
    else
        echo "❌ Módulo $module: views.py não encontrado"
    fi
done

echo "==================================="
echo "RESUMO DOS TESTES"
echo "==================================="

# Contagem final
TOTAL_TEMPLATES=$(find templates/ -name "*.html" | wc -l)
TOTAL_VIEWS=$(find . -name "views.py" -exec grep -c "class.*View" {} \; | awk '{s+=$1} END {print s}')
TOTAL_URLS=$(find . -name "urls.py" | wc -l)
TOTAL_MODELS=$(find . -name "models.py" -exec grep -c "class.*Model" {} \; | awk '{s+=$1} END {print s}')

echo "📊 Total de templates: $TOTAL_TEMPLATES"
echo "📊 Total de views: $TOTAL_VIEWS"
echo "📊 Total de URLs: $TOTAL_URLS"
echo "📊 Total de models: $TOTAL_MODELS"

echo "==================================="
echo "RECOMENDAÇÕES"
echo "==================================="

if [ $BOOTSTRAP_COUNT -gt 0 ]; then
    echo "⚠️  Finalizar migração Bootstrap → Tailwind ($BOOTSTRAP_COUNT referências restantes)"
fi

echo "✅ Execute 'python manage.py test' para testes unitários"
echo "✅ Execute 'python manage.py runserver' para iniciar o servidor"
echo "✅ Acesse http://localhost:8000 para testar o frontend"

echo "==================================="
echo "TESTE CONCLUÍDO"
echo "==================================="
