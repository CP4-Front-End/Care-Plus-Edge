#include <WiFi.h>
#include <PubSubClient.h>
//monitor led
const char* SSID        = "Wokwi-GUEST";
const char* PASSWORD    = "";
const char* BROKER_MQTT      = "host"; // ip do host do fiware
const int   BROKER_PORT      = 1883; // porta padrão do broker, normalmente 1883
const char* TOPICO_SUB  = "/ul/TEF/step001/attrs";
const char* ID_MQTT     = "fiware_leds_step001";

const int RED_PIN   = 25;
const int GREEN_PIN = 26;
const int BLUE_PIN  = 27;

// 0        → apagado
// 1–10     → azul fraco
// 11–20    → amarelo
// 21+      → verde vibrante

WiFiClient   espClient;
PubSubClient MQTT(espClient);

void setLed(int r, int g, int b) {
  analogWrite(RED_PIN,   r);
  analogWrite(GREEN_PIN, g);
  analogWrite(BLUE_PIN,  b);
}

void atualizarLed(float media) {
  if (media <= 0) {
    setLed(0, 0, 0);
    Serial.println(">> LED: apagado");
    return;
  }
  if (media <= 10) {
    setLed(0, 0, 80);   // azul fraco
    Serial.println(">> LED: azul (baixo)");
    return;
  }
  if (media <= 20) {
    setLed(180, 180, 0); // amarelo
    Serial.println(">> LED: amarelo (medio)");
    return;
  }
  setLed(0, 255, 0);    // verde vibrante
  Serial.println(">> LED: verde (meta atingida)");
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.print("MQTT recebido: ");
  Serial.println(msg);

  // Extrai valor após "m|"
  int idx = msg.indexOf("m|");
  if (idx == -1) return;

  String valorStr = msg.substring(idx + 2);
  int pipe = valorStr.indexOf("|");
  if (pipe != -1) valorStr = valorStr.substring(0, pipe);

  float media = valorStr.toFloat();
  Serial.print("steps_per_minute: ");
  Serial.println(media);

  atualizarLed(media);
}

void reconectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
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

void setup() {
  Serial.begin(115200);

  pinMode(RED_PIN,   OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN,  OUTPUT);
  setLed(0, 0, 0);

  reconectWiFi();
  MQTT.setServer(BROKER_MQTT, BROKER_PORT);
  MQTT.setCallback(mqtt_callback);

  Serial.println("=================================");
  Serial.println("LED Monitor — step001");
  Serial.println("0 p/min      → apagado");
  Serial.println("1–10 p/min   → azul");
  Serial.println("11–20 p/min  → amarelo");
  Serial.println("21+ p/min    → verde");
  Serial.println("=================================");
}

void loop() {
  verificaConexoes();
  MQTT.loop();
  delay(50);
}