import time
import base64
import cv2
from google.cloud import pubsub_v1

class Video_processor:
  def __init__(self) -> None:
    self.video_path=input('please input path of video file: ')
    self.capture=cv2.VideoCapture(self.video_path)
    self._check_video_path()
    self.video_length=self._get_video_length()
    print(self.video_length)

  def encode_current_frame(self) -> None:
    _, img_nparr=self.capture.read()
    _, img=cv2.imencode('.png', img_nparr)
    img_byte=img.tobytes()
    encoded_img=base64.b64encode(img_byte)
    return encoded_img
  
  def skip_video_per_sec(self, skip_time_sec) -> None:
    skip_time_msec=skip_time_sec*1000
    current_position_msec=self.capture.get(cv2.CAP_PROP_POS_MSEC)
    next_position=current_position_msec+skip_time_msec
    print(f'next position: {next_position}')
    video_length_msec=self.video_length*1000
    print(f'video_length_mesc position: {video_length_msec}')
    is_overrun=next_position>video_length_msec

    if is_overrun:
      self._video_restart()
      print('video is overrun')
    else:
      self.capture.set(cv2.CAP_PROP_POS_MSEC, next_position)

  def _video_restart(self):
    self.capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)

  def _get_video_length(self):
    total_frame=int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps=int(self.capture.get(cv2.CAP_PROP_FPS))
    video_length=int(total_frame/fps)-1
    return video_length

  def _check_video_path(self) -> None:
    correct_path = self.capture.isOpened()

    while not correct_path:
      self.capture.release()    
      print("Please check file path")
      self.video_path=input('Please input path of video file: ')
      self.capture=cv2.VideoCapture(self.video_path)
      correct_path = self.capture.isOpened()

class Ppublisher:
  def __init__(self, topic_id) -> None: 
    self.publisher=pubsub_v1.PublisherClient()
    self.topic_path=topic_id

  def publish(self, product) -> None:
    future=self.publisher.publish(self.topic_path, product)
    
    try:
      future.result()
    except Exception as e:    #기본 재시도 로직 실패시 종료
      print(f"Failed to publish: {e}")
      exit()

def main():
  topic_id='projects/andong-24-team-102/topics/test'
  processor=Video_processor()
  pub=Ppublisher(topic_id)

  while True:
    encoded_img=processor.encode_current_frame()
    pub.publish(encoded_img)
    time.sleep(1)
    processor.skip_video_per_sec(1)

if __name__=='__main__':
  main()
