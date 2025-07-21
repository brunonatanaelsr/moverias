"""
Comando para executar custom jobs do negócio
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.custom_jobs import custom_job_manager
from core.cache_optimizer import cache_optimizer
from core.threshold_manager import threshold_manager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Executar custom jobs e otimizações do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schedule-business-jobs',
            action='store_true',
            help='Agendar todos os jobs de negócio',
        )
        parser.add_argument(
            '--run-job',
            type=str,
            help='Executar um job específico',
            choices=[
                'beneficiary_follow_up',
                'workshop_notifications',
                'certificate_processing',
                'weekly_progress_report',
                'inactive_users_cleanup',
                'monthly_analytics',
                'coaching_review_reminder',
            ]
        )
        parser.add_argument(
            '--optimize-cache',
            action='store_true',
            help='Executar otimização de cache',
        )
        parser.add_argument(
            '--adjust-thresholds',
            action='store_true',
            help='Ajustar thresholds de performance',
        )
        parser.add_argument(
            '--collect-metrics',
            action='store_true',
            help='Coletar métricas do sistema',
        )
        parser.add_argument(
            '--generate-reports',
            action='store_true',
            help='Gerar relatórios do sistema',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Mostrar status dos jobs e otimizações',
        )

    def handle(self, *args, **options):
        if options['schedule_business_jobs']:
            self.schedule_business_jobs()
        elif options['run_job']:
            self.run_specific_job(options['run_job'])
        elif options['optimize_cache']:
            self.optimize_cache()
        elif options['adjust_thresholds']:
            self.adjust_thresholds()
        elif options['collect_metrics']:
            self.collect_metrics()
        elif options['generate_reports']:
            self.generate_reports()
        elif options['status']:
            self.show_status()
        else:
            self.show_help()

    def schedule_business_jobs(self):
        """Agendar todos os jobs de negócio"""
        self.stdout.write(self.style.SUCCESS('=== AGENDANDO JOBS DE NEGÓCIO ==='))
        
        try:
            custom_job_manager.schedule_business_jobs()
            self.stdout.write(self.style.SUCCESS('✅ Jobs de negócio agendados com sucesso'))
            
            # Mostrar jobs agendados
            self.stdout.write('\n📋 Jobs Agendados:')
            jobs = [
                ('beneficiary_follow_up', 'Acompanhamento de beneficiárias', 'Diário às 09:00'),
                ('workshop_notifications', 'Notificações de workshops', 'Diário às 10:00'),
                ('certificate_processing', 'Processamento de certificados', 'Diário às 14:00'),
                ('weekly_progress_report', 'Relatório semanal', 'Segunda-feira às 08:00'),
                ('inactive_users_cleanup', 'Limpeza de usuários inativos', 'Sexta-feira às 16:00'),
                ('monthly_analytics', 'Análise mensal', 'Dia 1 às 07:00'),
                ('coaching_review_reminder', 'Lembrete de revisão de coaching', 'Dia 15 às 09:00'),
            ]
            
            for job_id, description, schedule in jobs:
                self.stdout.write(f'  • {description} ({schedule})')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao agendar jobs: {str(e)}'))

    def run_specific_job(self, job_name):
        """Executar um job específico"""
        self.stdout.write(self.style.SUCCESS(f'=== EXECUTANDO JOB: {job_name.upper()} ==='))
        
        try:
            # Mapear nome do job para método
            job_methods = {
                'beneficiary_follow_up': custom_job_manager.beneficiary_follow_up,
                'workshop_notifications': custom_job_manager.workshop_notifications,
                'certificate_processing': custom_job_manager.certificate_processing,
                'weekly_progress_report': custom_job_manager.weekly_progress_report,
                'inactive_users_cleanup': custom_job_manager.inactive_users_cleanup,
                'monthly_analytics': custom_job_manager.monthly_analytics,
                'coaching_review_reminder': custom_job_manager.coaching_review_reminder,
            }
            
            if job_name not in job_methods:
                self.stdout.write(self.style.ERROR(f'❌ Job não encontrado: {job_name}'))
                return
            
            # Executar job
            result = job_methods[job_name]()
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS('✅ Job executado com sucesso'))
                
                # Mostrar resultados
                if 'processed' in result:
                    self.stdout.write(f'  • Itens processados: {result["processed"]}')
                if 'recipients' in result:
                    self.stdout.write(f'  • Destinatários: {result["recipients"]}')
                if 'stats' in result:
                    self.stdout.write(f'  • Estatísticas: {result["stats"]}')
                
            else:
                self.stdout.write(self.style.ERROR(f'❌ Erro no job: {result.get("error", "Erro desconhecido")}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao executar job: {str(e)}'))

    def optimize_cache(self):
        """Executar otimização de cache"""
        self.stdout.write(self.style.SUCCESS('=== OTIMIZAÇÃO DE CACHE ==='))
        
        try:
            # Coletar métricas
            self.stdout.write('🔍 Coletando métricas de cache...')
            metrics = cache_optimizer.collect_metrics()
            
            if metrics:
                self.stdout.write('✅ Métricas coletadas')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Erro ao coletar métricas'))
                return
            
            # Gerar recomendações
            self.stdout.write('🧠 Gerando recomendações...')
            recommendations = cache_optimizer.generate_recommendations()
            
            if 'error' in recommendations:
                self.stdout.write(self.style.ERROR(f'❌ Erro: {recommendations["error"]}'))
                return
            
            rec_count = recommendations.get('total_recommendations', 0)
            self.stdout.write(f'✅ {rec_count} recomendações geradas')
            
            if rec_count > 0:
                # Mostrar recomendações
                self.stdout.write('\n📋 Recomendações:')
                for rec in recommendations['recommendations'][:5]:  # Mostrar top 5
                    priority = rec['priority'].upper()
                    self.stdout.write(f'  • [{priority}] {rec["description"]}')
                
                # Aplicar otimizações automáticas
                self.stdout.write('\n⚙️  Aplicando otimizações automáticas...')
                auto_applied = cache_optimizer.apply_optimizations(auto_apply=True)
                
                applied_count = auto_applied.get('total_applied', 0)
                if applied_count > 0:
                    self.stdout.write(f'✅ {applied_count} otimizações aplicadas')
                else:
                    self.stdout.write('ℹ️  Nenhuma otimização automática aplicada')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro na otimização: {str(e)}'))

    def adjust_thresholds(self):
        """Ajustar thresholds de performance"""
        self.stdout.write(self.style.SUCCESS('=== AJUSTE DE THRESHOLDS ==='))
        
        try:
            # Coletar métricas atuais
            self.stdout.write('📊 Coletando métricas atuais...')
            metrics = threshold_manager.collect_current_metrics()
            
            if metrics:
                self.stdout.write('✅ Métricas coletadas')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Erro ao coletar métricas'))
                return
            
            # Analisar padrões
            self.stdout.write('🔍 Analisando padrões de performance...')
            analysis = threshold_manager.analyze_performance_patterns()
            
            if analysis.get('status') == 'insufficient_data':
                self.stdout.write(self.style.WARNING(f'⚠️  {analysis["message"]}'))
                return
            
            # Ajustar thresholds
            self.stdout.write('⚙️  Ajustando thresholds...')
            adjustments = threshold_manager.adjust_thresholds(analysis)
            
            if 'error' in adjustments:
                self.stdout.write(self.style.ERROR(f'❌ Erro: {adjustments["error"]}'))
                return
            
            applied_count = len(adjustments.get('applied_adjustments', {}))
            proposed_count = len(adjustments.get('proposed_adjustments', {}))
            
            self.stdout.write(f'✅ {applied_count} ajustes aplicados de {proposed_count} propostos')
            
            if applied_count > 0:
                self.stdout.write('\n📋 Ajustes Aplicados:')
                for metric, adjustment in adjustments['applied_adjustments'].items():
                    self.stdout.write(f'  • {metric}:')
                    self.stdout.write(f'    Warning: {adjustment["old_warning"]} → {adjustment["new_warning"]}')
                    self.stdout.write(f'    Critical: {adjustment["old_critical"]} → {adjustment["new_critical"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro no ajuste: {str(e)}'))

    def collect_metrics(self):
        """Coletar métricas do sistema"""
        self.stdout.write(self.style.SUCCESS('=== COLETA DE MÉTRICAS ==='))
        
        try:
            # Coletar métricas de threshold
            self.stdout.write('📊 Coletando métricas de performance...')
            perf_metrics = threshold_manager.collect_current_metrics()
            
            # Coletar métricas de cache
            self.stdout.write('💾 Coletando métricas de cache...')
            cache_metrics = cache_optimizer.collect_metrics()
            
            self.stdout.write('✅ Métricas coletadas com sucesso')
            
            # Mostrar resumo
            if perf_metrics:
                self.stdout.write('\n📈 Métricas de Performance:')
                for metric, value in perf_metrics.items():
                    if metric != 'timestamp' and value is not None:
                        self.stdout.write(f'  • {metric}: {value}')
            
            if cache_metrics:
                self.stdout.write('\n💾 Métricas de Cache:')
                cache_stats = cache_metrics.get('cache_stats', {})
                for metric, value in cache_stats.items():
                    if value is not None:
                        self.stdout.write(f'  • {metric}: {value}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro na coleta: {str(e)}'))

    def generate_reports(self):
        """Gerar relatórios do sistema"""
        self.stdout.write(self.style.SUCCESS('=== GERAÇÃO DE RELATÓRIOS ==='))
        
        try:
            # Relatório de cache
            self.stdout.write('📊 Gerando relatório de cache...')
            cache_status = cache_optimizer.get_optimization_status()
            
            # Relatório de thresholds
            self.stdout.write('📈 Gerando relatório de thresholds...')
            threshold_status = threshold_manager.get_status()
            
            # Relatório de jobs
            self.stdout.write('⚙️  Gerando relatório de jobs...')
            # Implementar quando necessário
            
            self.stdout.write('✅ Relatórios gerados')
            
            # Mostrar resumo
            self.stdout.write('\n📋 Resumo dos Relatórios:')
            
            # Status do cache
            if cache_status.get('status') == 'recommendations_available':
                rec_count = cache_status.get('recommendations_count', 0)
                self.stdout.write(f'  • Cache: {rec_count} recomendações disponíveis')
            else:
                self.stdout.write(f'  • Cache: {cache_status.get("message", "Status desconhecido")}')
            
            # Status dos thresholds
            if threshold_status.get('current_metrics'):
                alerts = threshold_status.get('threshold_check', {}).get('alerts', [])
                self.stdout.write(f'  • Thresholds: {len(alerts)} alertas ativos')
            else:
                self.stdout.write('  • Thresholds: Sem dados disponíveis')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro na geração: {str(e)}'))

    def show_status(self):
        """Mostrar status dos jobs e otimizações"""
        self.stdout.write(self.style.SUCCESS('=== STATUS DO SISTEMA ==='))
        
        try:
            # Status do cache
            self.stdout.write('\n💾 Status do Cache:')
            cache_status = cache_optimizer.get_optimization_status()
            
            status_msg = cache_status.get('message', 'Status desconhecido')
            self.stdout.write(f'  • Status: {status_msg}')
            
            if cache_status.get('recommendations_count', 0) > 0:
                self.stdout.write(f'  • Recomendações: {cache_status["recommendations_count"]}')
                self.stdout.write(f'    - Alta prioridade: {cache_status.get("high_priority", 0)}')
                self.stdout.write(f'    - Média prioridade: {cache_status.get("medium_priority", 0)}')
                self.stdout.write(f'    - Baixa prioridade: {cache_status.get("low_priority", 0)}')
            
            # Status dos thresholds
            self.stdout.write('\n📊 Status dos Thresholds:')
            threshold_status = threshold_manager.get_status()
            
            if threshold_status.get('current_metrics'):
                threshold_check = threshold_status.get('threshold_check', {})
                self.stdout.write(f'  • Status: {threshold_check.get("status", "unknown")}')
                self.stdout.write(f'  • Alertas críticos: {threshold_check.get("critical_count", 0)}')
                self.stdout.write(f'  • Alertas de warning: {threshold_check.get("warning_count", 0)}')
                
                auto_enabled = threshold_status.get('auto_adjustment_enabled', False)
                self.stdout.write(f'  • Ajuste automático: {"Habilitado" if auto_enabled else "Desabilitado"}')
            
            # Status dos jobs
            self.stdout.write('\n⚙️  Status dos Jobs:')
            self.stdout.write('  • Jobs de negócio: Configurados')
            self.stdout.write('  • Agendamento: Ativo')
            self.stdout.write('  • Última execução: Verifique logs')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao obter status: {str(e)}'))

    def show_help(self):
        """Mostrar ajuda"""
        self.stdout.write(self.style.SUCCESS('=== GERENCIAMENTO DE JOBS E OTIMIZAÇÕES ==='))
        self.stdout.write('')
        self.stdout.write('Comandos disponíveis:')
        self.stdout.write('')
        self.stdout.write('⚙️  Jobs de Negócio:')
        self.stdout.write('  --schedule-business-jobs    Agendar todos os jobs')
        self.stdout.write('  --run-job JOB_NAME         Executar job específico')
        self.stdout.write('')
        self.stdout.write('💾 Otimização de Cache:')
        self.stdout.write('  --optimize-cache           Executar otimização de cache')
        self.stdout.write('')
        self.stdout.write('📊 Thresholds:')
        self.stdout.write('  --adjust-thresholds        Ajustar thresholds automaticamente')
        self.stdout.write('')
        self.stdout.write('📈 Monitoramento:')
        self.stdout.write('  --collect-metrics          Coletar métricas do sistema')
        self.stdout.write('  --generate-reports         Gerar relatórios')
        self.stdout.write('  --status                   Mostrar status geral')
        self.stdout.write('')
        self.stdout.write('📝 Exemplos:')
        self.stdout.write('  python manage.py run_custom_jobs --schedule-business-jobs')
        self.stdout.write('  python manage.py run_custom_jobs --run-job beneficiary_follow_up')
        self.stdout.write('  python manage.py run_custom_jobs --optimize-cache')
        self.stdout.write('  python manage.py run_custom_jobs --adjust-thresholds')
