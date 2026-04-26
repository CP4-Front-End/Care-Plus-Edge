#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ── Identificação do dispositivo ──────────────────────────
const char* topicPrefix = "step001";
// ─────────────────────────────────────────────────────────

// ── WiFi / MQTT ───────────────────────────────────────────
const char* SSID             = "Wokwi-GUEST";
const char* PASSWORD         = "";
const char* BROKER_MQTT      = "35.247.231.140";
const int   BROKER_PORT      = 1883;
const char* TOPICO_SUBSCRIBE = "/TEF/step001/cmd";
const char* TOPICO_ATTRS     = "/ul/TEF/step001/attrs";
const char* ID_MQTT          = "fiware_step001";
// ─────────────────────────────────────────────────────────

// ── Pedômetro ─────────────────────────────────────────────
const int          PASSOS_MINIMOS = 10;
const unsigned long JANELA_MS    = 30UL * 1000;
const unsigned long PUBLISH_MS   = 10UL * 1000;
// ─────────────────────────────────────────────────────────

// ── Servo / LEDC ──────────────────────────────────────────
const int      SERVO_PIN      = 19;
const int      LEDC_FREQ      = 50;
const int      LEDC_RES       = 16;
const uint32_t SERVO_NEUTRO   = 4915;
const uint32_t SERVO_A        = 3900;
const uint32_t SERVO_B        = 5900;
const int      VIBRA_DELAY_MS = 80;
// ─────────────────────────────────────────────────────────

// ── Botões ────────────────────────────────────────────────
const int BTN_MISSAO_OK  = 25;
const int BTN_MISSAO_SAI = 32;
const int BTN_AGUA       = 33;
const int BTN_SOS        = 26;

const unsigned long DEBOUNCE_MS = 200;
const unsigned long SOS_HOLD_MS = 3000;

bool          estadoAnteriorBtn[4] = {HIGH, HIGH, HIGH, HIGH};
unsigned long ultimoDebounce[4]    = {0, 0, 0, 0};
unsigned long pressaoInicioSOS     = 0;
bool          sosAguardando        = false;
// ─────────────────────────────────────────────────────────

WiFiClient       espClient;
PubSubClient     MQTT(espClient);
Adafruit_MPU6050 mpu;
sensors_event_t  event;

int           passos        = 0;
int           passosJanela  = 0;
unsigned long ultimoPasso   = 0;
unsigned long inicioJanela  = 0;
unsigned long ultimoPublish = 0;
float         anterior      = 0;
bool          vibrando      = false;

// ── Servo ─────────────────────────────────────────────────
void servoWrite(uint32_t duty) {
  ledcWrite(SERVO_PIN, duty);
}

void vibrar() {
  static bool          lado           = false;
  static unsigned long ultimaVibracao = 0;
  if (millis() - ultimaVibracao >= VIBRA_DELAY_MS) {
    servoWrite(lado ? SERVO_A : SERVO_B);
    lado = !lado;
    ultimaVibracao = millis();
  }
}

void pararVibrar() {
  servoWrite(SERVO_NEUTRO);
  vibrando = false;
  Serial.println(">> Vibração parada.");
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

// ── MQTT ──────────────────────────────────────────────────
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.print("Comando recebido: ");
  Serial.println(msg);

  String aguaCmd = String(topicPrefix) + "@agua|";
  if (msg.equals(aguaCmd)) {
    Serial.println(">> Comando 'agua' recebido. (não implementado ainda)");
  }
}

