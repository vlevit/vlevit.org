# -*- mode: nginx; -*-
server {
    listen 443 ssl;
    include includes/ssl-keys;
    include includes/ssl-certs/bucket[.]ftp.sh;

    root /srv/http/transfer.sh-web;

    server_name bucket.ftp.sh;

    client_max_body_size 2500M;

    location / {
        proxy_pass https://127.0.0.1:5450;
        proxy_set_header Host $host;

        proxy_ssl_trusted_certificate /srv/http/transfer.sh/transfersh-self-signed-localhost.pem;
        proxy_ssl_session_reuse on;
        proxy_ssl_verify on;
    }

    include includes/acme-challenge;

}

server {
    listen 80;
    server_name bucket.ftp.sh;
    return 301 https://$host$request_uri;
}
