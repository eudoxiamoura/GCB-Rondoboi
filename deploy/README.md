# Deploy em VPS (Ubuntu/Debian)

Arquivos de referência usados para colocar o sistema em produção via
gunicorn + nginx + systemd, com acesso só por IP (sem domínio/HTTPS ainda).

## 1. Instalar dependências do sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git nginx
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

## 4. Serviço systemd

Copie `deploy/rondoboi.service` para `/etc/systemd/system/rondoboi.service`,
substituindo `COLE_A_CHAVE_GERADA_AQUI` pela chave do passo 3. Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rondoboi
sudo systemctl status rondoboi --no-pager
```

## 5. Nginx (proxy reverso)

Copie `deploy/nginx.conf` (já com o IP do servidor preenchido) para
`/etc/nginx/sites-available/rondoboi`. Depois:

```bash
sudo ln -sf /etc/nginx/sites-available/rondoboi /etc/nginx/sites-enabled/rondoboi
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## 6. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 7. Levar o banco de dados real

O `instance/bovinos.db` fica fora do git (dados financeiros reais). Envie do
seu computador para o servidor:

```bash
scp instance/bovinos.db root@31.97.95.53:~/GCB-Rondoboi/instance/bovinos.db
```

E reinicie o serviço para ele carregar o banco novo:

```bash
sudo systemctl restart rondoboi
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
