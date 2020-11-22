#!/usr/bin/env python
# coding: utf-8

# In[1]:


import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


# In[2]:


# convert the second row as the header, getting rid of !!
def convertHeader(df):
    df['GEO_ID'] = df['GEO_ID'].str[9:]
    df= df.rename(columns={'GEO_ID':'GEOID10'})
    df.columns = df.iloc[0]
    df = df.drop(index= 0).rename(columns = {"":'GEOID10'})

    cols = df.columns.tolist()
    for i in range(len(cols)):
        col = cols[i].replace( '!!',' ')
        cols[i] = col
    df.columns = cols
    return df

# find num of students of age 5-10 of each race in each block
def countElemStudents(df,race):
    elem_members = ['GEOID10','Total Male 5 to 9 years','Total Female 5 to 9 years','Total Male 10 to 14 years','Total Female 10 to 14 years']
    df_elem = df.loc[:,elem_members]
    for col in elem_members:#convert all columns to number format
        if col != 'GEOID10':
            df_elem[col] = pd.to_numeric(df_elem[col],errors = 'coerce')
    #assume kids are evenly distributed over different ages, so divide the column value by 5
    df_elem['Total Male 10 to 14 years'] = df_elem['Total Male 10 to 14 years']/5
    df_elem['Total Female 10 to 14 years'] = df_elem['Total Female 10 to 14 years']/5
    #sum over kids of all ages and genders
    df_elem['Total_{}'.format(race)] = df_elem.sum(axis = 1)
    return df_elem.loc[:,['GEOID10','Total_{}'.format(race)]]


# ## Import enrollment and geographic information of schools

# In[26]:


def get_schl_info():
    elem_durham =  gpd.read_file(r'./../data/elem_durham/elem_durham.shp')
    elem_durham_addr = pd.read_csv(r'./../data/map_distance.csv')
    elem_durham_addr['coords'] = elem_durham_addr.apply(lambda x: (x['long'],x['lat']), axis = 1)
    elem_durham_basic = pd.concat([elem_durham.loc[:,['name','member']], elem_durham_addr.loc[:,'coords']],axis = 1)


    magnet_basic = pd.read_csv(r'./../data/magnet_data.csv')
    magnet_basic['coords'] = magnet_basic.apply(lambda x: (x['long'],x['lat']), axis = 1)
    magnet_basic = magnet_basic.drop(columns = ['long','lat'])
    elem_durham_basic = pd.concat([elem_durham_basic,magnet_basic]).reset_index().drop(columns=['index'])
    return elem_durham_basic

def get_blk_info():
    block_durham = gpd.read_file(r'./../data/blk_shapefiles/tl_2018_37063_faces.shp')

    block_durham['coords'] = block_durham['geometry'].apply(lambda x: x.representative_point().coords[:])
    block_durham['coords'] = [coords[0] for coords in block_durham['coords']]
    block_durham['GEOID10'] = block_durham['STATEFP10'] + block_durham['COUNTYFP10'] + block_durham['TRACTCE10'] + block_durham['BLOCKCE10']
    block_durham = block_durham.dropna(subset = ['TFID'])
    block_durham = block_durham.dissolve(by='GEOID10', aggfunc='sum').reset_index()

    # write racial population information to each block
    all_races = ['W','A','M','H','B']
    for race in all_races:
        df_race = pd.read_csv(r'./../data/sex_age_race/sex_by_age_{}.csv'.format(race))
        df_race = convertHeader(df_race)
        df_race_elem = countElemStudents(df_race,race)
        block_durham = pd.merge(block_durham, df_race_elem, how = 'inner')

    # aggregate population information into block groups
    block_durham['BLKGRP'] = block_durham['GEOID10'].apply(lambda x: str(x)[:12])
    block_durham = block_durham.dissolve(by='BLKGRP', aggfunc='sum').reset_index()
    block_durham['coords'] = block_durham['geometry'].apply(lambda x: x.representative_point().coords[:])
    block_durham['coords'] = [coords[0] for coords in block_durham['coords']] 
    return block_durham

def comp_dist(elem_durham_basic,block_durham):
    df_dist =block_durham.loc[:,['BLKGRP']]
    df_dist['LON'] = block_durham['coords'].apply(lambda x: x[0])
    df_dist['LAT'] = block_durham['coords'].apply(lambda x: x[1])
    for index, row in elem_durham_basic.iterrows():
        school = row['name']
        coord0 = row['coords'][0]
        coord1 = row['coords'][1]
        df_dist[school] = (df_dist['LON'] - coord0)**2 + (df_dist['LAT'] - coord1)**2 
    return df_dist


# ## Export enrollment constraint

# In[34]:


if __name__ == "__main__": 

    elem_durham_basic = get_schl_info()
    block_durham = get_blk_info()
    df_dist = comp_dist(elem_durham_basic,block_durham)

    # write schl capacity info to data file
    f = open('school_capacity.txt', 'w')

    for idx, row in elem_durham_basic.iterrows():
        school_name = row['name']
        capacity = int(1.1*row['member'])
        write_string = school_name + '      ' + str(capacity) + "\n"
        f.write(write_string)
    f.close()

    school_string = '                ' + '   '.join(list(df_dist.columns)[3:])
    f = open('distance_file.txt', 'w')
    f.write(school_string+"\n")
    for idx, row in df_dist.iterrows():
        block_id = str(df_dist.iloc[idx,0]) + '              '
        dist =[str(d) for d in list(df_dist.iloc[idx,3:])]
        dist_string = '   '.join(dist)
        write_string =block_id + dist_string + "\n"
        f.write(write_string)
    f.close()

    import math
    f = open('block_race_file.txt', 'w')
    ethnicity_title = "            White     Asian     Multi     Hispanic     Black  :=\n"
    f.write(ethnicity_title)
    for idx, row in block_durham.iterrows():
        block_id = str(block_durham.iloc[idx,0]) + '              '
        nums =[int(d)+1 if int(d)%1 > 0.5 else int(d) for d in list(block_durham.iloc[idx,4:9])]
        nums = [str(x) for x in nums]
        nums_string = '   '.join(nums)
        write_string =block_id + nums_string + "\n"
        f.write(write_string)
    f.close()


# In[ ]:



# ig, ax = plt.subplots(1, 1,figsize=(25, 25))
# ax.spines["top"].set_visible(False)
# ax.spines["right"].set_visible(False)
# ax.set_title("Census Tracts in Durham",fontsize = 28)
# block_durham.geometry.boundary.plot(color = None, edgecolor = 'b',linewidth = 1, ax = ax, vmin = 0, vmax = 1)


# In[ ]:


# ig, ax = plt.subplots(1, 1,figsize=(25, 25))
# ax.spines["top"].set_visible(False)
# ax.spines["right"].set_visible(False)
# ax.set_title("Durham Public Elementary School Districts",fontsize = 28)
# #elem_durham.plot(ax = ax, legend = True, column = 'Pct_H',cmap = 'YlOrRd')
# #elem_durham.plot(ax = ax, legend = True,cmap = 'YlOrRd')
# elem_durham.geometry.boundary.plot(color = None, edgecolor = 'r',linewidth = 1, ax = ax, vmin = 0, vmax = 1)
# for idx, row in elem_durham.iterrows():
#     plt.annotate(s=row['name'][0:12], xy=row['coords'],
#                  horizontalalignment='center', fontsize = 16)

