#!/usr/bin/env python
import rospy
import subprocess
import random
import pandas as pd
import requests 
from gtts import gTTS
import playsound 
import speech_recognition as sr
import time
import numpy as np
import os
import pyaudio
import wave
import pyaudio
import wave
import audioop
import speech_recognition as sr
import tflite_runtime.interpreter as tflite
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib_msgs.msg import GoalStatus

# global variable:
current_folder = os.getcwd()
language = "vi"
idle_flag = True
idle_counter = 0
robot_state =0
def speak(input_text):
   sound_file_string = r'output.wav'
   soundfile = os.path.join(current_folder, sound_file_string)
   print(soundfile)
   # Create a gTTS object
   tts = gTTS(text=input_text, lang=language)
   # Save the audio file
   tts.save(soundfile)
   
   try:
      playsound.playsound(soundfile,True)
      
   except:
      playsound.playsound(soundfile,True)
   os.remove(soundfile)
   time.sleep(0.5)
   
   print("function speak() run done")


def record_audio(output_filename, record_seconds=10, format=pyaudio.paInt16, channels=1, rate=48000, chunk=1024, input_device_index=1):
   """
   Records audio from the specified input device and saves it to a file.

   Parameters:
   - output_filename: The name of the output file (e.g., 'output.wav').
   - record_seconds: Duration of the recording in seconds (default is 10).
   - format: Audio format (default is pyaudio.paInt16).
   - channels: Number of audio channels (default is 1 for mono).
   - rate: Sample rate in Hz (default is 48000).
   - chunk: Chunk size (default is 1024).
   - input_device_index: Index of the input device (default is 1).
   """

   # Initialize PyAudio
   audio = pyaudio.PyAudio()

   # Open stream
   stream = audio.open(format=format, channels=channels,
                     rate=rate, input=True,
                     frames_per_buffer=chunk, input_device_index=input_device_index)

   print("Recording...")

   frames = []

   # Record audio in chunks
   for _ in range(0, int(rate / chunk * record_seconds)):
      data = stream.read(chunk)
      frames.append(data)

   print("Finished recording.")

   # Stop and close the stream
   stream.stop_stream()
   stream.close()
   audio.terminate()

   # Save the recorded audio as a .wav file
   with wave.open(output_filename, 'wb') as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(audio.get_sample_size(format))
      wf.setframerate(rate)
      wf.writeframes(b''.join(frames))

   print(f"Audio recorded and saved as {output_filename}")

def wait_for_speech(threshold=400, chunk=1024, rate=48000, channels=1, format=pyaudio.paInt16, input_device_index=1):
   """
   Waits for speech to start by monitoring audio input.

   Parameters:
   - threshold: The RMS threshold for detecting speech.
   - chunk: Chunk size.
   - rate: Sample rate in Hz.
   - channels: Number of audio channels.
   - format: Audio format.
   - input_device_index: Index of the input device.
   """

   # Initialize PyAudio
   audio = pyaudio.PyAudio()

   # Open stream
   stream = audio.open(format=format, channels=channels,
                     rate=rate, input=True,
                     frames_per_buffer=chunk, input_device_index=input_device_index)

   print("Waiting for speech...")

   while True:
      data = stream.read(chunk, exception_on_overflow=False)
      rms = audioop.rms(data, 2)  # Calculate RMS of the chunk

      if rms > threshold:
         print("Speech detected!")
         break

   stream.stop_stream()
   stream.close()
   audio.terminate()

def get_voice(output_filename="output.wav", record_seconds=10):
   global idle_flag
   
   
   if idle_flag:
      record_seconds = 4
   # Record audio
   record_audio(output_filename, record_seconds)

   # Initialize recognizer
   r = sr.Recognizer()

   # Load the recorded audio file
   with sr.AudioFile(output_filename) as source:
      print("Me: ", end='')
      audio = r.record(source)

      try:
         text = r.recognize_google(audio, language="vi-VN")
         print(text)
         idle_flag = True
         return text
      except sr.UnknownValueError:
         print("Could not understand audio")
         return 0
      except sr.RequestError as e:
         print(f"Could not request results; {e}")
         return 0
         
