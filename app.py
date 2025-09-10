from flask import Flask, render_template_string
import socket
import requests
a = "commit deu bom"
+++++==+++
app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Hello Oracle Cloud</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { color-scheme: dark; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 2rem; background: #0f172a; color: #e2e8f0; }
    .card { max-width: 780px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 14px; padding: 1.25rem 1.5rem; }
    h1 { margin: 0 0 1rem 0; font-size: 1.8rem; }
    .grid { display: grid; grid-template-columns: 180px 1fr; gap: .75rem; }
    .row { padding: .6rem 0; border-top: 1px solid #1f2937; }
    .row:first-of-type { border-top: 0; }
    .label { color: #9ca3af; }
    code { background: #0b1220; padding: .15rem .4rem; border-radius: 6px; }
    .ok { display:inline-block; background:#065f46; color:#d1fae5; padding:.25rem .5rem; border-radius:8px; font-size:.9rem; }
    footer { margin-top: 1rem; color:#94a3b8; font-size:.9rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>✅ Hello World — Oracle Cloud</h1>
    <div class="row grid"><div class="label">Status</div><div><span class="ok">Servidor Web ativo</span></div></div>
    <div class="row grid"><div class="label">Hostname</div><div><code>{{ host }}</code></div></div>
    <div class="row grid"><div class="label">Private IP</div><div><code>{{ priv }}</code></div></div>
    <div class="row grid"><div class="label">Public IP</div><div><code>{{ pub }}</code></div></div>
    <footer>Descoberto via IMDS (OCI) ou rede local, sem dependências externas.</footer>
  </div>
</body>
</html>
"""

IMDS_URL_VNICS = "http://169.254.169.254/opc/v2/vnics/"
IMDS_HEADERS = {"Authorization": "Bearer Oracle"}  # requerido pela OCI IMDS v2


def get_ips_from_oci_imds():
    """
    Tenta obter IPs pela Instance Metadata (OCI).
    Retorna (private_ip, public_ip) ou (None, None) se não estiver na OCI.
    """
    try:
        r = requests.get(IMDS_URL_VNICS, headers=IMDS_HEADERS, timeout=0.4)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            vnic = data[0]  # primeira VNIC
            private_ip = vnic.get("privateIp")
            # em VNICs públicas, 'publicIp' costuma estar presente
            public_ip = vnic.get("publicIp")
            return private_ip, public_ip
    except Exception:
        pass
    return None, None


def get_first_non_loopback_ipv4():
    """
    Obtém um IPv4 local não-loopback sem chamar serviços externos.
    Usa getaddrinfo do hostname e filtra 127.0.0.0/8.
    """
    try:
        host = socket.gethostname()
        infos = socket.getaddrinfo(host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        for fam, socktype, proto, canonname, sockaddr in infos:
            ip = sockaddr[0]
            if not ip.startswith("127."):
                return ip
    except Exception:
        pass

    # fallback final: tenta o IP do hostname direto
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "unknown"


def get_private_ip():
    priv, _ = get_ips_from_oci_imds()
    if priv:
        return priv
    return get_first_non_loopback_ipv4()


def get_public_ip():
    # 1) Tenta IMDS (se VNIC tiver IP público)
    _, pub = get_ips_from_oci_imds()
    if pub:
        return pub

    # 2) Caso não exista IP público na VNIC (ou fora da OCI),
    #    não fazemos requisição externa; retornamos "none".
    return "none"


@app.route("/")
def index():
    host = socket.gethostname()
    priv = get_private_ip()
    pub = get_public_ip()
    return render_template_string(HTML_TEMPLATE, host=host, priv=priv, pub=pub)


if __name__ == "__main__":
    # útil para rodar local; em produção use gunicorn com Nginx
    app.run(host="127.0.0.1", port=8000)
