

#include <DHT.h>


//#include "DHT.h"
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

int land,pan,lamp,light,h, t;
String a;
String comdata = "";//声明字符串变量
char data; 
boolean not_started = true;

void execute(String message)
{
  /* d9:1,d10:1,d11:1, 
   * d9 : digital write 9
   * d10 : digital write 10
   */
   int startPosition, commaPosition;

   
   startPosition = 0;
   commaPosition = message.indexOf(',');
   while(commaPosition != -1)
   {
     String executeCommand = message.substring(startPosition,commaPosition);  //d9:1
   
     int colonPosition = executeCommand.indexOf(':');
     int pinNumber = executeCommand.substring(1, colonPosition).toInt();
     String output_command = executeCommand.substring(colonPosition+1, executeCommand.length());
     if (output_command == "a"){
//        land = analogRead(A0);
//        h = dht.readHumidity();
//        t = dht.readTemperature();
        output_command="1";
     }
     
     if (executeCommand[0] == 'D'){
        digitalWrite(pinNumber, output_command.toInt());
        Serial.print('D'); 
        Serial.print(pinNumber); 
        Serial.print(':'); 
        Serial.print(output_command); 
        Serial.print(','); 
     }
//     else if (executeCommand[0] == 'A')
//        analogWrite(pinNumber, output_command);  

     message = message.substring(commaPosition+1, message.length());
     startPosition = 0;
     commaPosition = message.indexOf(',');
   }
}

void setup() 
{
  Serial.begin(115200);      //设定的波特率
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  digitalWrite(9,0);
  digitalWrite(10,0);
  digitalWrite(11,0);
  
}
 
void loop() 
{
  boolean receive_over = false;
  if (not_started) {
    Serial.write("s\n");
    Serial.flush();
    not_started = false;
  }
  
   if (Serial.available() > 0)  
    {
        data = char(Serial.read());
        if (data==']') {
         receive_over = true;
        }
        else comdata+=data;
   }

    if (receive_over){
//        Serial.println("cd:"+comdata);
        String reply_data = "";
        if (comdata == "cgd"){
          land = analogRead(A0);
          h = dht.readHumidity();
          t = dht.readTemperature();
          reply_data = "Land:"+String(land)+",Humidity:"+String(h)+",Temperature:"+String(t)+"[";
        }
          
        else{
          /*  
           * 
           */
          execute(comdata);
          reply_data = "[";
        }
        Serial.print(reply_data);
        comdata = "";
    }
}