def get_text():
   global idle_flag
   for i in range(2):
      text = get_voice()
      print(idle_flag)
      if text:
         print(idle_flag)
         if idle_flag == True:
               idle_flag = False
               return text.lower()
      elif i == 1:
         if idle_flag == False:
               if idle_flag == True:
                  speak("cảm ơn quý khách, charon sẽ quay lại chế độ chờ!")
               idle_flag = True
               blank_return = ""
               print(idle_flag)
               return blank_return


class Chatbot:
   def __init__(self, filepath):
      self.responses = self.load_responses_from_excel(filepath)

   def load_responses_from_excel(self, filepath):
      df = pd.read_excel(filepath)
      responses = {}
      for _, row in df.iterrows():
         question = row['question'].strip().lower()
         response = row['response'].strip()
         if question in responses:
               responses[question].append(response)
         else:
               responses[question] = [response]
      return responses

   def respond(self, message):
      message = message.lower()
      best_match, confidence = process.extractOne(message, self.responses.keys(), scorer = fuzz.token_sort_ratio)
      if confidence > 60: 
         return random.choice(self.responses[best_match])
      tra_ve = "Xin lỗi, tôi không hiểu bạn đang nói gì. bạn có thế nói lại không?"
      return tra_ve
      
def import_data():
   global list_trieu_chung
   global list_ten_benh
   global df
   #Specify the file path
   file_path = r"/home/rasp/catkin_ws/src/jetson_nano_bot/navstack_pub/script/benh_trieuchung_dataset.xlsx"

   #Read the Excel file into a pandas DataFrame
   df = pd.read_excel(file_path)

   #Display the DataFrame
   print(df)

   df_data_x = df.drop(columns=["Căn bệnh","STT"])
   data_x = df_data_x.values.tolist()

   data_y = []

   for i in range(len(df)):
      row = df.iloc[i]
      row = row[2:]
      row = row.values
      df_data_y = []
      
      raw_row = list(row)
      for a in range(len(df)):
         if a==i:
            df_data_y.append(1)
         else:
            df_data_y.append(0)
      data_y.append(df_data_y)
      
   x_shape = len(data_x[1])
   y_shape = len(data_y[1])
   x_np = np.array(data_x)
   y_np = np.array(data_y)

   x_np = x_np.astype(np.float32)	
   list_trieu_chung = []
   counter =0
   for column_name in df.columns:
      if counter < 1:
         counter = counter +1
      else:
               print(column_name)
               list_trieu_chung.append(column_name)
   list_ten_benh = df["Căn bệnh"]

def prepare_data_for_prediction(text):
   new_data_x_R=[]
   new_data_x=[]
   global list_trieu_chung
   for i in range(85):
      if list_trieu_chung[i].lower() in text:
         new_data_x_R.append(1)
      else:
         new_data_x_R.append(0)
   new_data_x.append(new_data_x_R)
   new_data_x = np.array(new_data_x,dtype=np.float32)
   #new_data_x = np.array(new_data_x, dtype=np.float32)
   print('new_data_x: ',new_data_x)
   return new_data_x
