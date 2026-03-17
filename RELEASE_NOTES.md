# 📋 Notas de Versão — v0.3.0

> **Data:** Março 2026
> **Branch:** `feature/fix-active-recent-filter`
> **PRs incluídos:** [PR #2](https://github.com/IsmaelRDeMelo/apoiase-exporter/pull/2) · [PR #3](https://github.com/IsmaelRDeMelo/apoiase-exporter/pull/3)

---

## ✨ Novidades

### ⚡ Tela de Loading (Splash Screen) — PR #2

O aplicativo levava aproximadamente 20 segundos para abrir sem nenhum feedback visual. Agora exibe uma **tela de carregamento** durante a inicialização:

- Ícone e título do app
- Versão atual (v0.2.0)
- Texto "Carregando..."
- Barra de progresso animada (modo indeterminado)

A janela principal permanece oculta até que o carregamento seja concluído, evitando a exibição de uma interface em branco.

---

### 🔄 Correção: Dashboard não atualizava ao reimportar CSV — PR #2

**Problema:** Ao importar o CSV uma segunda vez (ex: mudando o filtro de dias), o dashboard mostrava os resultados duplicados empilhados na tela, sem substituir os dados anteriores.

**Causa raiz:** O `CTkScrollableFrame` do CustomTkinter não liberava corretamente o espaço no layout ao ser destruído, causando o acúmulo de múltiplos frames.

**Solução:** Adotado o padrão de **frame wrapper persistente** (`_wrapper`). Em cada reimportação, todos os filhos do wrapper são limpos com `pack_forget()` + `place_forget()` + `destroy()` antes de reconstruir o conteúdo.

Essa correção se aplica a:
- Aba **Dashboard** (`dashboard_tab.py`)
- Aba **Buscar** (`search_tab.py`)

---

### 🐛 Correção: Apoiadores Ativos sendo filtrados por data — PR #3

**Problema:** A lista "Apoiadores Ativos Últimos N Dias" estava aplicando o filtro de data **também** aos apoiadores com status `Ativo`, fazendo com que apoiadores antigos (mas ainda ativos) desaparecessem da lista.

**Regra correta:**
- **Ativo** → sempre aparece na lista, independente da data de última mudança
- **Desativado / Inadimplente / Aguardando Confirmação** → aparecem apenas se a `Data da Última Mudança` estiver dentro do período selecionado (N dias)

**Exemplo com filtro de 30 dias:**

| Apoiador | Status | Última mudança | Aparece na lista? |
|---|---|---|---|
| João Silva | Ativo | Jan/2024 (há 2 anos) | ✅ Sim — sempre |
| Maria Souza | Desativado | Há 15 dias | ✅ Sim — dentro do período |
| Carlos Lima | Inadimplente | Há 45 dias | ❌ Não — fora do período |

---

## 🧪 Cobertura de Testes

**89/89 testes passando**

| Módulo | Cobertura |
|---|---|
| `transform_use_case.py` | 99% |
| `models.py` | 100% |
| `name_utils.py` | 100% |
| `csv_reader.py` | 90% |
| Writers (YAML/JSON) | 100% |

---

## 🔧 Arquivos Alterados

### PR #2 — Splash Screen + Dashboard Refresh Fix
| Arquivo | Tipo de alteração |
|---|---|
| `src/gui/app.py` | Adicionado `SplashScreen` + padrão `withdraw`/`deiconify` |
| `src/gui/dashboard_tab.py` | Adotado wrapper persistente para evitar acúmulo de frames |
| `src/gui/search_tab.py` | Mesma correção do wrapper para a aba de busca |

### PR #3 — Correção do Filtro de Apoiadores Ativos Recentes
| Arquivo | Tipo de alteração |
|---|---|
| `src/application/transform_use_case.py` | Lógica `is_ativo or within_period` — Ativo sempre incluso |
| `tests/test_transform_use_case.py` | 5 testes atualizados para refletir a nova regra |
