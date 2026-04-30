#include <WiFi.h>
#include <PubSubClient.h>

// ── WiFi / MQTT ───────────────────────────────────────────
const char* SSID        = "Wokwi-GUEST";
const char* PASSWORD    = "";
const char* BROKER_MQTT = "35.247.231.140";
const int   BROKER_PORT = 1883;
const char* TOPICO_SUB  = "/ul/TEF/step001/attrs";
const char* ID_MQTT     = "fiware_leds_step001";

// ── Pinos LEDs RGB ────────────────────────────────────────
// LED 1 — azul fraco (baixo esforço)
const int LED1_R = 13;
const int LED1_G = 12;
const int LED1_B = 14;

// LED 2 — amarelo (esforço médio)
const int LED2_R = 27;
const int LED2_G = 26;
const int LED2_B = 25;

// LED 3 — verde vibrante (meta atingida)
const int LED3_R = 18;
const int LED3_G = 5;
const int LED3_B = 17;

// ── Faixas de passos/min ──────────────────────────────────
const int FAIXA_BAIXA  = 10;  // até 10  → 1 LED
const int FAIXA_MEDIA  = 20;  // até 20  → 2 LEDs
                               // acima   → 3 LEDs

WiFiClient   espClient;
PubSubClient MQTT(espClient);

// ── Funções de LED ────────────────────────────────────────
void setLed(int r, int g, int b, int R, int G, int B) {
  digitalWrite(r, R);
  digitalWrite(g, G);
  digitalWrite(b, B);
}

void apagarTodos() {
  setLed(LED1_R, LED1_G, LED1_B, LOW, LOW, LOW);
  setLed(LED2_R, LED2_G, LED2_B, LOW, LOW, LOW);
  setLed(LED3_R, LED3_G, LED3_B, LOW, LOW, LOW);
}

void atualizarLeds(float media) {
  apagarTodos();

  if (media <= 0) {
    // todos apagados
    return;
  }

  if (media <= FAIXA_BAIXA) {
    // 1 LED — azul fraco
    setLed(LED1_R, LED1_G, LED1_B, LOW, LOW, HIGH);
    Serial.println(">> LEDs: 1 aceso (azul)");
    return;
  }

  if (media <= FAIXA_MEDIA) {
    // 2 LEDs — azul + amarelo
    setLed(LED1_R, LED1_G, LED1_B, LOW, LOW, HIGH);
    setLed(LED2_R, LED2_G, LED2_B, HIGH, HIGH, LOW);
    Serial.println(">> LEDs: 2 acesos (azul + amarelo)");
    return;
  }

  // 3 LEDs — azul + amarelo + verde vibrante
  setLed(LED1_R, LED1_G, LED1_B, LOW,  LOW,  HIGH);
  setLed(LED2_R, LED2_G, LED2_B, HIGH, HIGH, LOW);
  setLed(LED3_R, LED3_G, LED3_B, LOW,  HIGH, LOW);
  Serial.println(">> LEDs: 3 acesos (azul + amarelo + verde)");
}

// ── Callback MQTT ─────────────────────────────────────────
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.print("MQTT recebido: ");
  Serial.println(msg);

  // Formato esperado: "p|123|m|45.6" ou só "m|45.6"
  // Extrai o valor após "m|"
  int idx = msg.indexOf("m|");
  if (idx == -1) return;

  String valorStr = msg.substring(idx + 2);
  // corta se houver mais campos depois
  int pipe = valorStr.indexOf("|");
  if (pipe != -1) valorStr = valorStr.substring(0, pipe);

  float media = valorStr.toFloat();
  Serial.print("steps_per_minute recebido: ");
  Serial.println(media);

  atualizarLeds(media);
}

// ── WiFi ──────────────────────────────────────────────────
void initWiFi() {
  WiFi.begin(SSID, PASSWORD);
  Serial.print("Conectando ao WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi conectado. IP: ");
  Serial.println(WiFi.localIP());
}

void reconectWiFi() {
  if (WiFi.status() != WL_CONNECTED) initWiFi();
}

void reconnectMQTT() {
  while (!MQTT.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (MQTT.connect(ID_MQTT)) {
      Serial.println(" conectado!");
      MQTT.subscribe(TOPICO_SUB);
      Serial.print("Inscrito em: ");
      Serial.println(TOPICO_SUB);
    } else {
      Serial.println(" falha. Tentando em 2s.");
      delay(2000);
    }
  }
}

void verificaConexoes() {
  reconectWiFi();
  if (!MQTT.connected()) reconnectMQTT();
}

// ── Setup ─────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Inicializa pinos dos LEDs
  int pinos[] = {
    LED1_R, LED1_G, LED1_B,
    LED2_R, LED2_G, LED2_B,
    LED3_R, LED3_G, LED3_B
  };
  for (int i = 0; i < 9; i++) {
    pinMode(pinos[i], OUTPUT);
    digitalWrite(pinos[i], LOW);
  }

  initWiFi();
  MQTT.setServer(BROKER_MQTT, BROKER_PORT);
  MQTT.setCallback(mqtt_callback);

  Serial.println("=================================");
  Serial.println("LED Monitor — step001");
  Serial.print("Faixa baixa:  0–");   Serial.print(FAIXA_BAIXA);  Serial.println(" p/min → 1 LED");
  Serial.print("Faixa média:  ");     Serial.print(FAIXA_BAIXA+1); Serial.print("–"); Serial.print(FAIXA_MEDIA); Serial.println(" p/min → 2 LEDs");
  Serial.print("Faixa alta:   >");    Serial.print(FAIXA_MEDIA);  Serial.println(" p/min → 3 LEDs");
  Serial.println("=================================");
}

// ── Loop ──────────────────────────────────────────────────
void loop() {
  verificaConexoes();
  MQTT.loop();
  delay(50);
}