void reconnectMQTT() {
  while (!MQTT.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (MQTT.connect(ID_MQTT)) {
      Serial.println(" conectado!");
      MQTT.subscribe(TOPICO_SUBSCRIBE);
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

// ── Publish ───────────────────────────────────────────────
void publicarDados() {
  float mediaMin = (float)passosJanela * (60000.0 / PUBLISH_MS);

  char payload[64];
  snprintf(payload, sizeof(payload), "p|%d|m|%.1f", passos, mediaMin);
  MQTT.publish(TOPICO_ATTRS, payload);

  Serial.println("─────────────────────────────────");
  Serial.print("Publicado | Passos totais: ");
  Serial.print(passos);
  Serial.print(" | Média: ");
  Serial.print(mediaMin);
  Serial.println(" passos/min");
  Serial.println("─────────────────────────────────");

  passosJanela = 0;
}

void publicarBotao(const char* evento) {
  char payload[64];
  snprintf(payload, sizeof(payload), "b|%s", evento);
  MQTT.publish(TOPICO_ATTRS, payload);
  Serial.print("Botao publicado: ");
  Serial.println(payload);
}

// ── Botões ────────────────────────────────────────────────
void initBotoes() {
  pinMode(BTN_MISSAO_OK,  INPUT_PULLUP);
  pinMode(BTN_MISSAO_SAI, INPUT_PULLUP);
  pinMode(BTN_AGUA,       INPUT_PULLUP);
  pinMode(BTN_SOS,        INPUT_PULLUP);
}

void lerBotoes() {
  unsigned long agora = millis();
  int pinos[4] = {BTN_MISSAO_OK, BTN_MISSAO_SAI, BTN_AGUA, BTN_SOS};

  // ── Botões 1, 2 e 3 — clique simples ───────────────
  for (int i = 0; i < 3; i++) {
    bool leitura = digitalRead(pinos[i]);

    if (leitura != estadoAnteriorBtn[i]) {
      ultimoDebounce[i] = agora;
      estadoAnteriorBtn[i] = leitura;
    }

    if ((agora - ultimoDebounce[i]) >= DEBOUNCE_MS && leitura == LOW) {
      switch (i) {
        case 0:
          publicarBotao("missao_progresso");
          Serial.println(">> Progresso na missão registrado.");
          break;
        case 1:
          publicarBotao("missao_saiu");
          Serial.println(">> Saiu da missão.");
          break;
        case 2:
          publicarBotao("agua_confirmada");
          Serial.println(">> Hidratação confirmada.");
          if (vibrando) pararVibrar();
          break;
      }
      // Força estado HIGH para não repetir enquanto segurar
      estadoAnteriorBtn[i] = HIGH;
    }
  }

  // ── Botão 4 — SOS com pressão longa de 3s ──────────
  bool leituraSOS = digitalRead(BTN_SOS);

  if (leituraSOS != estadoAnteriorBtn[3]) {
    ultimoDebounce[3]    = agora;
    estadoAnteriorBtn[3] = leituraSOS;
  }

  if (agora - ultimoDebounce[3] >= DEBOUNCE_MS) {
    if (leituraSOS == LOW && !sosAguardando) {
      sosAguardando    = true;
      pressaoInicioSOS = agora;
    }
    if (leituraSOS == HIGH && sosAguardando) {
      sosAguardando = false;
    }
    if (sosAguardando && (agora - pressaoInicioSOS >= SOS_HOLD_MS)) {
      publicarBotao("sos");
      Serial.println(">> SOS enviado!");
      sosAguardando = false;
    }
  }
}

// ── Setup ─────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  while (!mpu.begin()) {
    Serial.println("MPU6050 não encontrado...");
    delay(1000);
  }
  Serial.println("MPU6050 pronto!");

  ledcAttach(SERVO_PIN, LEDC_FREQ, LEDC_RES);
  servoWrite(SERVO_NEUTRO);

  initBotoes();

  initWiFi();
  MQTT.setServer(BROKER_MQTT, BROKER_PORT);
  MQTT.setCallback(mqtt_callback);

  inicioJanela  = millis();
  ultimoPublish = millis();

  Serial.println("=================================");
  Serial.print("Dispositivo: ");
  Serial.println(topicPrefix);
  Serial.print("Meta: ");
  Serial.print(PASSOS_MINIMOS);
  Serial.print(" passos em ");
  Serial.print(JANELA_MS / 1000);
  Serial.println("s");
  Serial.println("=================================");
}

// ── Loop ──────────────────────────────────────────────────
void loop() {
  unsigned long agora = millis();

  verificaConexoes();
  MQTT.loop();

  // ── Leitura do acelerômetro ─────────────────────────
  mpu.getAccelerometerSensor()->getEvent(&event);
  float total = sqrt(
    event.acceleration.x * event.acceleration.x +
    event.acceleration.y * event.acceleration.y +
    event.acceleration.z * event.acceleration.z
  );

  // ── Detecção de passo ───────────────────────────────
  float delta = total - anterior;
  if (delta > 3 && agora - ultimoPasso > 500) {
    passos++;
    passosJanela++;
    ultimoPasso = agora;

    unsigned long restante = (JANELA_MS - (agora - inicioJanela)) / 1000;
    Serial.print("Passo! Total: ");
    Serial.print(passos);
    Serial.print(" | Janela restante: ");
    Serial.print(restante);
    Serial.println("s");

    if (vibrando) pararVibrar();
  }
  anterior = total;

  // ── Leitura dos botões ──────────────────────────────
  lerBotoes();

  // ── Publica a cada PUBLISH_MS ───────────────────────
  if (agora - ultimoPublish >= PUBLISH_MS) {
    publicarDados();
    ultimoPublish = agora;
  }

  // ── Avaliação da janela de meta ─────────────────────
  if (agora - inicioJanela >= JANELA_MS) {
    Serial.println("=================================");
    Serial.print("Janela encerrada. Passos: ");
    Serial.print(passos);
    Serial.print(" / Meta: ");
    Serial.println(PASSOS_MINIMOS);

    if (passos < PASSOS_MINIMOS) {
      Serial.print("Meta não atingida! Faltaram ");
      Serial.print(PASSOS_MINIMOS - passos);
      Serial.println(" passos. Vibrando...");
      vibrando = true;
    } else {
      Serial.println("Meta atingida!");
    }
    Serial.println("=================================");

    passos       = 0;
    inicioJanela = agora;
  }

  // ── Vibração ────────────────────────────────────────
  if (vibrando) vibrar();

  delay(50);
}