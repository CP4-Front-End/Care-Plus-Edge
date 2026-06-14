#!/usr/bin/env python3
"""
nfc_vincular.py
Servidor web com frontend healthcare corporativo.
Fluxo: celular encosta na tag → página de confirmação → usuário clica → PATCH no Orion.

Uso:
    FIWARE_IP=localhost python3 nfc_vincular.py

Dependências:
    pip3 install requests
"""

import http.server
import urllib.parse
import requests
import json
import datetime
import os
# ── Configuração ───────────────────────────────────────────────────────────────
FIWARE_IP   = os.environ.get("FIWARE_IP", "136.113.59.15")
ORION_PORT  = int(os.environ.get("ORION_PORT", 1026))
SERVER_PORT = int(os.environ.get("SERVER_PORT", 8080))
ORION_BASE  = f"http://{FIWARE_IP}:{ORION_PORT}/v2/entities"
# ──────────────────────────────────────────────────────────────────────────────

# ── Página de confirmação (GET /vincular) ──────────────────────────────────────
HTML_CONFIRM = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Vincular Pulseira</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #F4F6F8;
      --surface: #FFFFFF;
      --primary: #1c9770;
      --primary-dark: #167a5a;
      --primary-subtle: rgba(28,151,112,0.08);
      --primary-border: rgba(28,151,112,0.2);
      --text: #1A202C;
      --muted: #6B7685;
      --border: #E4E7EB;
      --radius-sm: 8px;
      --radius-md: 12px;
    }}
    html, body {{ height:100%; background:var(--bg); font-family:'Roboto',sans-serif; color:var(--text); -webkit-font-smoothing:antialiased; }}
    body {{ display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px; }}
    .wrap {{ width:100%; max-width:420px; animation:rise 0.4s cubic-bezier(0.22,1,0.36,1) both; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:20px; }}
    .brand-icon {{ width:36px; height:36px; background:var(--primary); border-radius:var(--radius-sm); display:flex; align-items:center; justify-content:center; }}
    .brand-icon svg {{ width:18px; height:18px; fill:none; stroke:#fff; stroke-width:2; stroke-linecap:round; }}
    .brand-name {{ font-size:18px; font-weight:700; color:var(--primary); letter-spacing:-0.3px; }}
    .card {{ background:var(--surface); border-radius:var(--radius-md); border:1px solid var(--border); padding:32px 28px; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
    .nfc-wrap {{ display:flex; justify-content:center; margin-bottom:24px; }}
    .nfc-circle {{ width:64px; height:64px; background:var(--primary-subtle); border-radius:50%; display:flex; align-items:center; justify-content:center; position:relative; }}
    .nfc-circle svg {{ width:30px; height:30px; fill:none; stroke:var(--primary); stroke-width:2; stroke-linecap:round; }}
    .nfc-circle::before, .nfc-circle::after {{ content:''; position:absolute; border-radius:50%; border:1.5px solid var(--primary); opacity:0; animation:ripple 2.4s ease-out infinite; }}
    .nfc-circle::before {{ width:84px; height:84px; animation-delay:0s; }}
    .nfc-circle::after  {{ width:108px; height:108px; animation-delay:0.7s; }}
    @keyframes ripple {{ 0% {{ opacity:0.4; transform:scale(0.85); }} 100% {{ opacity:0; transform:scale(1.1); }} }}
    h1 {{ font-size:20px; font-weight:700; color:var(--text); text-align:center; margin-bottom:6px; }}
    .sub {{ font-size:13px; color:var(--muted); text-align:center; line-height:1.6; margin-bottom:24px; }}
    .device-row {{ background:var(--primary-subtle); border:1px solid var(--primary-border); border-radius:var(--radius-sm); padding:12px 16px; margin-bottom:20px; display:flex; align-items:center; gap:10px; }}
    .device-dot {{ width:8px; height:8px; background:var(--primary); border-radius:50%; flex-shrink:0; box-shadow:0 0 0 3px rgba(28,151,112,0.2); animation:pulse-dot 2s ease-in-out infinite; }}
    @keyframes pulse-dot {{ 0%,100% {{ box-shadow:0 0 0 3px rgba(28,151,112,0.2); }} 50% {{ box-shadow:0 0 0 6px rgba(28,151,112,0.08); }} }}
    .device-label {{ font-size:11px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.08em; }}
    .device-id {{ font-size:13px; font-weight:700; color:var(--primary); margin-top:2px; font-family:monospace; }}
    .field {{ margin-bottom:20px; }}
    .field-label {{ display:block; font-size:12px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px; }}
    .field-input {{ width:100%; padding:12px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-family:'Roboto',sans-serif; font-size:14px; color:var(--text); background:var(--bg); outline:none; transition:border-color 150ms ease, box-shadow 150ms ease; }}
    .field-input:focus {{ border-color:var(--primary); box-shadow:0 0 0 3px rgba(28,151,112,0.12); }}
    .field-input::placeholder {{ color:#9BA3AE; }}
    .btn-confirm {{ width:100%; padding:13px; background:var(--primary); color:#fff; border:none; border-radius:var(--radius-sm); font-family:'Roboto',sans-serif; font-size:14px; font-weight:700; cursor:pointer; transition:opacity 150ms ease, transform 100ms ease; }}
    .btn-confirm:hover {{ opacity:0.92; }}
    .btn-confirm:active {{ transform:scale(0.98); }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="brand-icon"><svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
      <span class="brand-name">BoostCare</span>
    </div>
    <div class="card">
      <div class="nfc-wrap">
        <div class="nfc-circle">
          <svg viewBox="0 0 24 24"><path d="M20 12a8 8 0 0 0-8-8"/><path d="M4 12a8 8 0 0 0 8 8"/><path d="M17 12a5 5 0 0 0-5-5"/><path d="M7 12a5 5 0 0 0 5 5"/><circle cx="12" cy="12" r="1.5" fill="var(--primary)" stroke="none"/></svg>
        </div>
      </div>
      <h1>Vincular pulseira</h1>
      <p class="sub">Tag detectada. Confirme o apelido e clique em vincular.</p>
      <div class="device-row">
        <div class="device-dot"></div>
        <div>
          <div class="device-label">Dispositivo</div>
          <div class="device-id">{device_id}</div>
        </div>
      </div>
      <form method="get" action="/confirmar">
        <input type="hidden" name="tag"    value="{nfc_id}">
        <input type="hidden" name="device" value="{device_id}">
        <div class="field">
          <label class="field-label" for="nome">Apelido da pulseira</label>
          <input class="field-input" id="nome" name="nome" type="text" placeholder="Ex: Pulseira da Ana" autocomplete="off" autofocus>
        </div>
        <button class="btn-confirm" type="submit">Vincular agora</button>
      </form>
    </div>
  </div>
</body>
</html>"""

# ── Página de sucesso ──────────────────────────────────────────────────────────
HTML_SUCESSO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Pulseira Vinculada</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
    :root {{ --bg:#F4F6F8; --surface:#fff; --primary:#1c9770; --primary-subtle:rgba(28,151,112,0.08); --primary-border:rgba(28,151,112,0.2); --text:#1A202C; --muted:#6B7685; --border:#E4E7EB; }}
    html, body {{ height:100%; background:var(--bg); font-family:'Roboto',sans-serif; -webkit-font-smoothing:antialiased; }}
    body {{ display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px; }}
    .wrap {{ width:100%; max-width:420px; animation:rise 0.4s cubic-bezier(0.22,1,0.36,1) both; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:20px; }}
    .brand-icon {{ width:36px; height:36px; background:var(--primary); border-radius:8px; display:flex; align-items:center; justify-content:center; }}
    .brand-icon svg {{ width:18px; height:18px; fill:none; stroke:#fff; stroke-width:2; stroke-linecap:round; }}
    .brand-name {{ font-size:18px; font-weight:700; color:var(--primary); }}
    .card {{ background:var(--surface); border-radius:12px; border:1px solid var(--border); padding:32px 28px; box-shadow:0 1px 3px rgba(0,0,0,0.06); text-align:center; }}
    .check-circle {{ width:72px; height:72px; border-radius:50%; background:var(--primary); display:flex; align-items:center; justify-content:center; margin:0 auto 20px; animation:pop 0.4s cubic-bezier(0.34,1.56,0.64,1) both; }}
    @keyframes pop {{ from {{ transform:scale(0); opacity:0; }} to {{ transform:scale(1); opacity:1; }} }}
    .check-circle svg {{ width:32px; height:32px; stroke:#fff; stroke-width:2.5; fill:none; stroke-linecap:round; stroke-linejoin:round; }}
    .check-circle svg path {{ stroke-dasharray:40; stroke-dashoffset:40; animation:draw 0.35s 0.3s ease forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
    h1 {{ font-size:20px; font-weight:700; color:var(--text); margin-bottom:6px; }}
    .sub {{ font-size:13px; color:var(--muted); line-height:1.6; margin-bottom:24px; }}
    .info-grid {{ display:grid; gap:8px; text-align:left; }}
    .info-row {{ background:var(--primary-subtle); border:1px solid var(--primary-border); border-radius:8px; padding:10px 14px; }}
    .info-label {{ font-size:11px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.08em; }}
    .info-value {{ font-size:13px; font-weight:700; color:var(--primary); margin-top:2px; font-family:monospace; }}
    .ts {{ font-size:12px; color:#9BA3AE; margin-top:16px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="brand-icon"><svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
      <span class="brand-name">BoostCare</span>
    </div>
    <div class="card">
      <div class="check-circle">
        <svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>
      </div>
      <h1>Pulseira vinculada!</h1>
      <p class="sub">A pulseira <strong>{nome}</strong> foi vinculada com sucesso.</p>
      <div class="info-grid">
        <div class="info-row">
          <div class="info-label">Apelido</div>
          <div class="info-value">{nome}</div>
        </div>
        <div class="info-row">
          <div class="info-label">Dispositivo</div>
          <div class="info-value">{device_id}</div>
        </div>
        <div class="info-row">
          <div class="info-label">Tag NFC</div>
          <div class="info-value">{nfc_id}</div>
        </div>
      </div>
      <p class="ts">{timestamp}</p>
    </div>
  </div>
</body>
</html>"""

# ── Página de erro ─────────────────────────────────────────────────────────────
HTML_ERRO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Erro</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
    :root {{ --bg:#F4F6F8; --surface:#fff; --primary:#1c9770; --danger:#FC8181; --text:#1A202C; --muted:#6B7685; --border:#E4E7EB; }}
    html, body {{ height:100%; background:var(--bg); font-family:'Roboto',sans-serif; -webkit-font-smoothing:antialiased; }}
    body {{ display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px; }}
    .wrap {{ width:100%; max-width:420px; animation:rise 0.4s cubic-bezier(0.22,1,0.36,1) both; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:20px; }}
    .brand-icon {{ width:36px; height:36px; background:var(--primary); border-radius:8px; display:flex; align-items:center; justify-content:center; }}
    .brand-icon svg {{ width:18px; height:18px; fill:none; stroke:#fff; stroke-width:2; stroke-linecap:round; }}
    .brand-name {{ font-size:18px; font-weight:700; color:var(--primary); }}
    .card {{ background:var(--surface); border-radius:12px; border:1px solid var(--border); padding:32px 28px; box-shadow:0 1px 3px rgba(0,0,0,0.06); text-align:center; }}
    .err-icon {{ width:64px; height:64px; border-radius:50%; background:#FFF0F0; border:1px solid #FCC; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; font-size:26px; animation:pop 0.4s cubic-bezier(0.34,1.56,0.64,1) both; }}
    @keyframes pop {{ from {{ transform:scale(0); }} to {{ transform:scale(1); }} }}
    h1 {{ font-size:20px; font-weight:700; color:var(--danger); margin-bottom:8px; }}
    .sub {{ font-size:13px; color:var(--muted); line-height:1.6; margin-bottom:4px; }}
    .detail {{ font-size:12px; color:var(--muted); background:#FFF8F8; border:1px solid #FCC; border-radius:8px; padding:10px 14px; margin-top:16px; text-align:left; font-family:monospace; word-break:break-all; line-height:1.6; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="brand-icon"><svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
      <span class="brand-name">BoostCare</span>
    </div>
    <div class="card">
      <div class="err-icon">✕</div>
      <h1>{titulo}</h1>
      <p class="sub">Algo deu errado. Tente novamente.</p>
      <div class="detail">{detalhe}</div>
    </div>
  </div>
</body>
</html>"""


def patch_nfc_id(device_id: str, nfc_id: str, nome: str = "") -> tuple[bool, str]:
    url = f"{ORION_BASE}/{urllib.parse.quote(device_id, safe='')}/attrs"
    payload = {
        "nfcId": {
            "value": nfc_id,
            "type": "Text",
            "metadata": {
                "timestamp": {
                    "value": datetime.datetime.utcnow().isoformat() + "Z",
                    "type": "DateTime"
                }
            }
        },
        "name": {
            "value": nome,
            "type": "Text"
        }
    }
    headers = {
        "Content-Type":       "application/json",
        "fiware-service":     "smart",
        "fiware-servicepath": "/"
    }
    try:
        r = requests.patch(url, data=json.dumps(payload), headers=headers, timeout=5)
        if r.status_code == 204:
            return True, "ok"
        if r.status_code == 404:
            return False, f"Entidade '{device_id}' não encontrada no Orion."
        return False, f"Orion {r.status_code}: {r.text}"
    except requests.exceptions.ConnectionError:
        return False, f"Sem conexão com Orion em {FIWARE_IP}:{ORION_PORT}"
    except Exception as e:
        return False, str(e)


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {format % args}")

    def send_html(self, code: int, body: str):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # ── Passo 1: exibe página de confirmação ──────────────────────────────
        if parsed.path == "/":
            nfc_id    = params.get("tag",    [None])[0]
            device_id = params.get("device", [None])[0]

            if not nfc_id or not device_id:
                self.send_html(400, HTML_ERRO.format(
                    titulo="Parâmetros inválidos",
                    detalhe="URL precisa conter ?tag=UID&device=ID"
                ))
                return

            self.send_html(200, HTML_CONFIRM.format(
                nfc_id=nfc_id,
                device_id=device_id
            ))
            return

        # ── Passo 2: executa o vínculo após confirmação do usuário ────────────
        if parsed.path == "/confirmar":
            nfc_id    = params.get("tag",    [None])[0]
            device_id = params.get("device", [None])[0]
            nome      = params.get("nome",   [None])[0] or ""

            if not nfc_id or not device_id:
                self.send_html(400, HTML_ERRO.format(
                    titulo="Parâmetros inválidos",
                    detalhe="Requisição inválida. Tente novamente encostando o celular na pulseira."
                ))
                return

            sucesso, msg = patch_nfc_id(device_id, nfc_id, nome)

            if sucesso:
                ts = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y às %H:%M")
                extra = f" ({nome})" if nome else ""
                self.send_html(200, HTML_SUCESSO.format(
                    nfc_id=nfc_id,
                    device_id=device_id,
                    nome=nome or device_id,
                    timestamp=ts
                ))
                print(f"[OK] Vinculado: tag={nfc_id} → device={device_id}{extra}")
            else:
                self.send_html(500, HTML_ERRO.format(
                    titulo="Falha ao vincular",
                    detalhe=msg
                ))
                print(f"[ERRO] {msg}")
            return

        # ── Health check ──────────────────────────────────────────────────────
        if parsed.path == "/health":
            self.send_html(200, "<pre>ok</pre>")
            return

        self.send_html(404, HTML_ERRO.format(
            titulo="Página não encontrada",
            detalhe=self.path
        ))


if __name__ == "__main__":
    print(f"Servidor NFC-Vincular iniciado — porta {SERVER_PORT}")
    print(f"Orion: {FIWARE_IP}:{ORION_PORT}")
    print("-" * 60)
    server = http.server.HTTPServer(("0.0.0.0", SERVER_PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")