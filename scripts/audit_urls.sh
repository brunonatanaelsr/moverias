#!/bin/bash
# audit_urls.sh - Script para identificar inconsistências de URLs

echo "=== AUDITORIA DE URLs DO SISTEMA MOVE MARIAS ==="
echo "Data: $(date)"
echo ""

echo "1. URLs definidas em arquivos urls.py:"
echo "----------------------------------------"
find . -name "urls.py" -exec echo "=== {} ===" \; -exec grep -n "name=" {} \;

echo ""
echo "2. URLs referenciadas em templates:"
echo "-----------------------------------"
find templates/ -name "*.html" -exec grep -l "{% url" {} \; 2>/dev/null | while read file; do
    echo "=== $file ==="
    grep -n "{% url" "$file"
done

echo ""
echo "3. Possíveis inconsistências:"
echo "-----------------------------"

# Extrair nomes de URLs dos templates
grep -r "{% url" templates/ 2>/dev/null | sed "s/.*{% url ['\"]//g" | sed "s/['\"].*//g" | sort | uniq > /tmp/template_urls.txt

# Extrair nomes de URLs dos arquivos urls.py
find . -name "urls.py" -exec grep -h "name=" {} \; | sed "s/.*name=['\"]//g" | sed "s/['\"].*//g" | sort | uniq > /tmp/defined_urls.txt

echo "URLs usadas em templates mas não definidas:"
comm -23 /tmp/template_urls.txt /tmp/defined_urls.txt

echo ""
echo "URLs definidas mas não usadas:"
comm -13 /tmp/template_urls.txt /tmp/defined_urls.txt

# Cleanup
rm -f /tmp/template_urls.txt /tmp/defined_urls.txt
