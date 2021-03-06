# -*- coding: utf-8 -*-
"""Yahoo Index Prediction Model 1 Univariate

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18_KQ2v9Ase7JJkER0JppLGg0OMYhT-h8
"""

import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt


#for replicability purposes
tf.random.set_seed(91195003)
##np.random.seed(91190530)
#for an easy reset backend session state
tf.keras.backend.clear_session()

"""1ª Parte"""

#Load dataset
def load_dataset(path):
    return pd.read_csv(path)

#split data into training and validation sets
def split_data(training, perc=10):
    train_idx = np.arange(0, int(len(training)*(100-perc)/100))
    val_idx = np.arange(int(len(training)*(100-perc)/100+1), len(training))
    return train_idx, val_idx

#Plot time series data
def plot_confirmed_cases(data):
    plt.figure(figsize=(8,6))
    plt.plot(range(len(data)), data)
    plt.title('Opening Value of S&P500 Index')
    plt.ylabel('Value')
    plt.xlabel('Days')
    plt.show()

def data_normalization(df, norm_range=(-1, 1)):
    #[-1, 1] for LSTM due to the internal use of tanh by the memory cell
    scaler = MinMaxScaler(feature_range=norm_range)
    #df[['cases']] = scaler.fit_transform(df[['cases']])
    df[['Open']] = scaler.fit_transform(df[['Open']])
    return scaler

#plot learning curve
def plot_learning_curves(hist_list, epochs):
  #accuracies and losses
  acc= hist_list.history['accuracy']
  val_acc=hist_list.history['val_accuracy']
  loss=hist_list.history['loss']
  val_loss=hist_list.history['val_loss']
  epochs_range = range(epochs)
  #creating figura
  plt.figure(figsize=(8,8))
  plt.subplot(1,2,3)
  plt.plot(epochs_range,acc,label='Training Accuracy')
  plt.plot(epochs_range, val_acc, label='Validation Acciracy')
  plt.legend(loc='lower right')
  plt.title('Training/Validation Accuracy')
  plt.subplot(1,2,2)
  plt.plot(epochs_range,loss,label='Training Loss')
  plt.plot(epochs_range,val_loss,label='Validation Loss')
  plt.legend(loc='upper rigth')
  plt.title('Training/Validation Loss')
  plt.show()

"""2ª Parte"""

# build our supervised problem
#Preparing the dataset for the LSTM
def to_supervised(df, timesteps):
    data = df.values
    #print(data)
    X, y = list(), list()

    #iterate over the training set to create X and y, X é um array com 5_timesteps, y será um array com o valor seguinte ao 5 timestep
    dataset_size = len(data)

    for curr_pos in range(dataset_size):
        #end of the input sequence is the current position + the number of timesteps of the input sequence
        input_index = curr_pos + timesteps
        #end of the labels corresponds to the end of the input sequence + 1
        label_index = input_index + 1
        #if we have enough data for this sequence
        if label_index < dataset_size:
            X.append(data[curr_pos:input_index, :])
            y.append(data[input_index:label_index, 0])

    #print(X)
    #print(y)

    #using np.float32 for GPU performance
    return np.array(X).astype('float32'), np.array(y).astype('float32')

"""3ª Parte"""

#Building the model
def rmse(y_true, y_pred):
    return tf.keras.backend.sqrt(tf.keras.backend.mean(tf.keras.backend.square(y_pred - y_true)))

def build_model(timesteps, features, h_neurons=64, activation='tanh'):

    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.LSTM(h_neurons, input_shape=(timesteps, features)))
    model.add(tf.keras.layers.Dense(h_neurons, activation=activation))
    model.add(tf.keras.layers.Dense(1, activation='linear'))

    #model summary (and save it as PNG)
    tf.keras.utils.plot_model(model, 'dowJones_model.png', show_shapes=True)

    return model

"""4ª Parte

Plot learning curves
"""

