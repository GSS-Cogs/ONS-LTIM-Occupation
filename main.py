# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.1.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# Long-term international migration 2.05, Occupation

# +
from gssutils import *

scraper = Scraper('https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/' \
                  'internationalmigration/datasets/longterminternationalmigrationusualoccupationpriortomigrationtable205')
scraper
# -

tab = next(t for t in scraper.distribution().as_databaker() if t.name == 'Table 2.05')

cell = tab.filter('Year')
cell.assert_one()
Occupation = cell.fill(RIGHT).is_not_blank().is_not_whitespace() 
Year = cell.expand(DOWN).filter(lambda x: type(x.value) != str or 'Significant Change?' not in x.value)
Geography = cell.fill(DOWN).one_of(['United Kingdom', 'England and Wales'])
Flow = cell.fill(DOWN).one_of(['Inflow', 'Outflow', 'Balance'])

observations = cell.shift(RIGHT).fill(DOWN).filter('Estimate').expand(RIGHT).filter('Estimate') \
                .fill(DOWN).is_not_blank().is_not_whitespace() 
Str =  tab.filter(contains_string('Significant Change?')).fill(RIGHT).is_not_number()
observations = observations - (tab.excel_ref('A1').expand(DOWN).expand(RIGHT).filter(contains_string('Significant Change')))
original_estimates = tab.filter(contains_string('Original Estimates')).fill(DOWN).is_number()
observations = observations - original_estimates - Str
CI = observations.shift(RIGHT)

csObs = ConversionSegment(observations, [
    HDim(Year,'Year', DIRECTLY, LEFT),
    HDim(Geography,'Geography', CLOSEST, ABOVE),
    HDim(Occupation, 'Occupation', CLOSEST, LEFT),
    HDim(Flow, 'Flow', CLOSEST, ABOVE),
    HDimConst('Measure Type', 'Count'),
    HDimConst('Unit','People (thousands)'),
    HDim(CI,'CI',DIRECTLY,RIGHT),
    HDimConst('Revision', '2011 Census Revision')
])
# savepreviewhtml(csObs)
tidy_revised = csObs.topandas()

csRevs = ConversionSegment(original_estimates, [
    HDim(Year, 'Year', DIRECTLY, LEFT),
    HDim(Geography,'Geography', CLOSEST, ABOVE),
    HDim(Occupation, 'Occupation', CLOSEST, LEFT),
    HDim(Flow, 'Flow', CLOSEST, ABOVE),
    HDimConst('Measure Type', 'Count'),
    HDimConst('Unit','People (thousands)'),
    HDim(original_estimates.shift(RIGHT), 'CI', DIRECTLY, RIGHT),
    HDimConst('Revision', 'Original Estimate')
])
orig_estimates = csRevs.topandas()

tidy = pd.concat([tidy_revised, orig_estimates], axis=0, join='outer', ignore_index=True, sort=False)

import numpy as np
# tidy['OBS'].replace('', np.nan, inplace=True)
# tidy.dropna(subset=['OBS'], inplace=True)
# if 'DATAMARKER' in tidy.columns:
#     tidy.drop(columns=['DATAMARKER'], inplace=True)
tidy.rename(columns={'OBS': 'Value'}, inplace=True)
# tidy['Value'] = tidy['Value'].astype(int)
# tidy['CI'] = tidy['CI'].map(lambda x:'' if x == ':' else int(x[:-2]) if x.endswith('.0') else 'ERR')

tidy['Marker'] = tidy['DATAMARKER'].map(lambda x: { ':' : 'not-available',
                                                'Statistically Significant Decrease' : 'statistically-significant-decrease'}.get(x, x))

tidy['CI'] = tidy['CI'].map(lambda x: { ':' : 'not-applicable',
                                                'N/A' : 'not-applicable'}.get(x, x))

tidy['Occupation'] = tidy['Occupation'].str.rstrip('1234')

for col in tidy.columns:
    if col not in ['Value', 'Year', 'CI']:
        tidy[col] = tidy[col].astype('category')
        display(col)
        display(tidy[col].cat.categories)

# +
tidy['Geography'] = tidy['Geography'].cat.rename_categories({
    'United Kingdom': 'K02000001',
    'England and Wales': 'K04000001'
})
tidy['Occupation'] = tidy['Occupation'].cat.rename_categories({
    'All persons': 'all-persons',
    'Children' : 'children',
    'Manual and clerical' : 'manual-and-clerical',
    'Other adults' : 'other-adults',
    'Professional and managerial' : 'professional-and-managerial',
    'Students' : 'students'    
            
})
tidy['Flow'] = tidy['Flow'].cat.rename_categories({
    'Balance': 'balance', 
    'Inflow': 'inflow',
    'Outflow': 'outflow'
})

tidy = tidy[['Geography', 'Year', 'Occupation', 'Flow',
              'Measure Type','Value', 'CI','Unit', 'Revision', 'Marker']]

# +
# tidy['Year'] = tidy['Year'].apply(lambda x: pd.to_numeric(x, downcast='integer'))

# +
# tidy['Year'] = tidy['Year'].astype(int)

# +
from pathlib import Path
destinationFolder = Path('out')
destinationFolder.mkdir(exist_ok=True, parents=True)

tidy.drop_duplicates().to_csv(destinationFolder / ('observations.csv'), index = False)

# +
from gssutils.metadata import THEME
scraper.dataset.theme = THEME['population']
scraper.dataset.family = 'migration'

with open(destinationFolder / 'dataset.trig', 'wb') as metadata:
    metadata.write(scraper.generate_trig())