def predict(text):
   global robot_state
   input_for_load_model = ""
   loaded_model = tflite.Interpreter(model_path=r"/home/rasp/catkin_ws/src/jetson_nano_bot/navstack_pub/script/model.tflite")
   loaded_model.allocate_tensors()
   input_details = loaded_model.get_input_details()
   output_details = loaded_model.get_output_details()
   input_for_load_model = prepare_data_for_prediction(text)
   loaded_model.set_tensor(input_details[0]['index'], input_for_load_model)
   #Call loaded_model
   loaded_model.invoke()
   #Make predictions on new data
   predictions = loaded_model.get_tensor(output_details[0]['index']) 
   #Flatten the array
   predictions_flat = predictions.flatten()

   #Filter values greater than 0.8 and sort them
   filtered_predictions = predictions_flat[predictions_flat > 0.5]
   sorted_predictions = np.sort(filtered_predictions)[::-1]

   #Keep the top 3 values
   top_3_predictions = sorted_predictions[:3]

   #Create a mask for the top 3 values
   mask = np.zeros_like(predictions_flat, dtype=bool)
   for value in top_3_predictions:
      mask |= (predictions_flat == value)

   #Set values not in the top 3 to 0
   predictions_flat[~mask] = 0

   #Reshape the array back to its original shape
   filtered_predictions = predictions_flat.reshape(predictions.shape)

   print("Filtered predictions with only the top 3 values > 0.8 retained:")
   print(filtered_predictions)

   #Filter out zero values and get their indices
   non_zero_indices = np.nonzero(predictions_flat)[0]
   non_zero_values = predictions_flat[non_zero_indices]

   #Sort the non-zero values in descending order and get the top values' indices
   sorted_non_zero_indices = non_zero_indices[np.argsort(non_zero_values)[::-1]]

   #Get the top 3 positions or less if fewer than 3 non-zero values exist
   top_positions = sorted_non_zero_indices[:3]

   print(f"Top positions in the array: {top_positions}")


   if len(top_positions) == 0 or (len(top_positions) == 1 and 'Viêm nhiễm phụ khoa' in list_ten_benh[top_positions[0]]):
      answer = "not predict"
      robot_state = 1
   else:
      answer = """qua dữ liệu trên, tôi chuẩn đoán sơ bộ được rằng khả năng cao bạn có thể đang mắc bệnh """
      for i in range(len(top_positions)):
         if i == len(top_positions) -1:
            answer = answer + str(list_ten_benh[top_positions[i]]) + "."
         else:
            answer = answer + str(list_ten_benh[top_positions[i]]) + " hoặc bệnh "
      robot_state = 2
   return answer
