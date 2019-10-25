#!/usr/bin/env python
# coding: utf-8

# Long-term international migration 2.01a, citizenship, UK and England and Wales

# In[2]:


from gssutils import *
scraper = Scraper('https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/'                   'internationalmigration/datasets/longterminternationalmigrationcitizenshiptable201a')
scraper


# In[3]:


tab = next(t for t in scraper.distributions[0].as_databaker() if t.name == 'Table 2.01a')


# Observations are in pairs of value +- confidence interval. Also, the table has been revised since the 2011 census and contains details about which observations have been revised and what their original estimates were.

# In[4]:


cell = tab.filter('Year')
cell.assert_one()
citizenship = cell.fill(RIGHT).is_not_blank().is_not_whitespace()  |             cell.shift(0,1).fill(RIGHT).is_not_blank().is_not_whitespace() |             cell.shift(0,2).expand(RIGHT).is_not_blank().is_not_whitespace().is_not_bold()             .filter(lambda x: type(x.value) != 'All' not in x.value)
citizenship

#citezenship = citenzship - tab.excel_ref("C").filter(contains_string("Census Revision")


# Revision to Notebook: Friday 20th September 2019 by M. Spooner.
# Description: Jenkins build failure due to source spreadsheet amendment to dimesnions structure.

# In[5]:


citizenship = citizenship.filter(lambda x: type(x.value) != '2011 Census Revisions1' not in x.value)                          .filter(lambda x: type(x.value) != 'Original Estimates1' not in x.value)
citizenship
                                                      


# In[6]:


observations = cell.shift(RIGHT).fill(DOWN).filter('Estimate').expand(RIGHT).filter('Estimate')                 .fill(DOWN).is_not_blank().is_not_whitespace() 
Str =  tab.filter(contains_string('Significant Change?')).fill(RIGHT).is_not_number()
observations = observations - (tab.excel_ref('A1').expand(DOWN).expand(RIGHT).filter(contains_string('Significant Change')))
original_estimates = tab.filter(contains_string('Original Estimates')).fill(DOWN).is_number()
observations = observations - original_estimates - Str


# In[7]:


CI = observations.shift(RIGHT)


# In[8]:


Year = cell.fill(DOWN) 
Year = Year.filter(lambda x: type(x.value) != str or 'Significant Change?' not in x.value)


# In[9]:


Geography = cell.fill(DOWN).one_of(['United Kingdom', 'England and Wales'])
Flow = cell.fill(DOWN).one_of(['Inflow', 'Outflow', 'Balance'])


# In[10]:


csObs = ConversionSegment(observations, [
    HDim(Year,'Year', DIRECTLY, LEFT),
    HDim(Geography,'Geography', CLOSEST, ABOVE),
    HDim(citizenship, 'Citizenship', DIRECTLY, ABOVE),
    HDim(Flow, 'Flow', CLOSEST, ABOVE),
    HDimConst('Measure Type', 'Count'),
    HDimConst('Unit','People (thousands)'),
    HDim(CI,'CI',DIRECTLY,RIGHT),
    HDimConst('Revision', '2011 Census Revision')
])
savepreviewhtml(csObs)
tidy_revised = csObs.topandas()


# In[11]:


csRevs = ConversionSegment(original_estimates, [
    HDim(Year, 'Year', DIRECTLY, LEFT),
    HDim(Geography,'Geography', CLOSEST, ABOVE),
    HDim(citizenship, 'Citizenship', DIRECTLY, ABOVE),
    HDim(Flow, 'Flow', CLOSEST, ABOVE),
    HDimConst('Measure Type', 'Count'),
    HDimConst('Unit','People (thousands)'),
    HDim(original_estimates.shift(RIGHT), 'CI', DIRECTLY, RIGHT),
    HDimConst('Revision', 'Original Estimate')
])
orig_estimates = csRevs.topandas()


# In[12]:


tidy = pd.concat([tidy_revised, orig_estimates], axis=0, join='outer', ignore_index=True, sort=False)


# Ignore data markers for now and ensure all observations are integers.
# **Todo: figure out what to do with data markers.**

# In[13]:


