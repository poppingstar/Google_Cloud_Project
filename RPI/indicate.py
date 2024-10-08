import json
import os
import time
import RPi.GPIO as GPIO
from abc import ABC, abstractmethod
from google.cloud import bigquery

GPIO.setmode(GPIO.BCM)

class UnitController(ABC):
  def __init__(self, *pins:int) -> None:
    self._pins=pins
  
    for pin in self._pins:
      GPIO.setup(pin, GPIO.OUT)

  @abstractmethod
  def set_safe(self) -> None:
    pass

  @abstractmethod
  def set_caution(self) -> None:
    pass

  @abstractmethod
  def set_watch(self) -> None:
    pass

  @abstractmethod
  def set_warning(self) -> None:
    pass

  def __del__(self) -> None:
    for pin in self._pins:
      GPIO.setup(pin, GPIO.IN)

class LEDController(UnitController):
  def __init__(self, *led_pins:int) -> None:    
    super().__init__(*led_pins)

  def __set_on(self,*led_pins) -> None:
    leds=led_pins if led_pins else self._pins
    for led in leds:
      GPIO.output(led, True)

  def __set_off(self,*led_pins) -> None:
    leds=led_pins if led_pins else self._pins
    for led in leds:
      GPIO.output(led, False)

  def set_safe(self) -> None:
    self.__set_off()

  def set_caution(self) -> None:
    self.__set_off()
    self.__set_on(self._pins[0])

  def set_watch(self) -> None:
    self.__set_on()

  def set_warning(self) -> None:
    self.__set_off()
    for led in self._pins:
      self.__set_on(led)
      time.sleep(0.15)
      self.__set_off(led)
      time.sleep(0.15)

class BuzzerController(UnitController):
  def __init__(self, *buzzer_pins:int) -> None:
    super().__init__(*buzzer_pins)

  def __set_off(self, *buzzer_pins) -> None:
    buzzers=buzzer_pins if buzzer_pins else self._pins
    for buzzer in buzzers:
      GPIO.output(buzzer,False)

  def set_safe(self) -> None:
    self.__set_off()

  def set_caution(self) -> None:
    self.__set_off()
  
  def set_watch(self) -> None:
    self.__set_off()
  
  def set_warning(self) -> None:
    for pin in self._pins:
      pwm=GPIO.PWM(pin, 640)
      pwm.start(95)
      for scale in range(700,1500,50):
        pwm.ChangeFrequency(scale)
        time.sleep(0.1)

class IntegratedController:
  def __init__(self, *alert_units:tuple[UnitController]) -> None:
    self.__alert_units=alert_units

  def set_safe_all(self) -> None:
    for unit in self.__alert_units:
      unit.set_safe()

  def set_caution_all(self) -> None:
    for unit in self.__alert_units:
      unit.set_caution()

  def set_watch_all(self) -> None:
    for unit in self.__alert_units:
      unit.set_watch()

  def set_warning_all(self) -> None:
    for unit in self.__alert_units:
      unit.set_warning()

class Enquirer:
  def __init__(self) -> None:
    self.__client=bigquery.Client()
  
  def query(self, query) -> int:
    query_job=self.__client.query(query)
    result=query_job.result()

    for count in result:  
      person_count=count['person_count']
    return person_count

def main() -> None:
  settings_path=os.path.join('settings','indicate_settings.json')
  settings_file_data=open_file(settings_path)
  led_pins=settings_file_data['led_pins']
  buzzer_pins=settings_file_data['buzzer_pins']
  credential_path=settings_file_data['credential_path']
  query=settings_file_data['query']
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

  measured_area=int(input('면적을 입력해주세요(단위:m^2): '))

  led=LEDController(*led_pins)
  buzzer=BuzzerController(*buzzer_pins)
  indicater_controler=IntegratedController(led,buzzer)
  enquirer=Enquirer()
  
  while True:
    person_count=enquirer.query(query)
    print(person_count)#테스트용
    density_per_sqmeter=person_count/measured_area

    watch=density_per_sqmeter<=5
    caution=density_per_sqmeter<=4
    safe=density_per_sqmeter<=3.5
    
    if safe:
      indicater_controler.set_safe_all()
    elif caution:
      indicater_controler.set_caution_all()
    elif watch:
      indicater_controler.set_watch_all()
    else:
      indicater_controler.set_warning_all()
    
    time.sleep(1)

def open_file(file_path):
  try:
    with open(file_path, 'r', encoding='utf-8') as file:
      file_data=json.load(file)
      return file_data
  except FileNotFoundError as e:
    print(f'File not found: {e}')
    print(f'Error message: {e}')
    exit()
  except json.JSONDecodeError as e:
    print(f'Error decoding json {e}')
    print(f'Error message: {e}')
    exit()

if __name__=='__main__':
  try:
    main()
  finally:
    GPIO.cleanup()
