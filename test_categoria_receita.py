# Teste rápido
from categorizador_receitas_simples import CategorizadorReceitasSimples
cat = CategorizadorReceitasSimples()

# Testar com nomes que deveriam ser manuais
nomes_teste = ['ALESSANDRA CRISTINE VAZ SANTOS', 'FELIPE CUNHA MATOS']
for nome in nomes_teste:
    resultado = cat._aplicar_regras_categorizacao(nome)
    print(f"{nome}: {resultado['tipo_preenchimento']}")
