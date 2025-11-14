"""
Estilo CSS unificado para todo o projeto de extração bancária.
Remove modo escuro/claro e cria interface consistente.
"""

def obter_css_unificado():
    """Retorna CSS unificado para toda a aplicação."""
    return """
    <style>
    /* ===== RESET E BASE ===== */
    * {
        box-sizing: border-box;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* ===== CORES PRINCIPAIS ===== */
    :root {
        --cor-primaria: #2E86AB;
        --cor-secundaria: #A23B72;
        --cor-sucesso: #28a745;
        --cor-erro: #dc3545;
        --cor-aviso: #ffc107;
        --cor-info: #17a2b8;
        --cor-fundo: #f8f9fa;
        --cor-texto: #212529;
        --cor-borda: #dee2e6;
        --sombra-leve: 0 2px 4px rgba(0,0,0,0.1);
        --sombra-media: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* ===== CARDS UNIVERSAIS ===== */
    .card-base {
        background: white;
        border: 1px solid var(--cor-borda);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: var(--sombra-leve);
        transition: all 0.3s ease;
    }
    
    .card-base:hover {
        box-shadow: var(--sombra-media);
        transform: translateY(-2px);
    }
    
    /* ===== CARDS ESPECÍFICOS ===== */
    .card-credito {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
        border-left: 5px solid var(--cor-sucesso);
    }
    
    .card-debito {
        background: linear-gradient(135deg, #ffeaea 0%, #fff2f2 100%);
        border-left: 5px solid var(--cor-erro);
    }
    
    .card-receita {
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
        border-left: 5px solid var(--cor-primaria);
    }
    
    .card-despesa {
        background: linear-gradient(135deg, #fce4ec 0%, #fff0f5 100%);
        border-left: 5px solid var(--cor-secundaria);
    }
    
    .card-resultado {
        background: linear-gradient(135deg, #fff8e1 0%, #fffef7 100%);
        border-left: 5px solid var(--cor-aviso);
    }
    
    /* ===== MÉTRICAS ===== */
    .metrica-valor {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 8px 0;
    }
    
    .metrica-label {
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.8;
    }
    
    .metrica-credito .metrica-valor { color: var(--cor-sucesso); }
    .metrica-debito .metrica-valor { color: var(--cor-erro); }
    .metrica-receita .metrica-valor { color: var(--cor-primaria); }
    .metrica-despesa .metrica-valor { color: var(--cor-secundaria); }
    
    /* ===== CATEGORIAS ===== */
    .categoria-item {
        background: white;
        border: 1px solid var(--cor-borda);
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: var(--sombra-leve);
        transition: all 0.2s ease;
    }
    
    .categoria-item:hover {
        box-shadow: var(--sombra-media);
    }
    
    .categoria-titulo {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0 0 8px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .categoria-valor {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 4px 0;
    }
    
    .categoria-detalhes {
        font-size: 0.9rem;
        color: #666;
        margin: 4px 0 0 0;
    }
    
    /* ===== CORES POR CATEGORIA ===== */
    .cat-aluguel { border-left: 4px solid #8B4513; }
    .cat-luz { border-left: 4px solid #FFD700; }
    .cat-fisioterapeutas { border-left: 4px solid #20B2AA; }
    .cat-limpeza { border-left: 4px solid #9370DB; }
    .cat-diversos { border-left: 4px solid #708090; }
    .cat-retirada { border-left: 4px solid #DC143C; }
    .cat-cartao { border-left: 4px solid #4169E1; }
    .cat-particular { border-left: 4px solid #32CD32; }
    
    /* ===== NAVEGAÇÃO ===== */
    .nav-button {
        background: white;
        border: 2px solid var(--cor-primaria);
        border-radius: 8px;
        padding: 12px 20px;
        margin: 8px 0;
        color: var(--cor-primaria);
        font-weight: 600;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        width: 100%;
    }
    
    .nav-button:hover {
        background: var(--cor-primaria);
        color: white;
        transform: translateX(4px);
    }
    
    .nav-button.active {
        background: var(--cor-primaria);
        color: white;
        box-shadow: var(--sombra-media);
    }
    
    /* ===== BOTÕES ===== */
    .btn-primary {
        background: linear-gradient(135deg, var(--cor-primaria) 0%, #1e6091 100%);
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: var(--sombra-media);
    }
    
    .btn-success {
        background: linear-gradient(135deg, var(--cor-sucesso) 0%, #1e7e34 100%);
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        color: white;
        font-weight: 600;
    }
    
    .btn-danger {
        background: linear-gradient(135deg, var(--cor-erro) 0%, #c82333 100%);
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        color: white;
        font-weight: 600;
    }
    
    /* ===== GRÁFICOS CUSTOMIZADOS ===== */
    .grafico-barra {
        background: var(--cor-fundo);
        border-radius: 8px;
        padding: 4px;
        margin: 8px 0;
        overflow: hidden;
    }
    
    .barra-credito {
        background: linear-gradient(90deg, var(--cor-sucesso) 0%, #34ce57 100%);
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        font-weight: 600;
        min-width: 60px;
    }
    
    .barra-debito {
        background: linear-gradient(90deg, var(--cor-erro) 0%, #e74c3c 100%);
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        font-weight: 600;
        min-width: 60px;
    }
    
    /* ===== ALERTAS E NOTIFICAÇÕES ===== */
    .alerta-sucesso {
        background: linear-gradient(135deg, #d4edda 0%, #e8f5e8 100%);
        border: 1px solid var(--cor-sucesso);
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        color: #155724;
    }
    
    .alerta-erro {
        background: linear-gradient(135deg, #f8d7da 0%, #ffeaea 100%);
        border: 1px solid var(--cor-erro);
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        color: #721c24;
    }
    
    .alerta-info {
        background: linear-gradient(135deg, #d1ecf1 0%, #e3f2fd 100%);
        border: 1px solid var(--cor-info);
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        color: #0c5460;
    }
    
    /* ===== TABELAS ===== */
    .tabela-customizada {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--sombra-leve);
        margin: 20px 0;
    }
    
    .tabela-customizada thead {
        background: var(--cor-primaria);
        color: white;
    }
    
    .tabela-customizada th {
        padding: 16px;
        font-weight: 600;
        text-align: left;
    }
    
    .tabela-customizada td {
        padding: 12px 16px;
        border-bottom: 1px solid var(--cor-borda);
    }
    
    .tabela-customizada tr:hover {
        background: var(--cor-fundo);
    }
    
    /* ===== SIDEBAR ===== */
    .sidebar .sidebar-content {
        background: white;
        padding: 20px;
    }
    
    /* ===== RESPONSIVIDADE ===== */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        
        .categoria-item {
            padding: 12px;
        }
        
        .metrica-valor {
            font-size: 1.4rem;
        }
    }
    
    /* ===== ANIMAÇÕES ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* ===== UTILITÁRIOS ===== */
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .mb-0 { margin-bottom: 0; }
    .mt-0 { margin-top: 0; }
    .p-0 { padding: 0; }
    .rounded { border-radius: 8px; }
    .shadow { box-shadow: var(--sombra-leve); }
    .shadow-lg { box-shadow: var(--sombra-media); }
    
    </style>
    """