#plot learning curve
def plot_learning_curves(history, epochs):
  #accuracies and losses
  #dict_keys(['loss', 'mae', 'rmse', 'val_loss', 'val_mae', 'val_rmse'])
  loss=history.history['loss']
  val_loss=history.history['val_loss']
  # mae=history.history['mae']
  # val_mae=history.history['val_mae']
  # rmse=history.history['rmse']
  # val_rmse=history.history['val_rmse']
  epochs_range = range(epochs)
  #creating figure
  plt.figure(figsize=(8,8))
  plt.subplot(1,2,2)
  plt.plot(epochs_range,loss,label='Training Loss')
  plt.plot(epochs_range,val_loss,label='Validation Loss')
  # plt.plot(epochs_range,mae,label='Training MAE')
  # plt.plot(epochs_range,val_mae,label='Validation MAE')
  # plt.plot(epochs_range,rmse,label='Training RMSE')
  # plt.plot(epochs_range,val_rmse,label='Validation RMSE')
  plt.legend(loc='upper right')
  plt.title('Training/Validation Loss')
  plt.show()

################
#4ª PARTE
################
#Compiling and fit the model


def compile_and_fit(model, epochs, batch_size):
  #compile
  model.compile(loss = rmse, optimizer = tf.keras.optimizers.Adam(), metrics = ['mae', rmse])
  #fit
  hist_list = list()
  loss_list = list()

  #callback
  #saving in Keras HDF5 (or h5), a binary data format
  callbacks = [tf.keras.callbacks.ModelCheckpoint(
        filepath='my_model_{epoch}_{val_loss:.3f}.h5',#path where to save model
        save_best_only=True,#overwrite the current checkpoint if and only if
        monitor='val_loss',#the val_loss score has improved
        save_weights_only=False,#if True, only the weigths are saved
        verbose=1,#verbosity mode
        period=5 #save ony at the fifth epoch (5 em 5 epocas) 
        )#,
    #interrupt training if loss stops improving for over 2 epochs
    #tf.keras.callbacks.EarlyStopping(patience=9, monitor='cost')
    ]

  #Time Series Cross Validator
  tscv = TimeSeriesSplit(n_splits=cv_splits)
  for train_index, test_index in tscv.split(X):
    train_idx, val_idx = split_data(train_index, perc=10) #further split into training and validation sets
    #build data
    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_index], y[test_index]

    #print("x_val::::",X_val,"\n","y_val:",y_val,"\n")

    history = model.fit(X_train, y_train, validation_data=(X_val, y_val),epochs=epochs, batch_size=batch_size, shuffle=False, callbacks=callbacks)
    metrics = model.evaluate(X_test, y_test)


    plot_learning_curves(history, epochs)
    hist_list.append(history)


  return model, hist_list

"""5ª parte - Previsão para os próximos N dias"""

#Recursive Multi-Step Forecast!!!
def forecast(model, df, timesteps, multisteps, scaler):
    input_seq = df[-timesteps:].values #getting the last sequence of known value
    inp = input_seq
    forecasts = list()

    #multisteps tells us how many iterations we want to perform, i.e., how many days we want to predict
    for step in range(1, multisteps+1):
        inp = inp.reshape(1,timesteps,1)
        yhat = model.predict(inp) #dá o valor predito normalizado
        yhat_desnormalized = scaler.inverse_transform(yhat) #dá valor predito desnormalizado
        forecasts.append(yhat_desnormalized) #adicionar previsao à lista final de previsões
        #preparar novo input para fazer previsão para o dia seguinte
        inp= np.append(inp[0],yhat) #adiciona previsão recente ao input
        inp = inp[-timesteps:] #vai ao input buscar os ultimos timesteps registados

    return forecasts

def plot_forecast(data, forecasts):

  plt.figure(figsize=(8,6))
  plt.plot(range(len(data)), data['Open'], color='green', label='True value')
  plt.plot(range(len(data)-1, len(data)+len(forecasts)-1), forecasts, color='red', label='Forecasts')
  plt.title('Yahoo stock price')
  plt.ylabel('Value')
  plt.xlabel('Days')
  plt.legend()
  plt.show()

"""**Main execution:**

Parâmetros
"""

# timesteps = 7  # number of days that make up a sequence
n_variate = 1  # number of features used by the model (using conf. cases to predict conf. cases)
# multisteps = 365  # number of days to forecast – we will forecast the next 5 days
# cv_splits = 4  # time series cross validator
# epochs = 25
# batch_size = 7  # 7 sequences of 5 days - which corresponds to a window of 7 days in a batch
df_raw = load_dataset('yahoo_stock.csv')