def recommend_clinics(input_string):
   # Từ điển ánh xạ bệnh với phòng khám
   disease_to_clinic = {
      "Cảm lạnh": "Phòng khám hô hấp",
      "Cảm cúm": "Phòng khám hô hấp",
      "Hen phế quản": "Phòng khám hô hấp",
      "Phổi tắc nghẽn mãn tính": "Phòng khám hô hấp",
      "Lao phổi": "Phòng khám hô hấp",
      "Viêm phế quản": "Phòng khám hô hấp",
      "Viêm họng": "Phòng khám hô hấp",
      "Viêm xoang": "Phòng khám hô hấp",
      "Cường giáp": "Phòng khám nội tiết",
      "Suy giáp": "Phòng khám nội tiết",
      "Tiểu đường": "Phòng khám nội tiết",
      "Hội chứng cushing": "Phòng khám nội tiết",
      "Tăng sinh lành tính tuyết tiền liệt": "Phòng khám nội tiết",
      "Hội chứng vành cấp": "Phòng khám tim mạch",
      "Suy tim": "Phòng khám tim mạch",
      "Bệnh Tăng huyết áp": "Phòng khám tim mạch",
      "Suy van tĩnh mạch chân": "Phòng khám tim mạch",
      "Gout": "Phòng khám cơ xương khớp",
      "Viêm khớp": "Phòng khám cơ xương khớp",
      "Thoát vị đĩa đệm cột sống cổ": "Phòng khám cơ xương khớp",
      "Trào ngược dạ dày, thực quản": "Phòng khám tiêu hóa",
      "Sỏi thận": "Phòng khám tiêu hóa",
      "Suy thận mãn tính": "Phòng khám tiêu hóa",
      "Viêm loét dạ dày, tá tràng": "Phòng khám tiêu hóa",
      "Viêm ruột thừa": "Phòng khám tiêu hóa",
      "Viêm túi mật cấp": "Phòng khám tiêu hóa",
      "Viêm tắc đường mật": "Phòng khám tiêu hóa",
      "Viêm gan siêu vi cấp": "Phòng khám tiêu hóa",
      "Xơ gan": "Phòng khám tiêu hóa",
      "Ung thư dạ dày": "Phòng khám tiêu hóa",
      "Ung thư trực tràng": "Phòng khám tiêu hóa",
      "Sốt xuất huyết": "Phòng khám truyền nhiễm",
      "Sởi": "Phòng khám truyền nhiễm",
      "Thủy đậu": "Phòng khám truyền nhiễm",
      "Viêm màng não": "Phòng khám truyền nhiễm",
      "Viêm cầu thận cấp hậu nhiễm liên cầu trùng": "Phòng khám truyền nhiễm",
      "Viêm tai giữa cấp": "Phòng khám truyền nhiễm",
      "Nhiễm trùng tiểu": "Phòng khám truyền nhiễm",
      "Viêm nhiễm phụ khoa": "Phòng khám truyền nhiễm",
      "Bệnh truyền nhiễm qua đường tình dục": "Phòng khám truyền nhiễm",
      "Nấm da": "Phòng khám da liễu",
      "Thai ngoài tử cung": "Phòng khám sản phụ khoa",
      "U buồng trứng": "Phòng khám sản phụ khoa",
      "Ung thư vú": "Phòng khám sản phụ khoa",
      "Thiếu máu, thiếu sắt": "Phòng khám huyết học",
      "Xuất huyết giảm tiểu cầu": "Phòng khám huyết học",
      "Ung thư tuyến giáp": "Phòng khám ung bướu",
      "Viêm nhiễm phụ khoa": "Phòng khám phụ khoa",
      "Viêm tắc đường mật": "Phòng khám tiêu hóa",
   }

   # Lấy các bệnh từ chuỗi đầu vào
   start_index = input_string.find("bệnh")
   diseases_part = input_string[start_index:]
   diseases = [d.strip() for d in diseases_part.split(",")]

   # Danh sách lưu các phòng khám theo thứ tự của bệnh được nhắc đến trong input_string
   clinics_to_visit = []
   for disease in diseases:
      disease_name = disease.replace("bệnh ", "")
      if disease_name in disease_to_clinic and disease_to_clinic[disease_name] not in clinics_to_visit:
         clinics_to_visit.append(disease_to_clinic[disease_name])
   
   # Định dạng chuỗi kết quả
   if clinics_to_visit:
      clinics_string = ', '.join(clinics_to_visit[:-1]) + " và " + clinics_to_visit[-1] if len(clinics_to_visit) > 1 else clinics_to_visit[0]
      output_string = f"Theo kết quả chuẩn đoán trên, bạn nên đi đến {clinics_string} để được kiểm tra kỹ càng hơn."
   else:
      output_string = "Không có thông tin về các bệnh được nhắc đến trong yêu cầu của bạn."
   return output_string, clinics_to_visit
