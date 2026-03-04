# Cloudflare-DNS-Monitor
Automação Python Dockerizada que monitora registros DNS na Cloudflare, e remove IPs problemáticos, integrando com Up Time Kuma

Uptime Kuma monitora IPs do cluster, e quando detecta um IP não saudável, aciona o script, que varre todos os registros dns contendo o IP defeituoso, e desativa o mesmo.

Ao detectar que o Host está UP novamente, o script roda, reativando o IP nos registros DNS
