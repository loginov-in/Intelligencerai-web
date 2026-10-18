#!/usr/bin/env bash
#
# Деплой Intelligencerai-web на сервер с доменом cloud.intelligencerai.ru
#
# Использование:
#   ./deploy.sh [ветка]          # по умолчанию main
#
# Переменные окружения (опционально):
#   CERT_EMAIL=admin@example.com  # e-mail для Let's Encrypt (обязателен при первом запуске)
#   APP_DIR=/opt/intelligencerai-web
#   REPO=https://github.com/loginov-in/Intelligencerai-web.git
#
# Скрипт можно запускать повторно — он идемпотентен (обновляет код,
# пересобирает контейнеры, продлевает сертификат при необходимости).

set -euo pipefail

DOMAIN="cloud.intelligencerai.ru"
APP_DIR="${APP_DIR:-/opt/intelligencerai-web}"
REPO="${REPO:-https://github.com/loginov-in/Intelligencerai-web.git}"
BRANCH="${1:-main}"
CERT_EMAIL="${CERT_EMAIL:-}"
COMPOSE_PROJECT="intelligencerai-web"
LETSENCRYPT_VOLUME="intelligencerai-letsencrypt"
CERTBOT_WWW_VOLUME="intelligencerai-certbot-www"
LETSENCRYPT_LIVE_DIR="/etc/letsencrypt/live/${DOMAIN}"

log()  { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[deploy]\033[0m %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

# ---------------------------------- root ---------------------------------- #
if [ "$(id -u)" -ne 0 ]; then
    log "Запуск через sudo..."
    exec sudo -E env "CERT_EMAIL=${CERT_EMAIL}" "APP_DIR=${APP_DIR}" "REPO=${REPO}" "$0" "$@"
fi

# --------------------------------- пакеты --------------------------------- #
PKG_MGR=""
if command -v apt-get >/dev/null 2>&1; then PKG_MGR="apt-get"; fi
if command -v dnf   >/dev/null 2>&1; then PKG_MGR="dnf"; fi
if command -v yum   >/dev/null 2>&1; then PKG_MGR="yum"; fi

if ! command -v git >/dev/null 2>&1; then
    log "Установка git..."
    [ "$PKG_MGR" = "apt-get" ] && apt-get update -y && apt-get install -y git curl \
        || { [ "$PKG_MGR" = "dnf" ] && dnf install -y git curl; } \
        || yum install -y git curl
fi

if ! command -v docker >/dev/null 2>&1; then
    log "Установка Docker..."
    curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null 2>&1 || die "Плагин docker compose не найден"

# --------------------------------- порты ---------------------------------- #
if command -v ss >/dev/null 2>&1; then
    if ss -lntH '( sport = :80 or sport = :443 )' | grep -qvE 'docker|:::'; then
        if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nginx 2>/dev/null; then
            log "Останавливаем системный nginx (порт 80/443 занят)"
            systemctl disable --now nginx || true
        else
            die "Порты 80/443 заняты сторонним процессом: $(ss -lntp '( sport = :80 or sport = :443 )')"
        fi
    fi
fi

# --------------------------------- код ------------------------------------ #
log "Получение кода (ветка: ${BRANCH})..."
mkdir -p "$APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" fetch origin
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" merge --ff-only "origin/${BRANCH}"
else
    git clone -b "$BRANCH" "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

# --------------------------------- .env ----------------------------------- #
if [ ! -f .env ]; then
    die "Не найден ${APP_DIR}/.env — создайте его (см. .env.example в репозитории) и запустите скрипт снова"
fi
grep -q '^SECRET_KEY=' .env || die "В .env отсутствует переменная SECRET_KEY"

mkdir -p nginx.conf.d

# ---------------------------- сертификат ---------------------------------- #
cert_exists() {
    docker run --rm -v "${LETSENCRYPT_VOLUME}:/etc/letsencrypt" alpine \
        sh -c "[ -f ${LETSENCRYPT_LIVE_DIR}/fullchain.pem ] && echo yes" 2>/dev/null | grep -q yes
}

bootstrap_nginx() {
    log "Первый запуск: пишем bootstrap-конфиг nginx (порт 80, только HTTP)"
    cat > nginx.conf.d/default.conf <<NGINX
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://web:9120;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX
}

if cert_exists; then
    log "Сертификат уже есть — ставим боевой конфиг nginx"
    cp nginx.conf nginx.conf.d/default.conf
else
    bootstrap_nginx
fi

# ------------------------------- сборка ----------------------------------- #
log "Сборка и запуск контейнеров..."
docker compose -p "$COMPOSE_PROJECT" build web
docker compose -p "$COMPOSE_PROJECT" up -d

if ! curl -fsS --max-time 10 "http://127.0.0.1" -H "Host: ${DOMAIN}" >/dev/null 2>&1; then
    err "Приложение не отвечает на http://127.0.0.1 — логи:"
    docker compose -p "$COMPOSE_PROJECT" logs --tail=50 web || true
fi

# -------------------------- выпуск сертификата ---------------------------- #
if ! cert_exists; then
    [ -n "$CERT_EMAIL" ] || die "Укажите e-mail для Let's Encrypt: CERT_EMAIL=you@example.com $0"
    log "Запрашиваем сертификат Let's Encrypt для ${DOMAIN}..."
    docker run --rm \
        -v "${LETSENCRYPT_VOLUME}:/etc/letsencrypt" \
        -v "${CERTBOT_WWW_VOLUME}:/var/www/certbot" \
        certbot/certbot certonly \
            --webroot -w /var/www/certbot \
            -d "$DOMAIN" \
            --email "$CERT_EMAIL" \
            --agree-tos --no-eff-email \
            --non-interactive --keep-until-expiring

    log "Включаем HTTPS..."
    cp nginx.conf nginx.conf.d/default.conf
    docker compose -p "$COMPOSE_PROJECT" exec -T nginx nginx -s reload
fi

# --------------------------- продление сертификата ------------------------ #
renew_script="${APP_DIR}/renew-certs.sh"
cat > "$renew_script" <<RENEW
#!/usr/bin/env bash
set -euo pipefail
cd ${APP_DIR}
docker run --rm \\
    -v ${LETSENCRYPT_VOLUME}:/etc/letsencrypt \\
    -v ${CERTBOT_WWW_VOLUME}:/var/www/certbot \\
    certbot/certbot renew --webroot -w /var/www/certbot --quiet
docker compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
RENEW
chmod +x "$renew_script"

CRON_LINE="0 3 * * 1 ${renew_script} >> /var/log/intelligencerai-renew.log 2>&1"
if ! crontab -l 2>/dev/null | grep -qF "$renew_script"; then
    log "Добавляем задание в crontab для продления сертификата..."
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
fi

# -------------------------------- итоги ----------------------------------- #
log "Статус контейнеров:"
docker compose -p "$COMPOSE_PROJECT" ps

if cert_exists; then
    log "Срок действия сертификата:"
    docker run --rm -v "${LETSENCRYPT_VOLUME}:/etc/letsencrypt" alpine \
        sh -c "ls -l ${LETSENCRYPT_LIVE_DIR}/fullchain.pem" || true
fi

if curl -fsS --max-time 10 -o /dev/null "https://${DOMAIN}/" 2>/dev/null; then
    log "OK: https://${DOMAIN} отвечает"
else
    err "https://${DOMAIN} пока не отвечает (проверьте DNS-запись A → IP сервера и логи: docker compose -p ${COMPOSE_PROJECT} logs)"
fi

log "Готово."
