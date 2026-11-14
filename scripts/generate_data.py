"""Parte 2.2: Gerador vetorizado e reprodutivel do dataset E-Commerce B2C (~6,25M linhas)."""

from __future__ import annotations

import random
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import DATA_DIR

SEED = 42
N_CLIENTES = 200_000
N_CLIENTES_COM_PEDIDO = 190_000  # 10.000 clientes sem pedidos para validar Q10
N_PRODUTOS = 50_000
N_PEDIDOS = 1_500_000
N_ITENS = 4_500_000

CHUNK_SIZE = 250_000

NOMES_PROPRIOS = np.array(
    [
        "Ana", "Bruno", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena",
        "Igor", "Juliana", "Lucas", "Mariana", "Nicolas", "Olivia", "Pedro", "Rafael",
        "Sofia", "Thiago", "Vanessa", "Vitor", "João", "José", "André", "Cláudia",
        "Fábio", "Lúcia", "Márcio", "Patrícia", "Renato", "Sônia",
    ]
)

SOBRENOMES = np.array(
    [
        "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Rodrigues",
        "Almeida", "Nascimento", "Lima", "Araújo", "Fernandes", "Carvalho", "Gomes",
        "Martins", "Rocha", "Ribeiro", "Alves", "Monteiro", "Mendes",
    ]
)

CIDADES_ESTADOS = [
    ("Teresina", "PI"), ("Picos", "PI"), ("Parnaíba", "PI"), ("Floriano", "PI"),
    ("São Paulo", "SP"), ("Campinas", "SP"), ("Rio de Janeiro", "RJ"), ("Niterói", "RJ"),
    ("Belo Horizonte", "MG"), ("Uberlândia", "MG"), ("Curitiba", "PR"), ("Londrina", "PR"),
    ("Porto Alegre", "RS"), ("Florianópolis", "SC"), ("Salvador", "BA"), ("Fortaleza", "CE"),
    ("Recife", "PE"), ("São Luís", "MA"), ("Brasília", "DF"), ("Goiânia", "GO"),
    ("Belém", "PA"), ("Manaus", "AM"), ("Vitória", "ES"), ("João Pessoa", "PB"),
]

PREFIXOS_PRODUTOS = np.array(
    [
        "Notebook", "Smartphone", "Monitor", "Teclado", "Mouse", "Headset",
        "Impressora", "Roteador", "Tablet", "Cadeira", "Mesa", "Webcam",
        "Microfone", "SSD", "Memória", "Placa", "Fonte", "Gabinete",
        "Carregador", "Mochila", "Suporte", "Smartwatch", "Caixa", "Hub",
    ]
)

MODELOS_PRODUTOS = np.array(
    [
        "Pro", "Ultra", "Plus", "Lite", "Max", "Studio", "Office", "Gamer",
        "Essential", "Prime", "Compact", "Slim", "Turbo", "Flex", "Advanced",
    ]
)

CATEGORIAS = np.array(
    [
        "Informática", "Eletrônicos", "Periféricos", "Móveis",
        "Acessórios", "Áudio e Vídeo", "Redes", "Armazenamento",
    ]
)

STATUS_PEDIDO = np.array(["ENTREGUE", "PAGO", "ENVIADO", "PENDENTE", "CANCELADO", "DEVOLVIDO"])
STATUS_PROBS = np.array([0.55, 0.15, 0.12, 0.08, 0.07, 0.03])


def _generate_clientes(rng: np.random.Generator, out_path: Path) -> None:
    """Gera clientes.csv (~200.000 linhas)."""
    ids = np.arange(1, N_CLIENTES + 1, dtype=np.int32)
    first_names = NOMES_PROPRIOS[rng.integers(0, len(NOMES_PROPRIOS), size=N_CLIENTES)]
    last_names_1 = SOBRENOMES[rng.integers(0, len(SOBRENOMES), size=N_CLIENTES)]
    last_names_2 = SOBRENOMES[rng.integers(0, len(SOBRENOMES), size=N_CLIENTES)]

    cidades_arr = np.array([c for c, _ in CIDADES_ESTADOS])
    estados_arr = np.array([uf for _, uf in CIDADES_ESTADOS])
    loc_idx = rng.integers(0, len(CIDADES_ESTADOS), size=N_CLIENTES)

    base_date = date(2020, 1, 1)
    day_offsets = rng.integers(0, 1800, size=N_CLIENTES)
    unique_dates = [(base_date + timedelta(days=d)).isoformat() for d in range(1800)]
    dates_arr = np.array(unique_dates)

    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("ClienteID,Nome,Email,Cidade,Estado,DataCadastro\n")
        for cid, fn, ln1, ln2, l_idx, d_off in zip(
            ids, first_names, last_names_1, last_names_2, loc_idx, day_offsets
        ):
            fh.write(
                f"{cid},{fn} {ln1} {ln2},cliente_{cid:06d}@exemplo.com.br,"
                f"{cidades_arr[l_idx]},{estados_arr[l_idx]},{dates_arr[d_off]}\n"
            )


def _generate_produtos(rng: np.random.Generator, out_path: Path) -> np.ndarray:
    """Gera produtos.csv (~50.000 linhas) e retorna vetor de precos indexado por ProdutoID-1."""
    ids = np.arange(1, N_PRODUTOS + 1, dtype=np.int32)
    prefixes = PREFIXOS_PRODUTOS[rng.integers(0, len(PREFIXOS_PRODUTOS), size=N_PRODUTOS)]
    models = MODELOS_PRODUTOS[rng.integers(0, len(MODELOS_PRODUTOS), size=N_PRODUTOS)]
    cats = CATEGORIAS[rng.integers(0, len(CATEGORIAS), size=N_PRODUTOS)]
    precos = np.round(rng.uniform(29.90, 8999.90, size=N_PRODUTOS), 2)
    estoques = rng.integers(0, 500, size=N_PRODUTOS)

    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("ProdutoID,Nome,Categoria,Preco,Estoque\n")
        for pid, pref, mod, cat, preco, est in zip(ids, prefixes, models, cats, precos, estoques):
            fh.write(f"{pid},{pref} {mod} Serie {pid},{cat},{preco:.2f},{est}\n")

    return precos


