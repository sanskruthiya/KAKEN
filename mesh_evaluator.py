import os
import sys
import codecs
import collections
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

#open an input file
file_name = input('Input csv file >> ')
if os.path.exists(file_name):
    with codecs.open(file_name, 'r', 'utf-8', 'ignore') as f:
        df_xy = pd.read_csv(f)
    base_name = os.path.splitext(os.path.basename(file_name))[0] #file name without extension
else:
    print('Program cancelled due to invalid input. Please enter a correct file name')
    sys.exit()

#input size of a side of mesh
mesh_input = input('Input size of a side of mesh (default=50) >> ')
try:
    mesh_qt = int(mesh_input)
except:
    mesh_qt = 50 #set default value
    print("The size of a side of mesh is set as 50, due to invalid input.")

#input parameter of distance decay
d_input = input('Input distance decay parameter (default=2) >> ')
try:
    d_cost = int(d_input) #check the input. Non-numeric value is denied.
except:
    d_cost = 2
    print('Distance decay parameter is set to 2, due to invalid input.')

#Input parameter of year as a recent year
if not "year" in df_xy.columns:
    y_input = input('Input column name of year for the recent flag >> ')
    year_column = y_input
    if not year_column in df_xy.columns:
        print("Program cancelled due to invalid input. Please enter a correct column name.")
        sys.exit()
else:
    year_column = "year"

log_doc = "Documents : " + str(len(df_xy)) #log the number of documents
print(log_doc)

#get min-max coordinates boundary
min_X = df_xy["x"].min()
max_X = df_xy["x"].max()
min_Y = df_xy["y"].min()
max_Y = df_xy["y"].max()

#generating hex-grid centroid points
x_coord = []
y_coord = []
x_side = ((max_X - min_X) / (mesh_qt - 1)) #x軸方向へのオフセット距離
a_side = 2/3 * x_side #正六角形の重心から各点への距離
y_side = (a_side * np.sqrt(3)) #y軸方向へのオフセット距離
mesh_count = 0
s_count = -1
for i in range(mesh_qt+2): #指定したメッシュ個数分の繰り返し(前後2回分を多くカバーするため＋２) 
    s = min_X + (x_side * (i-1)) #x座標は順番に打つ、ただしx_side一回分は初期値としてオフセットする
    s_count += 1 #x軸方向に何列目にいるのかを把握
    t = min_Y - y_side if s_count % 2 == 0 else min_Y - (y_side * 0.5) #initial Y coordinate
    while t < max_Y + y_side: #打った点のY座標値が上限を超えるまで繰り返し
        x_coord.append(s)
        y_coord.append(t)
        t += y_side
        mesh_count += 1

df_mesh_id = pd.DataFrame()
df_mesh_id['mesh_id'] = pd.RangeIndex(start=0, stop=mesh_count, step=1)
print("The number of mesh :" + str(mesh_count+1))
df_mesh_id["x"] = x_coord
df_mesh_id["y"] = y_coord

count_density_all = []
count_density_wt = []
count_density_201720 = []
count_density_wt201720 = []

df_xy["wt"] = np.sqrt(df_xy["total_grant"])
df_xy["cnt_201720"] = np.where((df_xy[year_column] >= 2017) & (df_xy[year_column] <= 2020), 1, 0)

for i in range(len(df_mesh_id)):
    mesh_x = df_mesh_id["x"][i]
    mesh_y = df_mesh_id["y"][i]
    mesh_dist = ((1 + (((df_xy["x"] - mesh_x) ** 2 + (df_xy["y"] - mesh_y) ** 2) ** 0.5) / a_side) ** d_cost)

    df_cnt_all = 1  / mesh_dist
    df_cnt_all_wt = df_xy["wt"] / mesh_dist
    df_cnt_201720 = df_xy["cnt_201720"] / mesh_dist
    df_cnt_201720_wt = (df_xy["cnt_201720"] * df_xy["wt"]) / mesh_dist

    count_density_all.append(df_cnt_all.sum())
    count_density_wt.append(df_cnt_all_wt.sum())
    count_density_201720.append(df_cnt_201720.sum())
    count_density_wt201720.append(df_cnt_201720_wt.sum())

    sys.stdout.write("\r%d/%d is done." % (i+1, len(df_mesh_id)))