#Get data from 2015 to the end of 2018
df_raw = df_raw[:1134]
#Get pair to evaluate for time series
#We are going to predict the opening value for each day
df_raw = df_raw.drop(columns=['High','Low','Close','Volume','Adj Close'])
df_raw["Date"] = pd.to_datetime(df_raw["Date"])
df_raw = df_raw.sort_values("Date")
df_raw = df_raw.set_index("Date")

df = df_raw.copy()
#print(df_data.dtypes)
#plot_confirmed_cases(df_data)  # the plot you saw previously
scaler = data_normalization(df)  # scaling data to [-1, 1]
#print(df.head())

# # our supervised problem
# X, y = to_supervised(df, timesteps)
# print("Training shape:", X.shape)
# print("Training labels shape:", y.shape)

# # fitting the model
# model = build_model(timesteps, univariate)
# model, hist_list, loss_list = compile_and_fit(model, epochs, batch_size)

    # Now that we have “tuned” our model, we should retrain it with all the available data
    # (as we did in SBS) and obtain real predictions for tomorrow, the day after, …
    # We want to forecast the next five days after today!

# # Recursive Multi-Step Forecast!!!
# forecasts = forecast(model, df, timesteps, multisteps, scaler)
# for forecast in forecasts:
#   print(forecast)

# #plot_forecast(df_data, forecasts)
# plot_forecast(df_raw, forecasts)

"""##Tunning Function

Tuning Dictionary
"""

"""# Tunning"""

tunning_dict = {               
                1: {'timesteps' : 7, 'multisteps' : 15, 'cv_splits': 3, 'epochs' : 10,  'batch_size' : 5 },
                2: {'timesteps' : 7, 'multisteps' : 15, 'cv_splits' : 3, 'epochs' : 50,  'batch_size' : 5 },
                3: {'timesteps' : 7, 'multisteps' : 15, 'cv_splits' : 3, 'epochs' : 100,  'batch_size' : 5 },

                #
                4: {'timesteps' : 8, 'multisteps' : 15, 'cv_splits': 3, 'epochs' : 60,  'batch_size' : 5 },
                5: {'timesteps' : 8, 'multisteps' : 15, 'cv_splits' : 3, 'epochs' : 90,  'batch_size' : 5 },
                6: {'timesteps' : 8, 'multisteps' : 15, 'cv_splits' : 3, 'epochs' : 120,  'batch_size' : 5 },
                #
                7: {'timesteps' : 10, 'multisteps' : 15, 'cv_splits': 3, 'epochs' : 50,  'batch_size' : 8 },
                8: {'timesteps' : 10, 'multisteps' : 15, 'cv_splits' : 3, 'epochs' : 90,  'batch_size' : 8 },
                9: {'timesteps' : 10, 'multisteps' : 15, 'cv_splits' : 3, 'epochs' : 120,  'batch_size' : 8 }

                }
# record da history de cada modelo
record = {}

for t in tunning_dict:
  #print(record[r])
  # fitting the model
  timesteps = tunning_dict[t]['timesteps']
  epochs = tunning_dict[t]['epochs']
  batch_size= tunning_dict[t]['batch_size']
  multisteps= tunning_dict[t]['multisteps']
  cv_splits = tunning_dict[t]['cv_splits']
  #print(timesteps,epochs,batch_size,cv_splits)

  X, y = to_supervised(df, timesteps)

  model = build_model(timesteps, n_variate)
  model, history = compile_and_fit(model, epochs, batch_size)
  #print("df: ",df.shape," timesteps",timesteps," multisteps ",multisteps)
  forecasts = forecast(model, df, timesteps, multisteps, scaler)

  print(forecasts)

  prev = []

  #plot do valor previsto da ação de Open
  for f in forecasts:
    prev.append(f[0][0])

  print(prev)
  plot_forecast(df_raw, prev)

  #Scorer
  

  record[t] = history

id_tunning = 1
id_split =1

final_dict = {}

