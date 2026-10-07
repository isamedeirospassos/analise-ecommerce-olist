from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# 1. LOCALIZA AS PASTAS DO PROJETO
pasta_projeto = Path(__file__).resolve().parent
pasta_dados = pasta_projeto / "dados"
pasta_resultados = pasta_projeto / "resultados"

pasta_resultados.mkdir(exist_ok=True)


# 2. CARREGA A TABELA DE PEDIDOS
arquivo = pasta_dados / "olist_orders_dataset.csv"
pedidos = pd.read_csv(arquivo)


# 3. EXPLORA OS DADOS
print("PRIMEIROS 5 PEDIDOS")
print(pedidos.head().to_string(index=False))

print("\nTAMANHO DA TABELA")
print(f"Linhas: {pedidos.shape[0]:,}")
print(f"Colunas: {pedidos.shape[1]}")

print("\nCOLUNAS E TIPOS ORIGINAIS DOS DADOS")
pedidos.info()

print("\nVALORES AUSENTES POR COLUNA")
print(pedidos.isna().sum())

print("\nQUANTIDADE DE PEDIDOS POR STATUS")
print(pedidos["order_status"].value_counts())

duplicados = pedidos["order_id"].duplicated().sum()
print(f"\nIDs de pedidos repetidos: {duplicados}")


# 4. PREPARA AS DATAS
# Interrompe a execução se encontrar uma data inválida.
pedidos["order_purchase_timestamp"] = pd.to_datetime(
    pedidos["order_purchase_timestamp"],
    errors="raise"
)

# Extrai o ano e o mês de cada compra.
pedidos["mes_compra"] = (
    pedidos["order_purchase_timestamp"].dt.to_period("M")
)


# 5. CONTA OS PEDIDOS POR MÊS
# Inclui todos os status, inclusive pedidos cancelados.
pedidos_por_mes = (
    pedidos.groupby("mes_compra")["order_id"]
    .nunique()
    .sort_index()
)

# Cria uma sequência completa do primeiro ao último mês.
meses = pd.period_range(
    start=pedidos_por_mes.index.min(),
    end=pedidos_por_mes.index.max(),
    freq="M"
)

# Zero significa que não há pedidos registrados naquele mês na base.
serie_mensal = pedidos_por_mes.reindex(meses, fill_value=0)
serie_mensal.index.name = "mes_compra"
serie_mensal.name = "quantidade_pedidos"

print("\nPEDIDOS POR MÊS — TODOS OS STATUS")
print(serie_mensal)


# 6. SALVA A TABELA MENSAL
caminho_tabela = pasta_resultados / "pedidos_por_mes.csv"

serie_mensal.to_csv(
    caminho_tabela,
    index_label="mes_compra",
    header=["quantidade_pedidos"],
    encoding="utf-8-sig",
    sep=";"
)

print(f"\nTabela salva em: {caminho_tabela}")


# 7. CRIA O GRÁFICO
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    serie_mensal.index.to_timestamp(),
    serie_mensal.values,
    color="#2563EB",
    marker="o",
    linewidth=2
)

ax.set_title(
    "Evolução mensal dos pedidos — Olist",
    fontsize=16,
    fontweight="bold",
    pad=15
)

ax.set_xlabel("Mês da compra")
ax.set_ylabel("Quantidade de pedidos")
ax.set_ylim(bottom=0)

# Formata os milhares com ponto: 1.000, 2.000 etc.
ax.yaxis.set_major_formatter(
    FuncFormatter(
        lambda valor, posicao: f"{valor:,.0f}".replace(",", ".")
    )
)

ax.set_xticks(serie_mensal.index.to_timestamp())
ax.set_xticklabels(
    serie_mensal.index.astype(str),
    rotation=60,
    ha="right"
)