def aplicar_estilo_pagina(st):
    """Aplica o estilo unificado na página atual."""
    st.markdown(obter_css_unificado(), unsafe_allow_html=True)

def card_categoria(categoria, valor, quantidade, media, tipo="despesa"):
    """Gera HTML para card de categoria."""
    cores = {
        "Aluguel": "#8B4513",
        "Luz": "#FFD700", 
        "Fisioterapeutas": "#20B2AA",
        "Limpeza": "#9370DB",
        "Diversos": "#708090",
        "Retirada": "#DC143C",
        "Cartão de Crédito": "#4169E1",
        "Particular": "#32CD32"
    }
    
    cor = cores.get(categoria, "#708090")
    
    return f"""
    <div class="categoria-item" style="border-left: 4px solid {cor};">
        <div class="categoria-titulo" style="color: {cor};">
            {categoria}
        </div>
        <div class="categoria-valor" style="color: {cor};">
            R$ {valor:,.2f}
        </div>
        <div class="categoria-detalhes">
            {quantidade} transações
        </div>
    </div>
    """

def metrica_customizada(label, valor, tipo="neutro"):
    """Gera HTML para métrica customizada."""
    classes = {
        "credito": "metrica-credito",
        "debito": "metrica-debito", 
        "receita": "metrica-receita",
        "despesa": "metrica-despesa",
        "neutro": ""
    }
    
    return f"""
    <div class="card-base {classes.get(tipo, '')}">
        <div class="metrica-label">{label}</div>
        <div class="metrica-valor">{valor}</div>
    </div>
    """
