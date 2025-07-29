#!/bin/bash
"""
CONFIGURAÇÃO DE CRON JOBS - SISTEMA DE NOTIFICAÇÕES MOVE MARIAS
Script para automatizar as notificações do sistema
"""
# Script de configuração de cron jobs para notificações automáticas

# Definir variáveis
MOVE_PATH="/workspaces/move"
PYTHON_PATH="python3"
SCRIPT_PATH="$MOVE_PATH/automated_notifications.py"

echo "=========================================="
echo "🔧 CONFIGURADOR DE CRON JOBS - MOVE MARIAS"
echo "=========================================="

# Verificar se o script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Erro: Script de notificações não encontrado em $SCRIPT_PATH"
    exit 1
fi

echo "✅ Script de notificações encontrado"

# Criar diretório de logs se não existir
LOG_DIR="$MOVE_PATH/logs"
mkdir -p "$LOG_DIR"

echo "✅ Diretório de logs criado: $LOG_DIR"

# Backup do crontab atual
echo "💾 Fazendo backup do crontab atual..."
crontab -l > "$MOVE_PATH/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "⚠️  Nenhum crontab existente"

# Cron jobs recomendados
echo "📋 Configurando cron jobs..."

# Criar arquivo temporário com novos cron jobs
TEMP_CRON=$(mktemp)

# Preservar cron jobs existentes (se houver)
crontab -l 2>/dev/null | grep -v "# Move Marias Notifications" >> "$TEMP_CRON" || true

# Adicionar novos cron jobs
cat >> "$TEMP_CRON" << EOF

# Move Marias Notifications - Auto-generated
# Notificações diárias às 8h
0 8 * * * cd $MOVE_PATH && $PYTHON_PATH $SCRIPT_PATH --frequency daily >> $LOG_DIR/notifications_daily.log 2>&1

# Notificações semanais às segundas-feiras às 9h
0 9 * * 1 cd $MOVE_PATH && $PYTHON_PATH $SCRIPT_PATH --frequency weekly >> $LOG_DIR/notifications_weekly.log 2>&1

# Notificações mensais no primeiro dia do mês às 10h
0 10 1 * * cd $MOVE_PATH && $PYTHON_PATH $SCRIPT_PATH --frequency monthly >> $LOG_DIR/notifications_monthly.log 2>&1

# Limpeza de logs antigos (executar semanalmente)
0 2 * * 0 find $LOG_DIR -name "*.log" -mtime +30 -delete

EOF

# Instalar novo crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Cron jobs configurados com sucesso!"

# Mostrar cron jobs ativos
echo ""
echo "📅 CRON JOBS ATIVOS:"
echo "===================="
crontab -l | grep -A 10 "Move Marias Notifications"

echo ""
echo "📊 CRONOGRAMA DE EXECUÇÃO:"
echo "=========================="
echo "• Notificações Diárias:  Todos os dias às 8:00"
echo "• Notificações Semanais: Segundas-feiras às 9:00"
echo "• Notificações Mensais:  Primeiro dia do mês às 10:00"
echo "• Limpeza de Logs:       Domingos às 2:00"

echo ""
echo "📁 LOGS SALVOS EM:"
echo "=================="
echo "• Diárias:  $LOG_DIR/notifications_daily.log"
echo "• Semanais: $LOG_DIR/notifications_weekly.log"
echo "• Mensais:  $LOG_DIR/notifications_monthly.log"

echo ""
echo "🔧 COMANDOS ÚTEIS:"
echo "=================="
echo "• Ver cron jobs:        crontab -l"
echo "• Editar cron jobs:     crontab -e"
echo "• Teste manual diário:  cd $MOVE_PATH && python automated_notifications.py --frequency daily"
echo "• Teste completo:       cd $MOVE_PATH && python automated_notifications.py --test"

echo ""
echo "✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "=========================================="

# Teste de execução
echo ""
echo "🧪 EXECUTANDO TESTE DE FUNCIONAMENTO..."
cd "$MOVE_PATH"
python3 "$SCRIPT_PATH" --test --frequency daily

echo ""
echo "🎉 SISTEMA DE NOTIFICAÇÕES AUTOMÁTICAS CONFIGURADO E TESTADO!"
echo "Os emails serão enviados automaticamente conforme programado."