def set_goal_based_on_text(text):
   rospy.init_node('simple_navigation_goals')

   # Create the SimpleActionClient, passing the type of the action to the constructor.
   client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
   
   # Wait for the action server to come up.
   rospy.loginfo("Waiting for the move_base action server to come up")
   client.wait_for_server()

   # Danh sách các phòng khám và tọa độ tương ứng
   destinations = {
      "Phòng khám hô hấp": {"x": 5.1486, "y": 0.7, "w": 1.0},
      "Phòng khám nội tiết": {"x": 12.3676, "y": 0.7, "w": 1.0},
      "Phòng khám tim mạch": {"x": 19.5, "y": 0.7, "w": 1.0},
      "Phòng khám cơ xương khớp": {"x": 0.0, "y": 0.0, "w": 1.0},
      "Phòng khám tiêu hóa": {"x": 24.389, "y": 0.7, "w": 1.0},
      "Phòng khám truyền nhiễm": {"x": 0.0, "y": 0.0, "w": 1.0},
      "Phòng khám da liễu": {"x": 0.0, "y": 0.0, "w": 1.0},
      "Phòng khám sản phụ khoa": {"x": 0.0, "y": 0.0, "w": 1.0},
      "Phòng khám huyết học": {"x": 0.0, "y": 0.0, "w": 1.0},
      "Phòng khám ung bướu": {"x": 0.0, "y": 0.0, "w": 1.0},
      "Phòng khám phụ khoa": {"x": 0.0, "y": 0.0, "w": 1.0}
   }

   # Tìm phòng khám đầu tiên được nhắc đến trong văn bản
   selected_clinic = None
   if len(text) > 0:
      for clinic in destinations.keys():
         if clinic == text[0]:
            selected_clinic = clinic
            break

   if selected_clinic:
      selected_place = destinations[selected_clinic]
      goal = MoveBaseGoal()
      goal.target_pose.header.frame_id = "map"
      goal.target_pose.header.stamp = rospy.get_rostime()
      goal.target_pose.pose.position.x = selected_place['x']
      goal.target_pose.pose.position.y = selected_place['y']
      goal.target_pose.pose.orientation.w = selected_place['w']

      client.send_goal(goal)
      rospy.loginfo(f"Sending goal to {selected_clinic}")
      client.wait_for_result()

      if client.get_state() == GoalState.SUCCEEDED:
         speak(f"chúng ta đã đến {selected_clinic}, mời bạn vào khám ạ. giờ tôi sẽ quay lại. cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!")
         time.sleep(4)
         goal = MoveBaseGoal()
         goal.target_pose.header.frame_id = "map"
         goal.target_pose.header.stamp = rospy.get_rostime()
         goal.target_pose.pose.position.x = 0
         goal.target_pose.pose.position.y = 0
         goal.target_pose.pose.orientation.w = 1.0

         client.send_goal(goal)
         rospy.loginfo(f"Sending goal to base")
         client.wait_for_result()
      else:
         rospy.loginfo("The robot failed to reach the goal location for some reason")
   else:
      rospy.loginfo("No valid clinic found in the input text.") 
def main():
   global idle_flag
   idle_flag = True
   recomended_clinnic = False
   bot = Chatbot('/home/rasp/catkin_ws/src/jetson_nano_bot/navstack_pub/script/chatbot.xlsx')
   import_data()
   while True:
      # Wait for speech to start
      wait_for_speech()
      while idle_flag:
         get_text()
         text_result =""
      if idle_flag == False:  
         speak("xin chào quý khách, tôi là charon , một robot trợ giúp khám bệnh.. xin hỏi quý khách đang gặp phải những triệu chứng gì ạ?")
         #speak("what's your name?")
         while idle_flag == False:
            print("-------------------------")
            print('idle_flag',idle_flag)
            text_result = get_text()
            time.sleep(0.3)
            print(text_result)
            if text_result != "":
               predict_result = predict(text_result)
               print('predict_result',predict_result)
               if True:#robot_state !=2:
                  if predict_result != "not predict":
                     #speak(text_result)
                     speak(predict_result)
                     time.sleep(1)
                     speak_phong_kham,phong_kham = recommend_clinics(predict_result)
                     speak(speak_phong_kham)
                     recomended_clinnic= True
                  else:
                     chatbot_responded = bot.respond(predict_result)
                     if recomended_clinnic and chatbot_responded == "accepted":
                        set_goal_based_on_text(phong_kham)
                     elif recomended_clinnic and chatbot_responded == "lead the way":
                        set_goal_based_on_text(predict_result)
                     else:
                        speak(chatbot_responded)
                     
                  
if __name__ == '__main__':
   main()
