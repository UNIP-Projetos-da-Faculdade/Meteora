
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>
#include <BH1750.h>

// ===== WI-FI =====
const char* ssid = ""; 
const char* password = "";

// ===== API DJANGO =====
const char* servidor = "http://10.0.0.114:8000/api/medicoes/";

// ===== SENSORES =====
#define DHT_PIN 4
#define DHT_TYPE DHT22

DHT dht(DHT_PIN, DHT_TYPE);
Adafruit_BMP280 bmp;
BH1750 lightMeter;

bool bmpOK = false;
bool lightOK = false;

unsigned long ultimoEnvio = 0;
const unsigned long intervalo = 10000;

// ===== CONEXÃO WI-FI =====
void conectarWiFi() {
  Serial.print("Conectando ao Wi-Fi");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi conectado!");
  Serial.print("IP da ESP32: ");
  Serial.println(WiFi.localIP());
}

// ===== SETUP =====
void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  dht.begin();

  bmpOK = bmp.begin(0x76);
  if (!bmpOK) {
    bmpOK = bmp.begin(0x77);
  }

  lightOK = lightMeter.begin(
    BH1750::CONTINUOUS_HIGH_RES_MODE
  );

  Serial.println("\n--- SENSORES ---");
  Serial.println(bmpOK ? "BMP280 OK" : "BMP280 nao encontrado");
  Serial.println(lightOK ? "BH1750 OK" : "BH1750 nao encontrado");

  conectarWiFi();
}

// ===== LOOP =====
void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
  }

  if (millis() - ultimoEnvio >= intervalo) {

    Serial.println("Iniciando leitura dos sensores...");
    ultimoEnvio = millis();

    // Leitura dos sensores
    float temperatura = dht.readTemperature();
    float umidade = dht.readHumidity();

    float pressao = NAN;
    if (bmpOK) {
      pressao = bmp.readPressure() / 100.0F;
    }

    float luminosidade = NAN;
    if (lightOK) {
      luminosidade = lightMeter.readLightLevel();
    }

    // Validação
    if (isnan(temperatura) || isnan(umidade) ||
        isnan(pressao) || isnan(luminosidade)) {

      Serial.println("Erro: leitura invalida. Envio cancelado.");
      return;
    }
    Serial.println("Leituras finalizadas!");
    // Exibição das leituras
    Serial.println("\n--- LEITURAS ---");

    Serial.print("Temperatura: ");
    Serial.print(temperatura);
    Serial.println(" °C");

    Serial.print("Umidade: ");
    Serial.print(umidade);
    Serial.println(" %");

    Serial.print("Pressao: ");
    Serial.print(pressao);
    Serial.println(" hPa");

    Serial.print("Luminosidade: ");
    Serial.print(luminosidade);
    Serial.println(" lux");

    // Criação do JSON
    String json = "{";
    json += "\"temperatura\":" + String(temperatura, 2) + ",";
    json += "\"umidade\":" + String(umidade, 2) + ",";
    json += "\"pressao\":" + String(pressao, 2) + ",";
    json += "\"luminosidade\":" + String(luminosidade, 2);
    json += "}";

    // Envio para a API
    HTTPClient http;

    http.begin(servidor);
    http.addHeader("Content-Type", "application/json");

    Serial.println("\nEnviando dados para a API...");

    int resposta = http.POST(json);

    if (resposta > 0) {
      Serial.print("Codigo HTTP: ");
      Serial.println(resposta);

      Serial.println("Resposta do servidor:");
      Serial.println(http.getString());

      if (resposta == 201) {
        Serial.println("Medicao salva com sucesso!");
      }

    } else {
      Serial.print("Falha no envio: ");
      Serial.println(http.errorToString(resposta));
    }

    http.end();

    Serial.println("-------------------------");
  }
}
