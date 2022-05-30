#include <Controllino.h>
#include <SPI.h>

#define ENCODER_USE_INTERRUPTS
#include <Encoder.h>

#define ENCODER_PULSES_PER_METER 7848
#define ENCODER_ROUNDING 3
//every 2 centimeters, the decoder distance is written to the serial bus
#define UPDATE_DISTANCE_METER 0.01
//doesn't have to be extremely accurate, and converting to an int is way faster
#define UPDATE_DISTANCE_TICKS int(ENCODER_PULSES_PER_METER*UPDATE_DISTANCE_METER)

#define HELP_STRING "?: show help \nr: reset encoder to 0\n"
#define RESET_ENCODER_COMMAND 'r'
#define HELP_COMMAND '?'
#define CMD_RESPONSE_CHAR '>'
#define CMD_DEBUG_TOGGLE 'd'

Encoder encoder(CONTROLLINO_IN0, CONTROLLINO_IN1);

char laser_pins[] = {CONTROLLINO_A5, CONTROLLINO_A4, CONTROLLINO_A0, CONTROLLINO_A3, CONTROLLINO_A2, CONTROLLINO_A1};
const int NUM_PINS = sizeof(laser_pins);

char prev_laser_data[NUM_PINS] = {0};
long prev_encoder=0;
bool debug_mode = false;

long debug_prev_encoder = -2147483647; //set long to max value to force value change

void setup() {
  // put your setup code here, to run once:
  for (int i=0; i<NUM_PINS; i++){
    pinMode(laser_pins[i], INPUT);
  }
  Serial.begin(115200); 
}

float encoder_convert_to_meter(long encoder_ticks){
  return -float(encoder_ticks)/ENCODER_PULSES_PER_METER;
}

String encoder_float_to_string(float encoder)
{
  return String(encoder, ENCODER_ROUNDING);
}

void handle_sensors (void) {
  uint8_t sensor_data[NUM_PINS];
  float encoder_distance;
  bool data_changed;
  String encoder_s;
  bool encoder_status;

  data_changed = read_laser_sensors(sensor_data);
  if (data_changed) {
    for (int i=0; i<NUM_PINS; i++){
      Serial.print(sensor_data[i]);
      Serial.print(" ");
    }
    encoder_distance = encoder_convert_to_meter(encoder.read());
    encoder_s = encoder_float_to_string(encoder_distance);
    Serial.println(encoder_s);
  } else {
    //laser data hasn't changed, check if encoder data should be send;
    encoder_status = read_encoder(&encoder_distance);
    if (encoder_status){
      Serial.print(":");
      encoder_s = encoder_float_to_string(encoder_distance);
      Serial.println(encoder_s);
    }
  }
}

void debug_encoder_status(long encoder)
{
  if (encoder != debug_prev_encoder){
    Serial.print(CMD_RESPONSE_CHAR); //debug data hidden in reponse to not effect other parts of software
    Serial.print("[Debug][Encoder] "); 
    Serial.println(encoder);
    debug_prev_encoder = encoder;
  }
}

bool read_encoder(float *encoder_distance)
{
  long current_encoder = encoder.read();

  if (debug_mode){
    debug_encoder_status(current_encoder);
  }
  
  if (prev_encoder+UPDATE_DISTANCE_TICKS < -current_encoder){
    *encoder_distance = encoder_convert_to_meter(current_encoder);
    prev_encoder = -current_encoder;
    return true;
  } else {
    return false;
  }
}

bool read_laser_sensors(uint8_t *sensor_data){
  bool data_changed = false;
  for (int i=0; i<NUM_PINS; i++){
    char laser_status = !digitalRead(laser_pins[i]);
    sensor_data[i] = laser_status;
    if (laser_status != prev_laser_data[i]){
      data_changed = true;
    }
  }
  memmove(prev_laser_data, sensor_data, NUM_PINS);
  return data_changed;
}

void handle_command (void) {
  char command = Serial.read();
  Serial.write(CMD_RESPONSE_CHAR);
  switch (command) {
    case RESET_ENCODER_COMMAND:
      //reset the encoder
      reset();
      Serial.write("System reset\n");
      break;
    case HELP_COMMAND:
      Serial.write(HELP_STRING);
      break;
    case CMD_DEBUG_TOGGLE:
      debug_mode ^= 1;
      break;
    case '\r':
    case '\n':
      break;
    default:
      Serial.write("Unknown command\n");
      break;
  }
}

void reset(void){
  encoder.write(0);
  prev_encoder=0;
  memset(prev_laser_data, 0, NUM_PINS);
}

void loop() {
  // put your main code here, to run repeatedly:
  handle_sensors();
  if (Serial.available()){
    handle_command();
  }
}
