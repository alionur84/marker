import pandas as pd
import numpy as np
import os
import re


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
    attended_count = len(df.index)
    mean_mark = round(float(df['Puan'].mean()), 2)
    std_dev = round(float(df['Puan'].std()), 2)
    result = {'df': df, 'attended_count': attended_count,
    'mean_mark': mean_mark, 'std_dev': std_dev}
    return result

def stats(df):
    attended_count = len(df.index)
    mean_mark = round(float(df['Puan'].mean()), 2)
    std_dev = round(float(df['Puan'].std()), 2)
    result = {'attended_count': attended_count,
    'mean_mark': mean_mark, 'std_dev': std_dev}
    return result


# not all student ids were numeric if student leaves some characters blank
# so corrected it to all numeric with regex

def convert_datatypes(df):
    # if there are nonnumeric ids
    if len(df.loc[df['TCKimlikNo'].isnull(), ['TCKimlikNo']]) != 0:
        print("lengthdeyim")
        df.loc[df['TCKimlikNo'].isnull(), ['TCKimlikNo']] = "11111111111"
        non_numeric = df.loc[~df['TCKimlikNo'].str.isnumeric()]
        for i in non_numeric.index:
            numeric = re.sub("[^0-9]", "", non_numeric.loc[i, ['TCKimlikNo']][0])
            df.loc[i, ['TCKimlikNo']] = numeric
    df = df.convert_dtypes()
    df['TCKimlikNo'] = df['TCKimlikNo'].astype('Int64')
    df['Adı '] = df['Adı '].astype('str')
    df['Soyadı'] = df['Soyadı'].astype('str')
    df['Puan'] = df['Puan'].astype('Int64')
    return df





'''
def convert_datatypes(df):
    df.loc[df['TCKimlikNo'].isnull(), ['TCKimlikNo']] = "11111111111"
    non_numeric = df.loc[~df['TCKimlikNo'].str.isnumeric()]
    for i in non_numeric.index:
        numeric = re.sub("[^0-9]", "", non_numeric.loc[i, ['TCKimlikNo']][0])
        df.loc[i, ['TCKimlikNo']] = numeric
    df = df.convert_dtypes()
    df['TCKimlikNo'] = df['TCKimlikNo'].astype('Int64')
    df['Adı '] = df['Adı '].astype('str')
    df['Soyadı'] = df['Soyadı'].astype('str')
    df['Puan'] = df['Puan'].astype('Int64')
    return df
'''

# check if they are excel or csv files
def template_concat(path1, path2=None, io_var=False):
    if io_var:
        sablon_o = pd.read_excel(path1)
        sablon_io = pd.read_excel(path2)
        template = pd.concat([sablon_o, sablon_io])
        template.reset_index(inplace=True, drop=True)
        enrolled_count = len(template.index)
        result = {'template_df': template, 'enrolled_count': enrolled_count}
        return result
    else:
        template = pd.read_excel(path1)
        enrolled_count = len(template.index)
        result = {'template_df': template, 'enrolled_count': enrolled_count}
        return result

# some students code their ids wrong this causes duplicate student ids
# first hande them and find the right ones from template
# then create unknown ids dataframe

def id_correct(df, template):
    duplicates = []
    corrected_ids_list = []
    found = []
    
    unknown_ids = df[~df['TCKimlikNo'].isin(template['OgrenciNo_StudentNo'])]    
    duplicated_ids = df.loc[df.duplicated('TCKimlikNo', keep=False)]
    
    if len(duplicated_ids.index) > 0:
        for i in duplicated_ids.index:
            name = duplicated_ids.loc[i, ['Adı ']][0]
            surname = duplicated_ids.loc[i, ['Soyadı']][0]
            for z in template.index:
                if name+surname == template.loc[z, ['Ad_Name']][0] + template.loc[z, ['Soyad_Surname']][0]:
                    if df.loc[i, ['TCKimlikNo']][0] != template.loc[z, ['OgrenciNo_StudentNo'][0]]:# burada numarayı da kontrol et aynıysa doğru farklıysa yanlış yazmış öğrenci
                        unknown_ids.loc[i] = df.loc[i]
                        duplicates.append(i)
                        df.loc[i, ['TCKimlikNo']] = template.loc[z, ['OgrenciNo_StudentNo'][0]]

                    else:
                        continue
                else:
                    continue
                            
    for i in unknown_ids.index:
        name = unknown_ids.loc[i, ['Adı '][0]]
        surname = unknown_ids.loc[i, ['Soyadı'][0]]
        for z in template.index:
            if name+surname == template.loc[z, ['Ad_Name']][0] + template.loc[z, ['Soyad_Surname']][0]:
                #print(template.loc[z, ['OgrenciNo_StudentNo']])
                df.loc[i, ['TCKimlikNo']] = template.loc[z, ['OgrenciNo_StudentNo'][0]]
                found.append(i)
                corrected_ids_list.append(template.loc[z, ['OgrenciNo_StudentNo'][0]])
            
    erasmuslike = unknown_ids[~unknown_ids.index.isin(found)]
    corrected_ids = unknown_ids[unknown_ids.index.isin(found)]
    corrected_ids['corrected_student_id'] = corrected_ids_list

    for i in erasmuslike.index:
        df.drop(i, inplace=True)
    # sometimes optical reader machine reads a paper twice.
    # in order to drop that duplicates below line is added
    df = df.drop_duplicates(subset = 'TCKimlikNo')
    df.sort_values(by='TCKimlikNo', inplace=True)
    df.reset_index(inplace=True, drop=True)
    return df, erasmuslike, corrected_ids
                

'''
def id_correct(df, template):
    unknown_ids = df[~df['TCKimlikNo'].isin(template['OgrenciNo_StudentNo'])]
    found = []
    corrected_ids_list = []
    for i in unknown_ids.index:
        name = unknown_ids.loc[i, ['Adı '][0]]
        surname = unknown_ids.loc[i, ['Soyadı'][0]]
        for z in template.index:
            if name+surname == template.loc[z, ['Ad_Name']][0] + template.loc[z, ['Soyad_Surname']][0]:
                #print(template.loc[z, ['OgrenciNo_StudentNo']])
                df.loc[i, ['TCKimlikNo']] = template.loc[z, ['OgrenciNo_StudentNo'][0]]
                found.append(i)
                corrected_ids_list.append(template.loc[z, ['OgrenciNo_StudentNo'][0]])
            
    erasmuslike = unknown_ids[~unknown_ids.index.isin(found)]
    corrected_ids = unknown_ids[unknown_ids.index.isin(found)]
    corrected_ids['corrected_student_id'] = corrected_ids_list

    for i in erasmuslike.index:
        df.drop(i, inplace=True)
            
    df.sort_values(by='TCKimlikNo', inplace=True)
    df.reset_index(inplace=True, drop=True)
    return df, erasmuslike, corrected_ids
'''

def finalizer(df, template, butunleme=False, grad=False):
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

    if butunleme == False:
        absent[attended.columns[-1]] = -1

    frames = [attended, absent]
    concated = pd.concat(frames)

    concated = concated.sort_values(by=['OgrenciNo_StudentNo'])
    concated = concated.convert_dtypes()
    concated.reset_index(inplace=True, drop=True)
    if grad:
        returned_list = [concated]
        return returned_list

    orgun = concated.loc[concated["OgrenciNo_StudentNo"] < 15000000000]
    io = concated.loc[concated["OgrenciNo_StudentNo"] >= 15000000000]
    
    return orgun, io


