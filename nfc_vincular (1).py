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
FIWARE_IP   = os.environ.get("FIWARE_IP", "35.247.231.140")
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
  <title>Vincular Dispositivo</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:        #F0F4F8;
      --surface:   #FFFFFF;
      --primary:   #0A6E6E;
      --primary-l: #E6F3F3;
      --accent:    #00B4A2;
      --text:      #1A2B3C;
      --muted:     #6B7C93;
      --border:    #D9E3EC;
      --danger:    #E05A5A;
      --radius:    20px;
    }}

    html, body {{
      height: 100%;
      background: var(--bg);
      font-family: 'DM Sans', sans-serif;
      color: var(--text);
      -webkit-font-smoothing: antialiased;
    }}

    body {{
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px;
    }}

    .wrap {{
      width: 100%;
      max-width: 400px;
      animation: rise 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
    }}

    @keyframes rise {{
      from {{ opacity: 0; transform: translateY(24px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 28px;
    }}

    .brand-icon {{
      width: 36px; height: 36px;
      background: var(--primary);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }}

    .brand-icon svg {{ width: 18px; height: 18px; fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; }}

    .brand-name {{
      font-family: 'DM Serif Display', serif;
      font-size: 20px;
      color: var(--primary);
      letter-spacing: -0.3px;
    }}

    .card {{
      background: var(--surface);
      border-radius: var(--radius);
      padding: 36px 32px 32px;
      box-shadow: 0 4px 24px rgba(10,110,110,0.08), 0 1px 4px rgba(0,0,0,0.04);
    }}

    .nfc-icon {{
      width: 72px; height: 72px;
      background: var(--primary-l);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 24px;
      position: relative;
    }}

    .nfc-icon svg {{ width: 36px; height: 36px; }}

    .nfc-icon::before, .nfc-icon::after {{
      content: '';
      position: absolute;
      border-radius: 50%;
      border: 2px solid var(--accent);
      opacity: 0;
      animation: ripple 2.4s ease-out infinite;
    }}
    .nfc-icon::before {{ width: 92px; height: 92px; animation-delay: 0s; }}
    .nfc-icon::after  {{ width: 116px; height: 116px; animation-delay: 0.6s; }}

    @keyframes ripple {{
      0%   {{ opacity: 0.5; transform: scale(0.85); }}
      100% {{ opacity: 0;   transform: scale(1.1); }}
    }}

    .question {{
      font-family: 'DM Serif Display', serif;
      font-size: 22px;
      line-height: 1.3;
      color: var(--text);
      text-align: center;
      margin-bottom: 8px;
      letter-spacing: -0.3px;
    }}

    .sub {{
      font-size: 14px;
      color: var(--muted);
      text-align: center;
      line-height: 1.6;
      margin-bottom: 28px;
    }}

    .device-info {{
      background: var(--primary-l);
      border: 1px solid #C2DEDE;
      border-radius: 12px;
      padding: 14px 18px;
      margin-bottom: 28px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .device-dot {{
      width: 10px; height: 10px;
      background: var(--accent);
      border-radius: 50%;
      flex-shrink: 0;
      animation: pulse-dot 2s ease-in-out infinite;
      box-shadow: 0 0 0 3px rgba(0,180,162,0.2);
    }}

    @keyframes pulse-dot {{
      0%, 100% {{ box-shadow: 0 0 0 3px rgba(0,180,162,0.2); }}
      50%       {{ box-shadow: 0 0 0 6px rgba(0,180,162,0.1); }}
    }}

    .device-text {{ flex: 1; }}
    .device-label {{ font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    .device-id    {{ font-size: 15px; font-weight: 600; color: var(--primary); margin-top: 2px; }}

    .btn-confirm {{
      width: 100%;
      padding: 16px;
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 14px;
      font-family: 'DM Sans', sans-serif;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s, box-shadow 0.2s;
      box-shadow: 0 4px 16px rgba(10,110,110,0.25);
      margin-bottom: 12px;
      position: relative;
      overflow: hidden;
    }}

    .btn-confirm:hover  {{ background: #085c5c; box-shadow: 0 6px 20px rgba(10,110,110,0.32); }}
    .btn-confirm:active {{ transform: scale(0.98); }}
    .btn-confirm.loading {{ pointer-events: none; }}
    .btn-confirm.loading span {{ opacity: 0; }}
    .btn-confirm.loading::after {{
      content: '';
      position: absolute;
      inset: 0; margin: auto;
      width: 22px; height: 22px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }}

    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    .btn-cancel {{
      width: 100%;
      padding: 14px;
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--border);
      border-radius: 14px;
      font-family: 'DM Sans', sans-serif;
      font-size: 15px;
      cursor: pointer;
      transition: border-color 0.2s, color 0.2s;
    }}

    .btn-cancel:hover {{ border-color: var(--danger); color: var(--danger); }}

    .uid-badge {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin-top: 20px;
    }}

    .uid-badge span {{ font-size: 11px; color: #A0AEBB; font-family: monospace; letter-spacing: 0.05em; }}
    .uid-dot {{ width: 4px; height: 4px; background: #C8D5E0; border-radius: 50%; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
      </div>
      <span class="brand-name">StepCare</span>
    </div>

    <div class="card">
      <div class="nfc-icon">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="10" fill="#0A6E6E" opacity="0.12"/>
          <circle cx="24" cy="24" r="5"  fill="#0A6E6E"/>
          <path d="M13 24a11 11 0 0 1 11-11" stroke="#00B4A2" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M35 24a11 11 0 0 1-11 11" stroke="#00B4A2" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M8  24a16 16 0 0 1 16-16" stroke="#0A6E6E" stroke-width="2"   stroke-linecap="round" opacity="0.4"/>
          <path d="M40 24a16 16 0 0 1-16 16" stroke="#0A6E6E" stroke-width="2"   stroke-linecap="round" opacity="0.4"/>
        </svg>
      </div>

      <h1 class="question">Deseja vincular seu dispositivo à Pulseira?</h1>
      <p class="sub">Ao confirmar, este celular será associado ao monitor de atividade identificado abaixo.</p>

      <div class="device-info">
        <div class="device-dot"></div>
        <div class="device-text">
          <div class="device-label">Dispositivo detectado</div>
          <div class="device-id">{device_id}</div>
        </div>
      </div>

      <button class="btn-confirm" id="btnConfirm" onclick="confirmar()">
        <span>Confirmar vínculo</span>
      </button>
      <button class="btn-cancel" onclick="cancelar()">Cancelar</button>

      <div class="uid-badge">
        <span>TAG</span>
        <div class="uid-dot"></div>
        <span>{nfc_id}</span>
      </div>
    </div>
  </div>

  <script>
    function confirmar() {{
      const btn = document.getElementById('btnConfirm');
      btn.classList.add('loading');
      fetch('/confirmar?tag={nfc_id}&device={device_id}')
        .then(r => r.text())
        .then(html => {{ document.open('text/html','replace'); document.write(html); }})
        .catch(() => {{ btn.classList.remove('loading'); alert('Erro de conexão. Tente novamente.'); }});
    }}
    function cancelar() {{
      document.querySelector('.card').style.opacity = '0.4';
      document.querySelector('.card').style.transition = '0.3s';
      document.querySelector('.card').style.pointerEvents = 'none';
      document.querySelector('.question').textContent = 'Operação cancelada.';
    }}
  </script>
</body>
</html>"""

# ── Página de sucesso ──────────────────────────────────────────────────────────
HTML_SUCESSO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Vinculado</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{ --primary:#0A6E6E; --accent:#00B4A2; --bg:#F0F4F8; --surface:#fff; --text:#1A2B3C; --muted:#6B7C93; }}
    html, body {{ height:100%; background:var(--bg); font-family:'DM Sans',sans-serif; -webkit-font-smoothing:antialiased; }}
    body {{ display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px; }}
    .wrap {{ width:100%; max-width:400px; animation:rise 0.5s cubic-bezier(0.22,1,0.36,1) both; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(24px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:28px; }}
    .brand-icon {{ width:36px; height:36px; background:var(--primary); border-radius:10px; display:flex; align-items:center; justify-content:center; }}
    .brand-icon svg {{ width:18px; height:18px; fill:none; stroke:#fff; stroke-width:2; stroke-linecap:round; }}
    .brand-name {{ font-family:'DM Serif Display',serif; font-size:20px; color:var(--primary); letter-spacing:-0.3px; }}
    .card {{ background:var(--surface); border-radius:20px; padding:40px 32px 36px; box-shadow:0 4px 24px rgba(10,110,110,0.08); text-align:center; }}
    .check-circle {{
      width:80px; height:80px; border-radius:50%;
      background: conic-gradient(var(--accent) 0%, var(--primary) 100%);
      display:flex; align-items:center; justify-content:center;
      margin: 0 auto 28px;
      animation: pop 0.4s cubic-bezier(0.34,1.56,0.64,1) both;
    }}
    @keyframes pop {{ from {{ transform:scale(0); opacity:0; }} to {{ transform:scale(1); opacity:1; }} }}
    .check-circle svg {{ width:36px; height:36px; stroke:#fff; stroke-width:2.5; fill:none; stroke-linecap:round; stroke-linejoin:round; }}
    .check-circle svg path {{ stroke-dasharray:40; stroke-dashoffset:40; animation:draw 0.4s 0.35s ease forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
    h1 {{ font-family:'DM Serif Display',serif; font-size:24px; color:var(--text); margin-bottom:8px; letter-spacing:-0.3px; }}
    .sub {{ font-size:14px; color:var(--muted); line-height:1.6; margin-bottom:28px; }}
    .info-grid {{ display:grid; gap:10px; text-align:left; }}
    .info-row {{ background:#F7FAFA; border:1px solid #E0EEEE; border-radius:12px; padding:12px 16px; }}
    .info-label {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:0.08em; }}
    .info-value {{ font-size:14px; font-weight:600; color:var(--primary); margin-top:3px; font-family:monospace; }}
    .ts {{ font-size:12px; color:#A0AEBB; text-align:center; margin-top:20px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="brand-icon"><svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
      <span class="brand-name">StepCare</span>
    </div>
    <div class="card">
      <div class="check-circle">
        <svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>
      </div>
      <h1>Pulseira vinculada!</h1>
      <p class="sub">Seu dispositivo foi associado com sucesso. Os dados de atividade serão sincronizados automaticamente.</p>
      <div class="info-grid">
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
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&family=DM+Serif+Display&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
    :root {{ --primary:#0A6E6E; --danger:#E05A5A; --bg:#F0F4F8; --surface:#fff; --text:#1A2B3C; --muted:#6B7C93; }}
    html, body {{ height:100%; background:var(--bg); font-family:'DM Sans',sans-serif; -webkit-font-smoothing:antialiased; }}
    body {{ display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px; }}
    .wrap {{ width:100%; max-width:400px; animation:rise 0.5s cubic-bezier(0.22,1,0.36,1) both; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(24px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:28px; }}
    .brand-icon {{ width:36px; height:36px; background:var(--primary); border-radius:10px; display:flex; align-items:center; justify-content:center; }}
    .brand-icon svg {{ width:18px; height:18px; fill:none; stroke:#fff; stroke-width:2; stroke-linecap:round; }}
    .brand-name {{ font-family:'DM Serif Display',serif; font-size:20px; color:var(--primary); }}
    .card {{ background:var(--surface); border-radius:20px; padding:40px 32px 36px; box-shadow:0 4px 24px rgba(10,110,110,0.08); text-align:center; }}
    .err-icon {{ width:72px; height:72px; border-radius:50%; background:#FFF0F0; border:2px solid #F5C5C5; display:flex; align-items:center; justify-content:center; margin:0 auto 24px; font-size:32px; animation:pop 0.4s cubic-bezier(0.34,1.56,0.64,1) both; }}
    @keyframes pop {{ from {{ transform:scale(0); }} to {{ transform:scale(1); }} }}
    h1 {{ font-family:'DM Serif Display',serif; font-size:22px; color:var(--danger); margin-bottom:8px; }}
    .detail {{ font-size:13px; color:var(--muted); line-height:1.6; background:#FFF8F8; border:1px solid #F5C5C5; border-radius:10px; padding:12px 16px; margin-top:20px; text-align:left; font-family:monospace; word-break:break-all; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="brand-icon"><svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
      <span class="brand-name">StepCare</span>
    </div>
    <div class="card">
      <div class="err-icon">✕</div>
      <h1>{titulo}</h1>
      <div class="detail">{detalhe}</div>
    </div>
  </div>
</body>
</html>"""


def patch_nfc_id(device_id: str, nfc_id: str) -> tuple[bool, str]:
    url = f"{ORION_BASE}/{device_id}/attrs"
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
        if r.status_code == 422:
            r2 = requests.post(url, data=json.dumps(payload), headers=headers, timeout=5)
            if r2.status_code in (200, 201, 204):
                return True, "ok (atributo criado)"
            return False, f"Orion {r2.status_code}: {r2.text}"
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
        if parsed.path == "/vincular":
            nfc_id    = params.get("tag",    [None])[0]
            device_id = params.get("device", [None])[0]

            if not nfc_id or not device_id:
                self.send_html(400, HTML_ERRO.format(
                    titulo="Parâmetros inválidos",
                    detalhe="URL precisa conter ?tag=UID&device=ID_DO_DISPOSITIVO"
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

            if not nfc_id or not device_id:
                self.send_html(400, HTML_ERRO.format(
                    titulo="Parâmetros inválidos",
                    detalhe="Requisição inválida. Tente novamente encostando o celular na pulseira."
                ))
                return

            sucesso, msg = patch_nfc_id(device_id, nfc_id)

            if sucesso:
                ts = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
                self.send_html(200, HTML_SUCESSO.format(
                    nfc_id=nfc_id,
                    device_id=device_id,
                    timestamp=ts
                ))
                print(f"[OK] Vinculado: tag={nfc_id} → device={device_id}")
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
