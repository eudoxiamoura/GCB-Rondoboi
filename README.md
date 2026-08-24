# Calculadora de Custos de Bovinos

Sistema web (Flask + SQLite) para substituir a planilha de controle de custos de gado.
Permite cadastrar lotes de animais, lançar compras e vendas, calcular custo médio por
cabeça, sobra e lucro (bruto, por cabeça e líquido), simular vendas antes de confirmar,
e transferir sobras entre lotes.

## Como rodar localmente

Pré-requisito: Python 3.9+ instalado.

```bash
# 1. Entrar na pasta do projeto
cd /Users/eudoxiamoura/Documents/romaneio

# 2. Ativar o ambiente virtual (já criado)
source venv/bin/activate

# 3. Instalar dependências (se ainda não instaladas)
pip install -r requirements.txt

# 4. Rodar o servidor
python run.py
```

O banco de dados SQLite (`instance/bovinos.db`) é criado automaticamente na primeira
execução — não é preciso rodar nenhum comando de migração.

Depois de iniciar, acesse **http://127.0.0.1:5000** no navegador. O sistema exige
login — veja abaixo como criar o primeiro usuário.

Para parar o servidor, pressione `Ctrl+C` no terminal.

### Criando o ambiente do zero (caso a pasta `venv/` não exista)

```bash
python3 -m venv venv
source venv/bin/activate
pip install Flask Flask-SQLAlchemy Flask-Login
pip freeze > requirements.txt
```

## Login

O sistema exige autenticação — todas as telas de lotes, compras e vendas ficam
atrás de uma tela de login (`/login`).

Há duas formas de criar um usuário:

- **Pela interface:** acesse `/registrar` (tem um link "Criar conta" na tela de
  login). Informe usuário, senha e confirmação — a conta já entra logada ao ser
  criada.
- **Pela linha de comando** (útil para o primeiro acesso em um servidor sem
  interface, ou para redefinir a senha de alguém):

  ```bash
  source venv/bin/activate
  FLASK_APP=run.py flask create-user
  ```

  O comando pede um usuário e uma senha (a senha fica com o eco desligado no
  terminal). Rodar de novo com o mesmo usuário redefine a senha dele.

Nenhuma credencial fica fixa no código.

## Glossário (planilha → sistema)

| Termo na planilha antiga | Termo no sistema |
|---|---|
| Bloco "013 - MACHOS - MARÇO" | Lote |
| TIPO = C | Compra |
| TIPO = V | Venda |
| TIPO = S | Sobra transferida |
| QUEM (compra) | Fornecedor |
| QUEM (venda) | Comprador |
| CUSTANDO / MÉDIA | Custo médio por cabeça |
| SOBRA | Sobra (cabeças não vendidas) |
| LUCRO | Lucro bruto |
| LUCRO POS DESPESAS | Lucro líquido |
| Total de Lucro Parceria | Divisão do lucro (parceria) |

## Fluxo de uso

1. Criar um **lote** novo — o número é gerado automaticamente (001, 002, 003...)
   e a data de abertura é a data de hoje; só é preciso preencher a descrição
   (opcional, pode ficar em branco e ser editada depois). O percentual de
   parceria começa em 50% e só é ajustado depois, em "Editar lote", se for
   diferente disso.
2. Lançar as **compras** do lote (uma por fornecedor/data).
3. O sistema calcula automaticamente o custo médio por cabeça.
4. Lançar as **vendas** conforme forem acontecendo (uma por comprador/data).
5. O resumo do lote mostra sobra, custo da sobra, lucro bruto, lucro por cabeça,
   lucro líquido e a divisão da parceria — atualizados em tempo real.
6. Antes de confirmar uma venda, use **"Simular venda"** para ver o resultado sem
   gravar nada.
7. Use **"Duplicar como rascunho"** para copiar um lote inteiro e testar cenários
   sem alterar os dados originais.
8. Quando sobrarem cabeças de um lote, use **"Transferir sobra"** para criar um
   lote novo com essas cabeças. Você informa um valor por cabeça (quanto elas
   estão "custando" na hora da transferência): esse valor é lançado como uma
   venda no lote de origem — fechando o lucro dele — e vira o custo de entrada
   das cabeças no lote novo. Esse lançamento aparece destacado (com a etiqueta
   "transferência") na lista de vendas do lote de origem.

## Regras de cálculo

Implementadas em [app/calculos.py](app/calculos.py), separadas das rotas para
facilitar testes e ajustes futuros:

- Custo médio por cabeça = custo total do lote ÷ total de cabeças compradas
- Sobra = total comprado − total vendido
- Custo da sobra = sobra × custo médio por cabeça (mostra "—" quando sobra é 0)
- Lucro bruto = receita total das vendas − custo total do lote
- Lucro por cabeça = lucro bruto ÷ total de cabeças vendidas
- Lucro líquido = lucro bruto − despesas extras do lote
- Divisão da parceria = lucro líquido × percentual de parceria (padrão 50%)

## Estrutura do projeto

```
romaneio/
├── app/
│   ├── __init__.py        # factory da aplicação, filtro "brl", login manager, CLI
│   ├── models.py          # User, Lote, Compra, Venda, SobraTransferida
│   ├── calculos.py        # regras de cálculo (custo médio, sobra, lucro...)
│   ├── routes/
│   │   ├── auth.py        # login/logout
│   │   ├── lotes.py       # criar/ver/editar lote, duplicar, transferir sobra
│   │   ├── compras.py     # lançar/excluir compra
│   │   └── vendas.py      # lançar/excluir venda, simular venda
│   ├── templates/
│   └── static/css/
├── instance/               # banco SQLite (criado automaticamente, fora do git)
├── requirements.txt
├── run.py
├── config.py
└── README.md
```

## Melhorias futuras

- Exportar relatório do lote em PDF ou Excel
- Gráficos de lucro por lote ao longo do tempo
- Histórico e busca de lotes anteriores por fornecedor/comprador
- Edição de compras/vendas já lançadas (hoje só é possível excluir e relançar)
- Testes automatizados para `app/calculos.py`
