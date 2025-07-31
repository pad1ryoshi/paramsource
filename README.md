# 🔍 Parameter Reflection Tester

Uma ferramenta Python para testar reflexão de parâmetros em URLs, útil para identificar potenciais vulnerabilidades de XSS refletido.

## 🎯 Funcionalidades

- ✅ **Detecção Automática**: Identifica automaticamente todos os parâmetros em URLs
- ✅ **Substituição Inteligente**: Substitui qualquer valor de parâmetro (FUZZ ou valores reais) por payloads únicos
- ✅ **Detecção de Reflexão HTTP**: Verifica se parâmetros são refletidos no corpo da resposta
- ✅ **Análise DOM**: Detecta reflexões em contextos específicos do DOM (inputs, scripts, atributos)
- ✅ **Payloads Únicos**: Gera strings aleatórias para evitar falsos positivos
- ✅ **Threading**: Execução paralela para maior velocidade
- ✅ **Rate Limiting**: Controle de delay entre requisições
- ✅ **Relatórios Detalhados**: Saída colorizada e exportação JSON
- ✅ **User-Agent Realista**: Headers HTTP que simulam navegadores reais

## 🚀 Instalação

### Pré-requisitos
- Python 3.6+
- pip

### Dependências
```bash
pip install requests beautifulsoup4 colorama
```

### Download
```bash
git clone https://github.com/pad1ryoshi/paramsource.git
cd paramsource
chmod +x paramsource.py
```

## 📝 Como Usar

### Preparar arquivo de URLs
Crie um arquivo com URLs contendo parâmetros. A ferramenta substituirá **automaticamente** todos os valores dos parâmetros por payloads únicos:

```
https://example.com/?q=search_term
https://example.com/?search=products&category=electronics
https://example.com/page?id=123
https://example.com/?utm_source=google&utm_medium=cpc
https://example.com/?email=test@example.com
https://example.com/media/pressreleases?y=2024
```

### Execução Básica
```bash
python3 paramsource.py -f urls.txt
```

### Execução com Parâmetros Personalizados
```bash
# Com 20 threads e delay de 1 segundo
python3 paramsource.py -f urls.txt -t 20 -d 1

# Com timeout personalizado e saída JSON
python3 paramsource.py -f urls.txt --timeout 15 -o results.json

# Configuração para evasão de rate limiting
python3 paramsource.py -f urls.txt -t 5 -d 2 --timeout 20
```

## ⚙️ Parâmetros

| Parâmetro | Descrição | Padrão |
|-----------|-----------|---------|
| `-f, --file` | Arquivo com lista de URLs (obrigatório) | - |
| `-t, --threads` | Número de threads para execução paralela | 10 |
| `--timeout` | Timeout das requisições HTTP (segundos) | 10 |
| `-d, --delay` | Delay entre requisições (segundos) | 0 |
| `-o, --output` | Arquivo para salvar relatório JSON | - |

## 📊 Tipos de Detecção

### 1. Reflexão HTTP Body
Detecta quando o payload aparece diretamente no corpo da resposta:
```html
<p>Você pesquisou por: abc123random</p>
```

### 2. Reflexão DOM
Analisa contextos específicos do DOM:

- **Input Values**: `<input value="abc123random">`
- **Scripts**: `<script>var query = "abc123random";</script>`
- **Atributos href**: `<a href="/search?q=abc123random">`
- **Atributos src**: `<img src="/image.php?name=abc123random">`
- **Event Handlers**: `<div onclick="search('abc123random')">`
- **Text Nodes**: Texto direto no HTML

## 📈 Exemplo de Saída

```
[INFO] Testando: https://example.com/?q=abc123random
[FOUND] Reflexão detectada em: https://example.com/?q=abc123random
  └─ Corpo HTTP: 2 ocorrência(s)
  └─ DOM (input_value): <input type="text" value="abc123random">
  └─ DOM (script): <script>var searchTerm = "abc123random";</script>

============================================================
RELATÓRIO FINAL
============================================================
Total testado: 15
Vulneráveis: 3
Limpos: 10
Erros: 2

URLs VULNERÁVEIS:
  ├─ https://example.com/?q=FUZZ
  │  └─ HTTP Body: 2 reflexão(ões)
  │  └─ DOM (input_value)
  │  └─ DOM (script)
```

## 📋 Formato do Relatório JSON

```json
{
  "summary": {
    "total_tested": 15,
    "reflected": 3,
    "clean": 10,
    "errors": 2
  },
  "reflected_urls": [
    {
      "url": "https://example.com/?q=search_term",
      "status": "reflected",
      "response_code": 200,
      "reflections": [
        {
          "type": "direct",
          "count": 2,
          "payload": "abc123random"
        }
      ],
      "dom_reflections": [
        {
          "context": "input_value",
          "payload": "abc123random",
          "element": "<input type=\"text\" value=\"abc123random\">"
        }
      ]
    }
  ]
}
```

## 📚 Contextos DOM Suportados

| Contexto | Descrição | Exemplo |
|----------|-----------|---------|
| `input_value` | Valores de campos input | `<input value="payload">` |
| `textarea` | Conteúdo de textarea | `<textarea>payload</textarea>` |
| `script` | Dentro de tags script | `<script>var x="payload"</script>` |
| `href` | Atributos href de links | `<a href="/page?q=payload">` |
| `src` | Atributos src | `<img src="/img?name=payload">` |
| `onclick` | Event handlers | `<div onclick="func('payload')">` |
| `text_content` | Texto direto no HTML | `<p>Resultado: payload</p>` |

## ⚖️ Disclaimer

Esta ferramenta é destinada apenas para uso autorizado.
---

OBS: O README.md foi feito pelo Claude 😂
