import pandas as pd
import numpy as np
import os


def file_uploader(filepath):
	ext = os.path.splitext(filepath)[-1].lower()
	if ext == ".xls" or ext ==".xlsx":
		df = pd.read_excel(filepath)
		return df
	elif ext ==".csv":
		df = pd.read_csv(filepath)
		return df
	else:
		return "dosya türü desteklenmiyor", ext

def header_dropper(df):
    col_start = df.loc[df[df.columns[2]]=='TCKimlikNo'].index[0]
    df.columns = df.iloc[col_start]
    new_df = df.drop(np.arange(0, col_start + 1))
    new_df.reset_index(inplace=True, drop=True)
    return new_df

def clean_na(df):
    df.dropna(inplace=True, how='all')
    df.dropna(axis=1, how='all', inplace=True)
    df.reset_index(inplace = True, drop = True)
    return df

def convert_datatypes(df):
    df = df.convert_dtypes()
    df['TCKimlikNo'] = df['TCKimlikNo'].astype('Int64')
    return df

# check if they are excel or csv files
def template_concat(path1, path2):
	sablon_o = pd.read_excel(path1)
	sablon_io = pd.read_excel(path2)
	template = pd.concat([sablon_o, sablon_io])
	template.reset_index(inplace=True, drop=True)
	return template

def id_correct(df, template):
    unknown_ids = df[~df['TCKimlikNo'].isin(template['OgrenciNo_StudentNo'])]
    found = []
    for i in unknown_ids.index:
        name = unknown_ids.loc[i, ['Adı '][0]]
        surname = unknown_ids.loc[i, ['Soyadı'][0]]
        for z in template.index:
            if name+surname == template.loc[z, ['Ad_Name']][0] + template.loc[z, ['Soyad_Surname']][0]:
                #print(template.loc[z, ['OgrenciNo_StudentNo']])
                df.loc[i, ['TCKimlikNo']] = template.loc[z, ['OgrenciNo_StudentNo'][0]]
                found.append(i)
            
    erasmuslike = unknown_ids[~unknown_ids.index.isin(found)]

    for i in erasmuslike.index:
        df.drop(i, inplace=True)
            
    df.sort_values(by='TCKimlikNo', inplace=True)
    df.reset_index(inplace=True, drop=True)
    return df, erasmuslike

def finalizer(df, template):
    attended = template[template['OgrenciNo_StudentNo'].isin(df['TCKimlikNo'])]
    absent = template[~template['OgrenciNo_StudentNo'].isin(df['TCKimlikNo'])]
    attended.reset_index(inplace=True, drop=True)
    absent.reset_index(inplace=True, drop=True)
    for i in df.index:
        if df.loc[i, ('TCKimlikNo')] == attended.loc[i, ('OgrenciNo_StudentNo')]:
            if df.loc[i, ('Puan')] <=100:
                attended.loc[i, (attended.columns[-1])] = df.loc[i, ('Puan')]
            else:
                attended.loc[i, (attended.columns[-1])] = 100
            
    absent[attended.columns[-1]] = -1

    frames = [attended, absent]
    concated = pd.concat(frames)

    concated = concated.sort_values(by=['OgrenciNo_StudentNo'])
    concated = concated.convert_dtypes()
    concated.reset_index(inplace=True, drop=True)
    orgun = concated.loc[concated["OgrenciNo_StudentNo"] < 15000000000]
    io = concated.loc[concated["OgrenciNo_StudentNo"] >= 15000000000]
    
    return orgun, io