#
df_mesh_id["density_all"] = pd.cut(count_density_all, 20, labels=False, include_lowest=False, duplicates='drop')
df_mesh_id["density_all_wt"] = pd.cut(count_density_wt, 20, labels=False, include_lowest=False, duplicates='drop')
df_mesh_id["density_201720"] = pd.cut(count_density_201720, 20, labels=False, include_lowest=False, duplicates='drop')
df_mesh_id["density_201720_wt"] = pd.cut(count_density_wt201720, 20, labels=False, include_lowest=False, duplicates='drop')

print("\ncreating mesh-document relations...")
nearest_point = NearestNeighbors(n_neighbors=1, algorithm='auto', metric='euclidean').fit(df_mesh_id[["x", "y"]].values)
distances, indices = nearest_point.kneighbors(df_xy[["x", "y"]])
df_nearest = pd.DataFrame(indices, columns=["mesh_id"])
df_xyn = pd.concat([df_xy, df_nearest], axis=1)

mesh_uid = df_xyn['mesh_id'].unique()
mesh_doc_uid = [] #mesh id
mesh_doc_i = [] #mesh size
mesh_key_i = []
mesh_doc_y = []
mesh_key_y = []

for i in mesh_uid:
    key_i_list = []
    key_y_list = []
    recent_flag = str(year_column) + " >= 2017" 
    df_key_uid = df_xyn.query("mesh_id == @i")
    df_key_yid = df_key_uid.query(recent_flag)

    keys_i = np.array(df_key_uid["keywords"])
    keys_y = np.array(df_key_yid["keywords"])
    s = keys_i.T
    t = keys_y.T

    for j in s:
        try:
            l = [x.strip() for x in j.split("|")]
            key_i_list.extend(l)
        except:
            pass
    for k in t:
        try:
            m = [x.strip() for x in k.split("|")]
            key_y_list.extend(m)
        except:
            pass

    #counting
    num_topKey = 10
    ci = collections.Counter(key_i_list)
    cy = collections.Counter(key_y_list)
    #ci_top = ci.most_common(num_topKey)[0:num_topKey]
    ci_top, ci_top_counts = zip(*ci.most_common(num_topKey)[0:num_topKey])
    if len(cy) > num_topKey - 1:
        #cy_top = cy.most_common(num_topKey)[0:num_topKey]
        cy_top, cy_top_counts = zip(*cy.most_common(num_topKey)[0:num_topKey])
    elif len(cy) > 0:
        #cy_top = cy.most_common(len(cy))
        cy_top, cy_top_counts = zip(*cy.most_common(len(cy)))
    else:
        cy_top = "N/A"
    
    mesh_doc_uid.append(i)
    mesh_doc_i.append(len(df_key_uid))
    mesh_doc_y.append(len(df_key_yid))
    mesh_key_i.append(ci_top)
    mesh_key_y.append(cy_top)

df_mesh_key = pd.DataFrame()
df_mesh_key["mesh_id"] = mesh_doc_uid
df_mesh_key["size"] = mesh_doc_i
df_mesh_key["recent_size"] = mesh_doc_y
df_mesh_key["keywords"] = mesh_key_i
#df_mesh_key["keywords_recent"] = mesh_key_y

df_mesh = pd.merge(df_mesh_id, df_mesh_key, on='mesh_id', how='outer', sort=True)

f_name = base_name +"_mesh_" + str(len(df_mesh_id)) + ".tsv"
df_mesh.to_csv(f_name, sep='\t', index=False, encoding='utf-8')

print("Completed.")
