import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle

data= pd.read_csv('crop_data.csv')

x= data[['N','P','K','rainfall','temperature']]
y= data['label']

x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=0.2, random_state=42)

model= RandomForestClassifier(n_estimators=200, random_state=42)

model.fit(x_train,y_train)

y_pred= model.predict(x_test)

acc= accuracy_score(y_test,y_pred)

print(f"model accuracy:{acc * 100:.2f}%")

with open("crop_model.pkl", "wb") as file:
    pickle.dump(model, file)
print("Model saved successfully as crop_model.pkl")

