#!/bin/bash

# Script para análise detalhada dos componentes Bootstrap restantes

echo "🔍 ANÁLISE DETALHADA DOS 11% RESTANTES DA MIGRAÇÃO TAILWIND"
echo "============================================================"

echo ""
echo "📋 RESUMO DOS COMPONENTES BOOTSTRAP RESTANTES:"
echo ""

# Análise por tipo de componente
echo "1. 🔘 BOTÕES (btn btn-*):"
grep -r "btn btn-" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"
grep -r "btn btn-" templates/ --include="*.html" | grep -o "templates/[^:]*" | sort | uniq -c | sort -nr | head -10

echo ""
echo "2. 🎫 BADGES (badge bg-*):"
grep -r "badge bg-" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"
grep -r "badge bg-" templates/ --include="*.html" | grep -o "templates/[^:]*" | sort | uniq -c | sort -nr | head -10

echo ""
echo "3. 🚨 ALERTS (alert alert-*):"
grep -r "alert alert-" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"
grep -r "alert alert-" templates/ --include="*.html" | grep -o "templates/[^:]*" | sort | uniq -c | sort -nr | head -10

echo ""
echo "4. 🃏 CARDS (card-*):"
grep -r "card-" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"
grep -r "card-" templates/ --include="*.html" | grep -o "templates/[^:]*" | sort | uniq -c | sort -nr | head -10

echo ""
echo "5. 🎯 BOOTSTRAP JS (data-bs-*):"
grep -r "data-bs-" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"
grep -r "data-bs-" templates/ --include="*.html" | grep -o "templates/[^:]*" | sort | uniq -c | sort -nr | head -10

echo ""
echo "6. 📐 LAYOUT CLASSES (d-flex, justify-content-*, etc.):"
grep -r "d-flex\|justify-content-\|align-items-" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"

echo ""
echo "7. 📏 SPACING CLASSES (me-*, ms-*, etc.):"
grep -r "me-[0-9]\|ms-[0-9]\|mb-[0-9]\|mt-[0-9]\|mx-[0-9]\|my-[0-9]" templates/ --include="*.html" | wc -l | xargs echo "   - Total:"

echo ""
echo "========================================="
echo "📊 PRIORIDADE DE MIGRAÇÃO:"
echo "========================================="
echo "🥇 ALTA PRIORIDADE (Funcionalidade crítica):"
echo "   - Módulo Tasks: 18 referências Bootstrap"
echo "   - Modais com data-bs-: 11 referências"
echo ""
echo "🥈 MÉDIA PRIORIDADE (Visual):"
echo "   - Badges: 11 referências"
echo "   - Cards: 21 referências"
echo ""
echo "🥉 BAIXA PRIORIDADE (Poucos casos):"
echo "   - Alerts: 2 referências"
echo "   - Espaçamento: Casos pontuais"
echo ""
echo "🎯 ESTIMATIVA DE TEMPO:"
echo "   - Tasks: 2-3 horas"
echo "   - Modais: 1-2 horas"
echo "   - Badges: 1 hora"
echo "   - Cards: 1 hora"
echo "   - TOTAL: 5-7 horas"