ax.grid(axis="y", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(
    0.02,
    0.02,
    "Fonte: Olist / Kaggle | Todos os status. "
    "Meses nas extremidades podem ter cobertura parcial.",
    fontsize=9,
    color="#555555"
)

fig.tight_layout(rect=[0, 0.07, 1, 1])


# 8. SALVA E EXIBE O GRÁFICO
caminho_grafico = pasta_resultados / "pedidos_por_mes.png"

fig.savefig(
    caminho_grafico,
    dpi=200,
    bbox_inches="tight"
)

print(f"\nGráfico salvo em: {caminho_grafico}")

plt.show()
plt.close(fig)

# 9. CARREGA A TABELA DE CLIENTES
clientes = pd.read_csv(
    pasta_dados / "olist_customers_dataset.csv"
)

# Acrescenta o estado do cliente a cada pedido.
# "left" mantém todos os pedidos.
# A validação exige um único cliente por customer_id na tabela de clientes.
pedidos_clientes = pedidos.merge(
    clientes[["customer_id", "customer_state"]],
    on="customer_id",
    how="left",
    validate="many_to_one"
)

sem_estado = pedidos_clientes["customer_state"].isna().sum()
print(f"\nPedidos sem estado identificado: {sem_estado}")


# 10. CONTA OS PEDIDOS POR ESTADO
pedidos_por_estado = (
    pedidos_clientes
    .groupby("customer_state", dropna=False)["order_id"]
    .nunique()
    .sort_values(ascending=False)
)

print("\nPEDIDOS POR ESTADO — TODOS OS STATUS")
print(pedidos_por_estado)

pedidos_por_estado.to_csv(
    pasta_resultados / "pedidos_por_estado.csv",
    index_label="estado",
    header=["quantidade_pedidos"],
    encoding="utf-8-sig",
    sep=";"
)

# 11. GRÁFICO DOS 10 ESTADOS COM MAIS PEDIDOS
# Seleciona os maiores e organiza para o gráfico horizontal.
top_10_estados = pedidos_por_estado.head(10).sort_values()

fig, ax = plt.subplots(figsize=(10, 6))

barras = ax.barh(
    top_10_estados.index,
    top_10_estados.values,
    color="#2563EB"
)

# Escreve a quantidade ao lado de cada barra.
rotulos = [
    f"{valor:,.0f}".replace(",", ".")
    for valor in top_10_estados.values
]
ax.bar_label(barras, labels=rotulos, padding=5)

ax.set_title(
    "10 estados com mais pedidos — Olist",
    fontsize=16,
    fontweight="bold",
    pad=15
)
ax.set_xlabel("Quantidade de pedidos")
ax.set_ylabel("Estado do cliente")

# Reserva espaço para os números ao lado das barras.
ax.set_xlim(0, top_10_estados.max() * 1.18)

ax.xaxis.set_major_formatter(
    FuncFormatter(
        lambda valor, posicao: f"{valor:,.0f}".replace(",", ".")
    )
)

ax.set_axisbelow(True)
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(
    0.02,
    0.02,
    "Fonte: Olist / Kaggle | Todos os status, incluindo cancelados.",
    fontsize=9,
    color="#555555"
)

fig.tight_layout(rect=[0, 0.06, 1, 1])

caminho_grafico_estados = pasta_resultados / "pedidos_por_estado.png"
fig.savefig(caminho_grafico_estados, dpi=200, bbox_inches="tight")

print(f"\nGráfico salvo em: {caminho_grafico_estados}")

plt.show()
plt.close(fig)

# 12. CARREGA OS ITENS DOS PEDIDOS E OS PRODUTOS
itens = pd.read_csv(
    pasta_dados / "olist_order_items_dataset.csv"
)

produtos = pd.read_csv(
    pasta_dados / "olist_products_dataset.csv"
)

# Cada linha de itens representa um item de um pedido.
# Um pedido pode ter vários itens.
print(f"\nItens carregados: {len(itens):,}")
print(f"Produtos carregados: {len(produtos):,}")


# 13. SELECIONA APENAS PEDIDOS ENTREGUES
pedidos_entregues = pedidos.loc[
    pedidos["order_status"] == "delivered",
    ["order_id"]
]

# Mantém apenas os itens que pertencem a pedidos entregues.
itens_entregues = itens.merge(
    pedidos_entregues,
    on="order_id",
    how="inner",
    validate="many_to_one"
)

# Acrescenta a categoria de cada produto.
itens_categorias = itens_entregues.merge(
    produtos[["product_id", "product_category_name"]],
    on="product_id",
    how="left",
    validate="many_to_one"
)

# Preserva os itens sem categoria para não perder seus valores.
sem_categoria = itens_categorias["product_category_name"].isna().sum()
print(f"Itens entregues sem categoria: {sem_categoria}")

itens_categorias["product_category_name"] = (
    itens_categorias["product_category_name"]
    .fillna("sem_categoria")
)


# 14. SOMA O VALOR DOS PRODUTOS POR CATEGORIA
valor_por_categoria = (
    itens_categorias.groupby("product_category_name")["price"]
    .sum()
    .sort_values(ascending=False)
)

# Função para exibir valores em reais.
def formatar_reais(valor):
    numero = f"{valor:,.2f}"
    numero = numero.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {numero}"


print("\nTOP 10 CATEGORIAS — VALOR DOS PRODUTOS ENTREGUES")
print(valor_por_categoria.head(10).apply(formatar_reais))

print(
    "\nValor total dos produtos em pedidos entregues:",
    formatar_reais(valor_por_categoria.sum())
)

# Mantém os valores numéricos no CSV.
valor_por_categoria.to_csv(
    pasta_resultados / "valor_por_categoria.csv",
    index_label="categoria",
    header=["valor_produtos_entregues"],
    encoding="utf-8-sig",
    sep=";",
    decimal=",",
    float_format="%.2f"
)


# 15. CRIA O GRÁFICO DAS 10 MAIORES CATEGORIAS
top_categorias = valor_por_categoria.head(10).sort_values()

fig, ax = plt.subplots(figsize=(12, 7))

nomes = top_categorias.index.str.replace("_", " ")

barras = ax.barh(
    nomes,
    top_categorias.values,
    color="#059669"
)

ax.bar_label(
    barras,
    labels=[formatar_reais(valor) for valor in top_categorias.values],
    padding=5,
    fontsize=9
)

ax.set_title(
    "Top 10 categorias por valor dos produtos — Olist",
    fontsize=15,
    fontweight="bold",
    pad=15
)
ax.set_xlabel("Valor dos produtos (R$)")
ax.set_ylabel("")

ax.set_xlim(0, top_categorias.max() * 1.30)
ax.xaxis.set_major_formatter(
    FuncFormatter(
        lambda valor, posicao: f"{valor:,.0f}".replace(",", ".")
    )
)

ax.set_axisbelow(True)
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(
    0.02,
    0.02,
    "Fonte: Olist / Kaggle | Soma de price. "
    "Somente pedidos entregues; frete excluído.",
    fontsize=9,
    color="#555555"
)

fig.tight_layout(rect=[0, 0.06, 1, 1])

caminho_categorias = pasta_resultados / "valor_por_categoria.png"
fig.savefig(caminho_categorias, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"\nGráfico salvo em: {caminho_categorias}")

# 16. PREPARA AS DATAS DOS PEDIDOS ENTREGUES
entregas = pedidos.loc[
    pedidos["order_status"] == "delivered",
    [
        "order_id",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
].copy()

colunas_datas = [
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for coluna in colunas_datas:
    entregas[coluna] = pd.to_datetime(
        entregas[coluna],
        errors="raise"
    )

sem_datas = entregas[colunas_datas].isna().any(axis=1)

print(
    "\nPedidos entregues excluídos por falta de datas:",
    sem_datas.sum()
)

entregas = entregas.loc[~sem_datas].copy()

# Compara apenas o dia, desconsiderando o horário.
entregas["atrasado"] = (
    entregas["order_delivered_customer_date"].dt.normalize()
    > entregas["order_estimated_delivery_date"].dt.normalize()
)

entregas["situacao_entrega"] = entregas["atrasado"].map({
    False: "No prazo",
    True: "Atrasado"
})

taxa_atraso = entregas["atrasado"].mean() * 100
print(f"Taxa de atraso entre entregas com datas: {taxa_atraso:.2f}%")


# 17. CARREGA AS AVALIAÇÕES
avaliacoes = pd.read_csv(
    pasta_dados / "olist_order_reviews_dataset.csv"
)

# Considera apenas notas válidas de 1 a 5.
avaliacoes_validas = avaliacoes.loc[
    avaliacoes["review_score"].between(1, 5)
]

# Se houver várias avaliações para um pedido, usa sua média.
# Assim, cada pedido terá o mesmo peso na comparação.
nota_por_pedido = (
    avaliacoes_validas.groupby("order_id", as_index=False)
    .agg(nota_media=("review_score", "mean"))
)

entregas_avaliadas = entregas.merge(
    nota_por_pedido,
    on="order_id",
    how="left",
    validate="one_to_one"
)

print(
    "Pedidos com datas, mas sem avaliação válida:",
    entregas_avaliadas["nota_media"].isna().sum()
)


# 18. COMPARA AS NOTAS
comparacao = (
    entregas_avaliadas
    .groupby("situacao_entrega")
    .agg(
        pedidos_com_datas=("order_id", "nunique"),
        pedidos_avaliados=("nota_media", "count"),
        nota_media=("nota_media", "mean")
    )
    .reindex(["No prazo", "Atrasado"])
)

print("\nAVALIAÇÕES POR SITUAÇÃO DA ENTREGA")
print(comparacao.round(2).to_string())

comparacao.to_csv(
    pasta_resultados / "avaliacoes_por_entrega.csv",
    encoding="utf-8-sig",
    sep=";",
    decimal=",",
    float_format="%.2f"
)


# 19. CRIA O GRÁFICO
fig, ax = plt.subplots(figsize=(8, 5))

barras = ax.bar(
    comparacao.index,
    comparacao["nota_media"],
    color=["#059669", "#DC2626"]
)

rotulos = [
    f"{nota:.2f}".replace(".", ",")
    for nota in comparacao["nota_media"]
]

ax.bar_label(barras, labels=rotulos, padding=5)
ax.set_ylim(0, 5.5)
ax.set_yticks([0, 1, 2, 3, 4, 5])
ax.set_ylabel("Nota média (avaliações de 1 a 5)")
ax.set_title("Avaliação dos pedidos por situação da entrega")

ax.set_axisbelow(True)
ax.grid(axis="y", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(
    0.02,
    0.02,
    "Fonte: Olist / Kaggle | Pedidos entregues com datas e notas válidas.\n"
    "Cada pedido tem o mesmo peso. Comparação não demonstra causalidade.",
    fontsize=9,
    color="#555555"
)

fig.tight_layout(rect=[0, 0.10, 1, 1])

caminho_avaliacoes = pasta_resultados / "avaliacoes_por_entrega.png"
fig.savefig(caminho_avaliacoes, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"\nGráfico salvo em: {caminho_avaliacoes}")