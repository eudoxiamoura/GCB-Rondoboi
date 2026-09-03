# Rondoboi - Comércio de Bovinos

Sistema web para controle de custos de lotes de gado: cadastro de lotes (separados
por macho/fêmea), lançamento de compras e vendas, cálculo automático de custo médio
por cabeça, sobra, lucro (bruto, por cabeça e líquido) e divisão de parceria, além de
transferência de sobra entre lotes e simulação de venda antes de confirmar. Também
inclui um módulo de romaneio para pesagem individual de animais.

## Desenvolvido em

- [Python](https://www.python.org/) + [Flask](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) com banco [SQLite](https://www.sqlite.org/)
- [Flask-Login](https://flask-login.readthedocs.io/) para autenticação
- [Bootstrap 5](https://getbootstrap.com/) no front-end
- PWA (manifest + service worker) para instalação em celular
