#!/usr/bin/env python3
"""
URL Parameter Reflection Tester
Ferramenta para testar reflexão de parâmetros em URLs
Author: pad1ryoshi
"""

import requests
import sys
import argparse
import time
import random
import string
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from bs4 import BeautifulSoup
import re
from colorama import Fore, Back, Style, init

# Inicializar colorama
init(autoreset=True)

class ParameterReflectionTester:
    def __init__(self, threads=10, timeout=10, delay=0):
        self.threads = threads
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.results = []
        
    def generate_unique_payload(self, length=12):
        """Gera um payload único para testar reflexão"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def replace_params_with_payload(self, url, payload):
        """Substitui todos os valores dos parâmetros pelo payload único"""
        parsed = urlparse(url)
        
        if not parsed.query:
            return url
            
        # Parse dos parâmetros existentes
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        # Substituir todos os valores pelos payloads
        new_params = {}
        for param_name, param_values in params.items():
            # Se o valor original é FUZZ, ou qualquer outro valor, substitui pelo payload
            new_params[param_name] = [payload] * len(param_values)
        
        # Reconstruir a query string
        new_query = urlencode(new_params, doseq=True)
        
        # Reconstruir a URL
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def check_reflection_in_response(self, response_text, payload):
        """Verifica se o payload está refletido no corpo da resposta HTTP"""
        reflections = []
        
        # Busca direta pelo payload
        if payload in response_text:
            # Conta quantas vezes aparece
            count = response_text.count(payload)
            reflections.append({
                'type': 'direct',
                'count': count,
                'payload': payload
            })
            
        return reflections
    
    def check_reflection_in_dom(self, response_text, payload):
        """Verifica se o payload está refletido no DOM (elementos HTML)"""
        dom_reflections = []
        
        try:
            soup = BeautifulSoup(response_text, 'html.parser')
            
            # Verificar em diferentes contextos do DOM
            contexts = [
                ('input_value', soup.find_all('input')),
                ('textarea', soup.find_all('textarea')),
                ('script', soup.find_all('script')),
                ('href', soup.find_all('a')),
                ('src', soup.find_all(['img', 'script', 'iframe'])),
                ('onclick', soup.find_all(attrs={'onclick': True})),
                ('text_content', soup.find_all(text=True))
            ]
            
            for context_name, elements in contexts:
                for element in elements:
                    if context_name == 'text_content':
                        if payload in str(element):
                            dom_reflections.append({
                                'context': 'text_node',
                                'payload': payload,
                                'element': str(element)[:100] + '...' if len(str(element)) > 100 else str(element)
                            })
                    else:
                        element_str = str(element)
                        if payload in element_str:
                            dom_reflections.append({
                                'context': context_name,
                                'payload': payload,
                                'element': element_str[:200] + '...' if len(element_str) > 200 else element_str
                            })
                            
        except Exception as e:
            print(f"{Fore.YELLOW}[WARNING] Erro ao analisar DOM: {e}")
            
        return dom_reflections
    
    def test_url(self, url):
        """Testa uma URL específica para reflexão de parâmetros"""
        result = {
            'url': url,
            'status': 'error',
            'reflections': [],
            'dom_reflections': [],
            'response_code': None,
            'error': None
        }
        
        try:
            # Gerar payload único
            payload = self.generate_unique_payload()
            
            # Substituir todos os parâmetros pelo payload
            test_url = self.replace_params_with_payload(url, payload)
            
            print(f"{Fore.CYAN}[INFO] Testando: {test_url}")
            
            # Fazer requisição
            response = self.session.get(test_url, timeout=self.timeout, allow_redirects=True)
            result['response_code'] = response.status_code
            
            if response.status_code == 200:
                response_text = response.text
                
                # Verificar reflexão no corpo da resposta
                reflections = self.check_reflection_in_response(response_text, payload)
                result['reflections'] = reflections
                
                # Verificar reflexão no DOM
                dom_reflections = self.check_reflection_in_dom(response_text, payload)
                result['dom_reflections'] = dom_reflections
                
                if reflections or dom_reflections:
                    result['status'] = 'reflected'
                    print(f"{Fore.GREEN}[FOUND] Reflexão detectada em: {test_url}")
                    
                    if reflections:
                        for ref in reflections:
                            print(f"  {Fore.GREEN}└─ Corpo HTTP: {ref['count']} ocorrência(s)")
                    
                    if dom_reflections:
                        for dom_ref in dom_reflections:
                            print(f"  {Fore.GREEN}└─ DOM ({dom_ref['context']}): {dom_ref['element'][:50]}...")
                else:
                    result['status'] = 'clean'
                    print(f"{Fore.WHITE}[CLEAN] Nenhuma reflexão em: {test_url}")
            else:
                result['status'] = 'error'
                result['error'] = f"HTTP {response.status_code}"
                print(f"{Fore.YELLOW}[ERROR] HTTP {response.status_code}: {test_url}")
                
        except requests.exceptions.Timeout:
            result['error'] = 'Timeout'
            print(f"{Fore.RED}[TIMEOUT] {url}")
        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
            print(f"{Fore.RED}[ERROR] {url}: {e}")
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"
            print(f"{Fore.RED}[ERROR] {url}: {e}")
        
        # Delay entre requisições
        if self.delay > 0:
            time.sleep(self.delay)
            
        return result
    
    def run_tests(self, urls):
        """Executa testes em paralelo para lista de URLs"""
        print(f"{Fore.MAGENTA}[INFO] Iniciando testes em {len(urls)} URLs com {self.threads} threads")
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_url = {executor.submit(self.test_url, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                result = future.result()
                self.results.append(result)
    
    def generate_report(self, output_file=None):
        """Gera relatório dos resultados"""
        reflected_count = len([r for r in self.results if r['status'] == 'reflected'])
        clean_count = len([r for r in self.results if r['status'] == 'clean'])
        error_count = len([r for r in self.results if r['status'] == 'error'])
        
        report = {
            'summary': {
                'total_tested': len(self.results),
                'reflected': reflected_count,
                'clean': clean_count,
                'errors': error_count
            },
            'reflected_urls': [r for r in self.results if r['status'] == 'reflected'],
            'all_results': self.results
        }
        
        # Imprimir sumário
        print(f"\n{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}RELATÓRIO FINAL")
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.WHITE}Total testado: {len(self.results)}")
        print(f"{Fore.GREEN}URLs Refletidas: {reflected_count}")
        print(f"{Fore.WHITE}Limpos: {clean_count}")
        print(f"{Fore.RED}Erros: {error_count}")
        
        if reflected_count > 0:
            print(f"\n{Fore.GREEN}URLs COM REFLEXÃO:")
            for result in report['reflected_urls']:
                print(f"{Fore.GREEN}  ├─ {result['url']}")
                if result['reflections']:
                    for ref in result['reflections']:
                        print(f"{Fore.GREEN}  │  └─ HTTP Body: {ref['count']} reflexão(ões)")
                if result['dom_reflections']:
                    for dom_ref in result['dom_reflections']:
                        print(f"{Fore.GREEN}  │  └─ DOM ({dom_ref['context']})")
        
        # Salvar em arquivo se especificado
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n{Fore.CYAN}[INFO] Relatório salvo em: {output_file}")
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description='Testa reflexão de parâmetros em URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python3 paramsource.py -f urls.txt
  python3 paramsource.py -f urls.txt -t 20 -d 1 -o results.json
  python3 paramsource.py -f urls.txt --timeout 15
        """
    )
    
    parser.add_argument('-f', '--file', required=True, help='Arquivo com lista de URLs')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Número de threads (padrão: 10)')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout das requisições em segundos (padrão: 10)')
    parser.add_argument('-d', '--delay', type=float, default=0, help='Delay entre requisições em segundos (padrão: 0)')
    parser.add_argument('-o', '--output', help='Arquivo para salvar relatório JSON')
    
    args = parser.parse_args()
    
    # Ler URLs do arquivo
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"{Fore.RED}[ERROR] Arquivo não encontrado: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Erro ao ler arquivo: {e}")
        sys.exit(1)
    
    if not urls:
        print(f"{Fore.RED}[ERROR] Nenhuma URL encontrada no arquivo")
        sys.exit(1)
    
    # Criar tester e executar
    tester = ParameterReflectionTester(
        threads=args.threads,
        timeout=args.timeout,
        delay=args.delay
    )
    
    try:
        tester.run_tests(urls)
        tester.generate_report(args.output)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INFO] Teste interrompido pelo usuário")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Erro durante execução: {e}")

if __name__ == '__main__':
    main()