import numpy as np
tidy['OBS'].replace('', np.nan, inplace=True)
tidy.dropna(subset=['OBS'], inplace=True)
tidy.drop(columns=['DATAMARKER'], inplace=True)
tidy.rename(columns={'OBS': 'Value', 'Citizenship' : 'LTIM Citizenship'}, inplace=True)
tidy['Value'] = tidy['Value'].astype(int)
tidy['CI'] = tidy['CI'].map(lambda x:'' if x == ':' else int(x[:-2]) if x.endswith('.0') else 'ERR')


# Check each observation has a year and use ints.

# In[14]:


tidy['Year'] = tidy['Year'].apply(lambda x: pd.to_numeric(x, downcast='integer'))
tidy['Year'] = tidy['Year'].astype(int)


# In[15]:


for col in tidy.columns:
    if col not in ['Value', 'Year', 'CI']:
        tidy[col] = tidy[col].astype('category')
        display(col)
        display(tidy[col].cat.categories)


# In[16]:


tidy['Geography'] = tidy['Geography'].cat.rename_categories({
    'United Kingdom': 'K02000001',
    'England and Wales': 'K04000001'
})
tidy['LTIM Citizenship'] = tidy['LTIM Citizenship'].cat.rename_categories({
    'All citizenships' : 'all-citizenships',
    'All3' : 'non-european-union-all',
    'Asia' :'non-european-union-asia-all',
    'British\n(Including Overseas Territories)' : 'british-including-overseas-territories',
    'Central and South America' : 'non-european-union-rest-of-the-world-central-and-south-america', 
    'East Asia' : 'non-european-union-asia-east-asia',
    'European Union EU15' : 'european-union-european-union-eu15',
    'European Union EU2' : 'european-union-european-union-eu2',
    'European Union EU8':'european-union-european-union-eu8',
    'European Union Other' : 'european-union-european-union-other',
    'European Union2' : 'european-union-european-union' , 
    'Middle East and Central Asia' : 'non-european-union-asia-middle-east-and-central-asia', 
    'Non-British' : 'non-british' ,
    'North Africa' : 'non-european-union-rest-of-the-world-north-africa',
    'North America' : 'non-european-union-rest-of-the-world-north-america', 
    'Oceania' : 'non-european-union-rest-of-the-world-oceania', 
    'Other Europe3' : 'non-european-union-other-europe',
    'Rest of the World' : 'non-european-union-rest-of-the-world-all', 
    'South Asia' : 'non-european-union-asia-south-asia', 
    'South East Asia' : 'non-european-union-asia-south-east-asia', 
    'Stateless' : 'non-european-union-stateless',
    'Sub-Saharan Africa' : 'non-european-union-rest-of-the-world-sub-saharan-africa'
            
})
tidy['Flow'] = tidy['Flow'].cat.rename_categories({
    'Balance': 'balance', 
    'Inflow': 'inflow',
    'Outflow': 'outflow'
})


# Todo: some values (estimations / CIs) have been rounded to zero and indicated with a `0~`, but this seems to be using conditional formatting of some kind and doesn't come through. We need to add data markers.
# 
# For CI we'll use a blank string for these markers, otherwise use the string representation of the int so it comes out in CSV okish.

# In[17]:


tidy['CI'] = tidy['CI'].apply(
    lambda x: '' if str(x) in ['', '0', ':', 'z'] else int(float(x))
)
tidy


# Re-order the columns and output as CSV with some metadata.

# In[18]:


tidy = tidy[['Geography','Year','LTIM Citizenship','Flow','Measure Type','Value','CI','Unit', 'Revision']]
from pathlib import Path
destinationFolder = Path('out')
destinationFolder.mkdir(exist_ok=True, parents=True)

tidy.to_csv(destinationFolder / ('observations.csv'), index = False)

from gssutils.metadata import THEME

scraper.dataset.family = 'migration'
scraper.dataset.theme = THEME['population']

with open(destinationFolder / 'dataset.trig', 'wb') as metadata:
    metadata.write(scraper.generate_trig())


# In[19]:


csvw = CSVWMetadata('https://gss-cogs.github.io/ref_migration/')
csvw.create(destinationFolder / 'observations.csv', destinationFolder / 'observations.csv-schema.json')


# In[ ]:




