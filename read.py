import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv("training_data/message1Results.csv")
string = "["
for i,d in df.iterrows():
    string = string + "[\"\"\""+str(d["Message"])+ "\"\"\","+ str(d["aggr"])+"," + str(d["decept"]) +","+ str(d["encour"]) +","+ str(d["quirky"])+"],\n"
string += "]"
print(string)

