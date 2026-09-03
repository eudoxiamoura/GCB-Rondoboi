# Deploy em VPS (Ubuntu/Debian)

Arquivos de referência usados para colocar o sistema em produção via
gunicorn + nginx + systemd, com acesso só por IP (sem domínio/HTTPS ainda).

Em produção o sistema usa Postgres (banco de verdade, mais seguro pra manter
os dados). Em desenvolvimento local continua usando SQLite normalmente — não
precisa instalar Postgres na sua máquina, só no servidor.

## 1. Instalar dependências do sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git nginx postgresql
```

## 2. Clonar o projeto e instalar as dependências Python

```bash
cd ~
git clone https://github.com/eudoxiamoura/GCB-Rondoboi.git
cd GCB-Rondoboi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Gerar uma chave secreta

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 4. Criar o banco Postgres

```bash
sudo -u postgres psql -c "CREATE USER rondoboi WITH PASSWORD 'ESCOLHA_UMA_SENHA_AQUI';"
sudo -u postgres psql -c "CREATE DATABASE rondoboi OWNER rondoboi;"
```

## 5. Levar o banco de dados real e migrar pro Postgres

O `instance/bovinos.db` (com os lotes já lançados) fica fora do git. Envie do
seu computador para o servidor:

```bash
scp instance/bovinos.db root@31.97.95.53:~/GCB-Rondoboi/instance/bovinos.db
```

No servidor, com o venv ativado, rode a migração (troque a senha pela que
você escolheu no passo 4):

```bash
cd ~/GCB-Rondoboi
source venv/bin/activate
DATABASE_URL_DESTINO="postgresql+psycopg://rondoboi:ESCOLHA_UMA_SENHA_AQUI@localhost/rondoboi" \
python deploy/migrate_to_postgres.py
```

O script mostra quantas linhas foram migradas em cada tabela — confira se
bate com o que você espera (ex: 21 lotes). Ele não apaga nem altera o
`bovinos.db` original, só lê dele; pode manter esse arquivo como backup.

## 6. Serviço systemd

Copie `deploy/rondoboi.service` para `/etc/systemd/system/rondoboi.service`,
substituindo `COLE_A_CHAVE_GERADA_AQUI` (chave do passo 3) e
`COLE_A_SENHA_DO_BANCO_AQUI` (senha do passo 4). Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rondoboi
sudo systemctl status rondoboi --no-pager
```

## 7. Nginx (proxy reverso)

Copie `deploy/nginx.conf` (já com o IP do servidor preenchido) para
`/etc/nginx/sites-available/rondoboi`. Depois:

```bash
sudo ln -sf /etc/nginx/sites-available/rondoboi /etc/nginx/sites-enabled/rondoboi
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## 8. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Atualizando uma versão já em produção

```bash
cd ~/GCB-Rondoboi
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart rondoboi
```

## Próximo passo: HTTPS

Sem domínio, o acesso é em HTTP puro (login trafega sem criptografia).
Quando houver um domínio apontando para o servidor, trocar para HTTPS com
[Let's Encrypt](https://certbot.eff.org/) (`certbot --nginx`).
