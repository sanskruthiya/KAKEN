import pandas as pd
import os
import sys
import codecs
import csv

file_name = input('Input csv file >> ')
if os.path.exists(file_name):
    with codecs.open(file_name, 'r', 'utf-8', 'ignore') as f:
        df = pd.read_csv(f)
    base_name = os.path.splitext(os.path.basename(file_name))[0] #file name without extension
else:
    print('Program cancelled due to invalid input. Please enter correct file name')
    sys.exit

col_len = len(df)
df['description'] = df['研究開始時の研究の概要'].str.cat(df.loc[:,['研究開始時の研究の概要', '研究概要', '研究成果の概要', '研究実績の概要', '今後の研究の推進方策']], sep=' | ', na_rep=' - ')

df2 = pd.DataFrame(columns=['id', 'title', 'description', 'year_range', 'start_year', 'author', 'affiliation', 'category01', 'category02', 'grant', 'grade'])
df2['id'] = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
df2['title'] = df['研究課題名'].replace('[\r\n]', '', regex=True)
df2['description'] = df['description'].replace('[\r\n]', '', regex=True)
df2['year_range'] = df['研究期間 (年度)'].replace('[\r\n]', '', regex=True)
df2['start_year'] = df['研究期間 (年度)'].str[:4]
df2['author'] = df['研究代表者'].replace('[\r\n]', '', regex=True)
df2['affiliation'] = df['研究機関'].replace('[\r\n]', '', regex=True)
df2['category01'] = df['審査区分'].replace('[\r\n]', '', regex=True)
df2['category02'] = df['研究種目'].replace('[\r\n]', '', regex=True)
df2['grant'] = df['総配分額'].replace('[\r\n]', '', regex=True)
df2['grade'] = df['評価記号'].replace('[\r\n]', '', regex=True)

df2.to_csv(base_name + "_summary.csv", encoding="utf-8", index=False, quotechar='"', quoting=csv.QUOTE_ALL)