def _generate_itens_e_pedidos(
    rng: np.random.Generator,
    precos_produtos: np.ndarray,
    itens_path: Path,
    pedidos_path: Path,
) -> None:
    """Gera itens_pedido.csv (~4.500.000) e pedidos.csv (~1.500.000) com ValorTotal consistente."""
    # Cada pedido recebe de 1 a 5 itens; media ~3 itens totalizando exatamente 4.500.000 itens
    pedido_ids_itens = np.empty(N_ITENS, dtype=np.int32)
    # Primeiros 1.500.000 itens garantem ao menos 1 item por pedido; 3.000.000 distribuidos
    pedido_ids_itens[:N_PEDIDOS] = np.arange(1, N_PEDIDOS + 1, dtype=np.int32)
    pedido_ids_itens[N_PEDIDOS:] = rng.integers(1, N_PEDIDOS + 1, size=N_ITENS - N_PEDIDOS, dtype=np.int32)
    rng.shuffle(pedido_ids_itens)

    produto_ids = rng.integers(1, N_PRODUTOS + 1, size=N_ITENS, dtype=np.int32)
    quantidades = rng.integers(1, 6, size=N_ITENS, dtype=np.int16)
    precos_unit = precos_produtos[produto_ids - 1]
    descontos = rng.choice(np.array([0.0, 5.0, 10.0, 15.0]), size=N_ITENS, p=[0.60, 0.20, 0.15, 0.05])

    subtotais = quantidades * precos_unit * (1.0 - descontos / 100.0)
    totais_pedidos = np.bincount(pedido_ids_itens, weights=subtotais, minlength=N_PEDIDOS + 1)[1:]
    totais_pedidos = np.round(totais_pedidos, 2)

    with itens_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("ItemPedidoID,PedidoID,ProdutoID,Quantidade,PrecoUnitario,Desconto\n")
        for start in range(0, N_ITENS, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE, N_ITENS)
            lines = [
                f"{iid},{ped_id},{prod_id},{qtd},{pu:.2f},{desc:.2f}\n"
                for iid, ped_id, prod_id, qtd, pu, desc in zip(
                    range(start + 1, end + 1),
                    pedido_ids_itens[start:end],
                    produto_ids[start:end],
                    quantidades[start:end],
                    precos_unit[start:end],
                    descontos[start:end],
                )
            ]
            fh.writelines(lines)

    # Agora gera pedidos.csv (~1.500.000 linhas)
    cliente_ids = rng.integers(1, N_CLIENTES_COM_PEDIDO + 1, size=N_PEDIDOS, dtype=np.int32)
    status_arr = rng.choice(STATUS_PEDIDO, size=N_PEDIDOS, p=STATUS_PROBS)

    # Datas de 2022-01-01 00:00:00 ate 2026-10-31 23:59:59 (1765 dias)
    start_ts = np.datetime64("2022-01-01T00:00:00", "s")
    max_seconds = 1765 * 86400
    sec_offsets = rng.integers(0, max_seconds, size=N_PEDIDOS, dtype=np.int64)

    with pedidos_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("PedidoID,ClienteID,DataPedido,Status,ValorTotal\n")
        for start in range(0, N_PEDIDOS, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE, N_PEDIDOS)
            ts_chunk = (start_ts + sec_offsets[start:end].astype("timedelta64[s]")).astype(str)
            lines = [
                f"{pid},{cid},{ts.replace('T', ' ')},{st},{vt:.2f}\n"
                for pid, cid, ts, st, vt in zip(
                    range(start + 1, end + 1),
                    cliente_ids[start:end],
                    ts_chunk,
                    status_arr[start:end],
                    totais_pedidos[start:end],
                )
            ]
            fh.writelines(lines)


def generate_all() -> None:
    """Executa a geracao completa dos 4 CSVs com semente fixa (seed=42)."""
    t0 = time.perf_counter()
    random.seed(SEED)
    np.random.seed(SEED)
    rng = np.random.default_rng(SEED)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    clientes_csv = DATA_DIR / "clientes.csv"
    produtos_csv = DATA_DIR / "produtos.csv"
    pedidos_csv = DATA_DIR / "pedidos.csv"
    itens_csv = DATA_DIR / "itens_pedido.csv"

    print("[1/3] Gerando clientes.csv (200.000 registros)...")
    _generate_clientes(rng, clientes_csv)

    print("[2/3] Gerando produtos.csv (50.000 registros)...")
    precos = _generate_produtos(rng, produtos_csv)

    print("[3/3] Gerando itens_pedido.csv (4.500.000) e pedidos.csv (1.500.000)...")
    _generate_itens_e_pedidos(rng, precos, itens_csv, pedidos_csv)

    elapsed = time.perf_counter() - t0
    total_bytes = sum(p.stat().st_size for p in (clientes_csv, produtos_csv, pedidos_csv, itens_csv))
    print(f"[OK] Geracao concluida em {elapsed:.2f}s | Tamanho total CSVs: {total_bytes / (1024**2):.2f} MiB")
    for p in (clientes_csv, produtos_csv, pedidos_csv, itens_csv):
        print(f"  - {p.name}: {p.stat().st_size / (1024**2):.2f} MiB")


if __name__ == "__main__":
    generate_all()