for r in record:
#print(tunning_dict[1]['epochs'])
  loss = []
  mae =[]
  rmse = []
  val_loss = []
  val_mae = []
  val_rmse = []

  for h in record[r]:
    #print("Tunning ID:  ",id_tunning," Split ID: ",id_split)
    #plot_learning_curves(h, tunning_dict[id_tunning]['epochs'])
    #['loss', 'mae', 'rmse', 'val_loss', 'val_mae', 'val_rmse']
    #print("loss: ",sum(h.history['loss'])/len(h.history['loss'])," MAE: ",sum(h.history['mae'])/len(h.history['mae'])," RMSE: ",sum(h.history['rmse'])/len(h.history['rmse'])," VAL_LOSS: ",sum(h.history['val_loss'])/len(h.history['val_loss'])," VAL_MAE: ",sum(h.history['val_mae'])/len(h.history['val_mae'])," VAL_RMSE: ",sum(h.history['val_rmse'])/len(h.history['val_rmse']))
    loss.append(sum(h.history['loss'])/len(h.history['loss']))
    mae.append(sum(h.history['mae'])/len(h.history['mae']))
    rmse.append(sum(h.history['rmse'])/len(h.history['rmse']))
    val_loss.append(sum(h.history['val_loss'])/len(h.history['val_loss']))
    val_mae.append(sum(h.history['val_mae'])/len(h.history['val_mae']))
    val_rmse.append(sum(h.history['val_rmse'])/len(h.history['val_rmse']))
    id_split+=1
  id_split=1
  
  final_dict[id_tunning]=[sum(loss)/len(loss), sum(mae)/len(mae),sum(rmse)/len(rmse),sum(val_loss)/len(val_loss),sum(val_mae)/len(val_mae), sum(val_rmse)/len(val_rmse)]

  id_tunning=id_tunning+1

for f in final_dict:
  print("Loss | MAE | RMSE | VAL_LOSS | VAL_MAE | VAL_RMSE")
  print("ID tunning: ",f, " Valores: ",final_dict[f],"\n")

"""Tuning Cycle"""



"""Quantos Historys tenho dentro do record do primeiro tunning : (record é uma dicionário cujos seus valores são listas de historys)"""

print(len(record))

"""Fazer print dos valores registados em cada tunning:"""

id_tunning = 1
id_split =1

final_dict = {}

for r in record:
#print(tunning_dict[1]['epochs'])
  loss = []
  mae =[]
  rmse = []
  val_loss = []
  val_mae = []
  val_rmse = []

  for h in record[r]:
    print("Tunning ID:  ",id_tunning," Split ID: ",id_split)
    #plot_learning_curves(h, tunning_dict[id_tunning]['epochs'])
    #['loss', 'mae', 'rmse', 'val_loss', 'val_mae', 'val_rmse']
    #print("loss: ",sum(h.history['loss'])/len(h.history['loss'])," MAE: ",sum(h.history['mae'])/len(h.history['mae'])," RMSE: ",sum(h.history['rmse'])/len(h.history['rmse'])," VAL_LOSS: ",sum(h.history['val_loss'])/len(h.history['val_loss'])," VAL_MAE: ",sum(h.history['val_mae'])/len(h.history['val_mae'])," VAL_RMSE: ",sum(h.history['val_rmse'])/len(h.history['val_rmse']))
    loss.append(sum(h.history['loss'])/len(h.history['loss']))
    mae.append(sum(h.history['mae'])/len(h.history['mae']))
    rmse.append(sum(h.history['rmse'])/len(h.history['rmse']))
    val_loss.append(sum(h.history['val_loss'])/len(h.history['val_loss']))
    val_mae.append(sum(h.history['val_mae'])/len(h.history['val_mae']))
    val_rmse.append(sum(h.history['val_rmse'])/len(h.history['val_rmse']))
    id_split+=1
  id_split=1
  
  final_dict[id_tunning]=[sum(loss)/len(loss), sum(mae)/len(mae),sum(rmse)/len(rmse),sum(val_loss)/len(val_loss),sum(val_mae)/len(val_mae), sum(val_rmse)/len(val_rmse)]

  id_tunning=id_tunning+1