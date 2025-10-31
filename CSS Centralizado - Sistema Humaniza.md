# CSS Centralizado - Sistema Humaniza

## 📁 Estrutura de Arquivos

```
extrator_bancario/
├── styles.css              ← Arquivo CSS centralizado
├── utils_css.py            ← Utilitário para carregar CSS
├── app.py                  ← Importa utils_css
├── pagina_despesas.py
├── pagina_receitas_simples.py
├── pagina_resultado.py
└── ...
```

---

## 🎨 Arquivo: `styles.css`

Contém **todos** os estilos do sistema:

### Seções:
1. **Variáveis CSS** - Paleta de cores
2. **Métricas e Cards** - Estilos de débitos/créditos
3. **Saldos** - Positivos e negativos
4. **Categorias** - Cards de categorias
5. **Navegação** - Links e botões
6. **Componentes Streamlit** - Sidebar, botões, expanders
7. **Cards Customizados** - HTML inline
8. **Dark Mode** - Tema escuro

### Paleta de Cores:
```css
:root {
    --sage-principal: #849585;
    --sage-escuro: #6B7A6C;
    --sage-claro: #A8B5A9;
    --sage-muito-claro: #E8EBE8;
    --sage-fundo: #F5F6F5;
}
```

---

## 🔧 Arquivo: `utils_css.py`

Módulo utilitário com 2 funções:

### 1. `carregar_css()`
Lê o arquivo `styles.css` e injeta no Streamlit.

```python
from utils_css import carregar_css

def configurar_pagina():
    st.set_page_config(...)
    carregar_css()  # ← Carrega CSS
```

### 2. `aplicar_dark_mode()`
Aplica classe CSS para tema escuro (futuro).

---

## 📝 Como Usar

### No `app.py`:

```python
def configurar_pagina():
    """Configurações gerais da página."""
    st.set_page_config(
        page_title="Humaniza - Gestão Financeira", 
        page_icon="🦋", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Carregar CSS centralizado
    from utils_css import carregar_css
    carregar_css()
```

### Nas páginas individuais:

**Não precisa fazer nada!** O CSS é carregado automaticamente pelo `app.py`.

---

## ✨ Vantagens

### 1. **Manutenção Centralizada**
- Alterar uma cor: editar **1 arquivo** (styles.css)
- Antes: editar 4+ arquivos

### 2. **Consistência Visual**
- Todas as páginas usam o mesmo CSS
- Sem duplicação de código

### 3. **Fácil Personalização**
- Editar `styles.css` com editor de texto
- Não precisa mexer no código Python

### 4. **Variáveis CSS**
- Usar `var(--sage-principal)` no CSS
- Mudar a cor principal: alterar **1 linha**

### 5. **Organização**
- CSS separado do Python
- Código mais limpo e legível

---

## 🎨 Exemplo de Uso no HTML Inline

### Antes (cores hardcoded):
```python
st.markdown(f"""
<div style="background-color: #F5F6F5; border-left: 4px solid #849585;">
    <h4 style="color: #849585;">{categoria}</h4>
</div>
""", unsafe_allow_html=True)
```

### Agora (usando classes CSS):
```python
st.markdown(f"""
<div class="card-despesa">
    <h4>{categoria}</h4>
</div>
""", unsafe_allow_html=True)
```

**Benefício:** Se mudar a cor no `styles.css`, todos os cards atualizam automaticamente!

---

## 🔄 Como Alterar as Cores

### 1. Abrir `styles.css`

### 2. Editar as variáveis:
```css
:root {
    --sage-principal: #849585;  ← Mudar aqui
    --sage-escuro: #6B7A6C;     ← E aqui
    --sage-claro: #A8B5A9;
    --sage-muito-claro: #E8EBE8;
    --sage-fundo: #F5F6F5;
}
```

### 3. Salvar e recarregar o Streamlit

**Todas as páginas atualizam automaticamente!**

---

## 🌙 Dark Mode (Preparado)

O arquivo CSS já tem suporte para dark mode:

```css
.dark-mode {
    --sage-fundo: #2C3531;
    --sage-muito-claro: #3E4A47;
    /* ... */
}
```

Para ativar:
1. Usuário clica no toggle "Modo Escuro"
2. `st.session_state.dark_mode = True`
3. `aplicar_dark_mode()` adiciona classe `.dark-mode`
4. CSS aplica cores escuras

---

## 📋 Checklist de Instalação

- [ ] Arquivo `styles.css` no diretório do projeto
- [ ] Arquivo `utils_css.py` no diretório do projeto
- [ ] `app.py` importa `carregar_css()`
- [ ] Páginas individuais **não** têm CSS inline duplicado
- [ ] Testar: cores aplicadas corretamente
- [ ] Testar: alterar cor no CSS e verificar mudança

---

## 🚀 Próximos Passos (Opcional)

1. **Migrar HTML inline para classes CSS**
   - Trocar `style="..."` por `class="card-despesa"`
   - Mais limpo e manutenível

2. **Adicionar mais variáveis**
   - `--border-radius-card: 8px;`
   - `--padding-card: 15px;`

3. **Criar temas alternativos**
   - `styles-dark.css`
   - `styles-light.css`
   - Trocar dinamicamente

4. **Minificar CSS para produção**
   - Remover espaços e comentários
   - Melhor performance

---

## ❓ Solução de Problemas

### CSS não carrega
**Solução:** Verificar se `styles.css` está no mesmo diretório que `app.py`

### Cores não mudam
**Solução:** 
1. Limpar cache do Streamlit
2. Recarregar página (F5)
3. Verificar se `carregar_css()` está sendo chamado

### Erro "FileNotFoundError"
**Solução:** Caminho do CSS incorreto. Verificar `utils_css.py` linha 14.

---

**Status:** ✅ CSS Centralizado Implementado

Agora você pode gerenciar todos os estilos em um único arquivo! 🎨

