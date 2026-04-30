# NFC → FIWARE — Guia de implementação

## O que isso faz

Celular encosta na pulseira (NTAG213) → abre URL automaticamente →
servidor Python recebe o GET → faz PATCH no Orion → MongoDB registra o vínculo.

---

## 1. Provisionar o atributo nfcId na entidade existente

Execute **uma vez** no servidor para adicionar o atributo à entidade step001:

```bash
curl -X POST "http://35.247.231.140:1026/v2/entities/urn:ngsi-ld:step001/attrs" \
  -H "Content-Type: application/json" \
  -d '{
    "nfcId": {
      "value": "",
      "type": "Text"
    }
  }'
```

> Se sua entidade não usa o prefixo urn:ngsi-ld:, troque pelo ID exato.
> Verifique com: curl http://35.247.231.140:1026/v2/entities/step001

---

## 2. Subir o servidor Python

```bash
# Instalar dependência
pip3 install requests

# Rodar (com IP do servidor na env var se o IP mudou)
FIWARE_IP=35.247.231.140 python3 nfc_vincular.py
```

Para rodar em background:
```bash
nohup FIWARE_IP=35.247.231.140 python3 nfc_vincular.py > nfc.log 2>&1 &
```

A porta padrão é 8080. Para mudar:
```bash
SERVER_PORT=9000 FIWARE_IP=35.247.231.140 python3 nfc_vincular.py
```

---

## 3. Gravar a URL na tag NTAG213

Use o app **NFC Tools** (Android/iOS) → Write → Add a record → URL/URI

URL a gravar:
```
http://35.247.231.140:8080/vincular?tag=UID_FIXO_DA_TAG&device=step001
```

ATENÇÃO: o UID_FIXO_DA_TAG é o UID físico da NTAG213 (leia com NFC Tools → Read antes de gravar).
Exemplo real: se o UID for 04:A3:B2:C1:D4:E5:F6, use 04A3B2C1D4E5F6

URL final de exemplo:
```
http://35.247.231.140:8080/vincular?tag=04A3B2C1D4E5F6&device=step001
```

---

## 4. Verificar o vínculo no Orion

```bash
curl http://35.247.231.140:1026/v2/entities/step001 | python3 -m json.tool
```

Você verá o atributo nfcId com o UID gravado e o timestamp do vínculo.

---

## 5. Liberar porta no firewall (se necessário)

```bash
sudo ufw allow 8080/tcp
```

---

## Fluxo completo

```
[Celular encosta na pulseira]
        ↓
[NTAG213 abre URL no browser]
        ↓
[GET /vincular?tag=UID&device=step001]
        ↓
[nfc_vincular.py recebe a requisição]
        ↓
[PATCH /v2/entities/step001/attrs → Orion]
        ↓
[MongoDB persiste nfcId + timestamp]
        ↓
[Browser exibe confirmação]
```

---

## Observações

- O IP rotativo é o único ponto de fragilidade: quando mudar, precisa regravar a tag.
  Solução futura: usar um domínio com DNS dinâmico (ex: DuckDNS, gratuito) para
  não depender do IP.
- O servidor trata automaticamente entidades sem o atributo nfcId ainda provisionado
  (faz POST em vez de PATCH).
- Nenhuma alteração necessária no código do ESP32.
