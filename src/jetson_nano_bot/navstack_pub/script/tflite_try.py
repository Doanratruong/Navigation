#!/usr/bin/env python
import numpy as np
import tflite_runtime.interpreter as tflite
import random
import pandas as pd

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
list_trieu_chung = []
counter = 0
for column_name in df.columns:
   if counter < 2:
      counter = counter +1
   else:
      print(column_name)
      list_trieu_chung.append(column_name)
	
print('list_trieu_chung:   ',list_trieu_chung)
x_np = x_np.astype(np.float32)

interpreter = tflite.Interpreter(model_path=r"/home/rasp/catkin_ws/src/jetson_nano_bot/navstack_pub/script/model.tflite")
interpreter.allocate_tensors()

# Get input and output tensors.
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("Input Details:", input_details)
print("Output Details:", output_details)


# Assuming you have loaded your new data as new_data_x
new_data_x_R=[]
new_data_x=[]
#manual:
for i in range(85):
  random_number = random.randint(0, 1)
  new_data_x_R.append(random_number)
print('new_data_x_R   ',new_data_x_R)
#auto:
new_data_x.append(new_data_x_R)
new_data_x = np.array(new_data_x)
# Load the saved model
loaded_model = tflite.Interpreter(model_path=r"/home/rasp/catkin_ws/src/jetson_nano_bot/navstack_pub/script/model.tflite")
loaded_model.allocate_tensors()

#Get tensor output and input
input_details = loaded_model.get_input_details()
output_details = loaded_model.get_output_details()

#Convert data from int32 to float32
new_data_x = np.array(new_data_x, dtype=np.float32)
print('new_data_x', new_data_x)

loaded_model.set_tensor(input_details[0]['index'], new_data_x)

#Call loaded_model
loaded_model.invoke()

#Make predictions on new data
predictions = loaded_model.get_tensor(output_details[0]['index'])

#If you want to get the predicted class labels
predicted_labels = np.argmax(predictions, axis=1)

#The variable 'predicted_labels' now contains the predicted class labels for the new data

list_ten_benh = df["Căn bệnh"]
print("predictions  ", predictions)
print(list_ten_benh[predicted_labels])


#Flatten the array
predictions_flat = predictions.flatten()

#Filter values greater than 0.8 and sort them
filtered_predictions = predictions_flat[predictions_flat > 0.8]
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

answer = """qua dữ liệu trên, tôi chuẩn đoán sơ bộ được rằng bạn có thể mắc """
for i in range(len(top_positions)):
   if i == len(top_positions) -1:
      answer = answer + str(list_ten_benh[top_positions[i]]) + " "
   else:
      answer = answer + str(list_ten_benh[top_positions[i]]) + " hoặc "

print(answer)

