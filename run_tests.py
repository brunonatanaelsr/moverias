#!/usr/bin/env python
"""
Script para executar suite completa de testes
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime


def run_command(command, description):
    """Executar comando e capturar resultado"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print('='*60)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Executar testes Django')
    parser.add_argument('--unit', action='store_true', help='Executar apenas testes unitários')
    parser.add_argument('--integration', action='store_true', help='Executar apenas testes de integração')
    parser.add_argument('--api', action='store_true', help='Executar apenas testes de API')
    parser.add_argument('--security', action='store_true', help='Executar apenas testes de segurança')
    parser.add_argument('--performance', action='store_true', help='Executar apenas testes de performance')
    parser.add_argument('--smoke', action='store_true', help='Executar apenas testes smoke')
    parser.add_argument('--coverage', action='store_true', help='Gerar relatório de cobertura')
    parser.add_argument('--verbose', '-v', action='store_true', help='Saída verbosa')
    parser.add_argument('--failfast', '-x', action='store_true', help='Parar no primeiro erro')
    
    args = parser.parse_args()
    
    # Configurar ambiente
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movemarias.settings')
    
    print("🚀 Iniciando Suite de Testes Django")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Comandos base
    base_cmd = "python -m pytest"
    
    if args.verbose:
        base_cmd += " -v"
    
    if args.failfast:
        base_cmd += " -x"
    
    # Determinar quais testes executar
    test_suites = []
    
    if args.unit:
        test_suites.append(("-m unit", "Testes Unitários"))
    elif args.integration:
        test_suites.append(("-m integration", "Testes de Integração"))
    elif args.api:
        test_suites.append(("-m api", "Testes de API"))
    elif args.security:
        test_suites.append(("-m security", "Testes de Segurança"))
    elif args.performance:
        test_suites.append(("-m performance", "Testes de Performance"))
    elif args.smoke:
        test_suites.append(("-m smoke", "Testes Smoke"))
    else:
        # Executar todos os testes em ordem
        test_suites = [
            ("-m unit", "Testes Unitários"),
            ("-m integration", "Testes de Integração"),
            ("-m api", "Testes de API"),
            ("-m security", "Testes de Segurança"),
            ("-m 'performance and not slow'", "Testes de Performance (Rápidos)"),
            ("-m smoke", "Testes Smoke"),
        ]
    
    # Executar testes
    all_passed = True
    results = []
    
    for marker, description in test_suites:
        cmd = f"{base_cmd} {marker}"
        
        if args.coverage and "unit" in marker:
            cmd += " --cov=. --cov-report=html --cov-report=term-missing"
        
        success = run_command(cmd, description)
        results.append((description, success))
        all_passed = all_passed and success
    
    # Executar testes específicos adicionais
    additional_tests = [
        ("python manage.py check", "Django System Check"),
        ("python manage.py check --deploy", "Django Deploy Check"),
    ]
    
    print(f"\n{'='*60}")
    print("🔧 Verificações Adicionais")
    print('='*60)
    
    for cmd, description in additional_tests:
        success = run_command(cmd, description)
        results.append((description, success))
        all_passed = all_passed and success
    
    # Relatório final
    print(f"\n{'='*60}")
    print("📊 RELATÓRIO FINAL")
    print('='*60)
    
    for description, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {description}")
    
    if all_passed:
        print(f"\n🎉 TODOS OS TESTES PASSARAM! 🎉")
        return 0
    else:
        print(f"\n💥 ALGUNS TESTES FALHARAM 💥")
        return 1


if __name__ == "__main__":
    sys.exit(main())
