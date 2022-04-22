import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

tafe_survey = pd.read_csv('tafe_survey.csv') # load rawdata
dete_survey = pd.read_csv('dete_survey.csv', na_values = 'Not Stated') # load rawdata represent Not Stated as NaN vals

tafe_survey_to_drop = tafe_survey.columns[17:66] # tafe columns 2be dropped
dete_survey_to_drop = dete_survey.columns[28:49] # dete columns 2be dropped

tafe_survey = tafe_survey.drop(tafe_survey_to_drop, axis = 1) # drop columns 17:66
dete_survey = dete_survey.drop(dete_survey_to_drop, axis = 1) # drop columns 28:49

# cleaning column names manually:
rename_names = {'Record ID': 'id', 
                'CESSATION YEAR': 'cease_date',
                'Reason for ceasing employment': 'separationtype',
                'Gender. What is your Gender?': 'gender', 
                'CurrentAge. Current Age': 'age',
                'Employment Type. Employment Type': 'employment_status',
                'Classification. Classification': 'position',
                'LengthofServiceOverall. Overall Length of Service at Institute (in years)': 'institute_service',
                'LengthofServiceCurrent. Length of Service at current workplace (in years)': 'role_service'}

tafe_survey = tafe_survey.rename(columns = rename_names)
dete_survey = dete_survey.rename(columns = rename_names)

# cleaning column names:
# remove trailing white spaces
# replace remaining white spaces with '_'
# make all columns lower case
tafe_survey.columns = tafe_survey.columns.str.lower().str.strip().str.replace(' ','_')
dete_survey.columns = dete_survey.columns.str.lower().str.strip().str.replace(' ','_')

# select resignations
dete_resignations = dete_survey[(dete_survey['separationtype'] == 'Resignation-Other reasons') | \
                               (dete_survey['separationtype'] == 'Resignation-Other employer')| \
                                (dete_survey['separationtype'] == 'Resignation-Move overseas/interstate')].copy()

taf_resignations = tafe_survey[tafe_survey['separationtype'] == 'Resignation'].copy()

# change to datatime
dete_resignations['cease_date'] = pd.to_datetime(dete_resignations['cease_date']).dt.strftime('%Y').astype(float)

dete_resignations['dete_start_date'] = pd.to_datetime(dete_resignations['dete_start_date'], \
                                                      format = "%Y").dt.strftime('%Y').astype(float)

# subtract dete_start_date from cease_date

dete_resignations['institute_service'] = dete_resignations['cease_date'].astype(float) \
                                                - dete_resignations['dete_start_date'].astype(float)

def update_vals(val):
    '''
    update columns:
    - contributing_factors._job_dissatisfaction
    -  contributing_factors._dissatisfaction
    to either uniformly indicate wether or not employee left because of dissatisfaction
    '''
    if pd.isnull(val):
        return np.nan
    elif val == '-':
        return False
    else:
        return True
    
# apply update_vals function to dataframe 
# df['A'] = df['A'].map(addOne)
taf_resignations['contributing_factors._dissatisfaction'] = \
            taf_resignations['contributing_factors._dissatisfaction'].map(update_vals)

taf_resignations['contributing_factors._job_dissatisfaction'] = \
            taf_resignations['contributing_factors._job_dissatisfaction'].map(update_vals)

taf_resignations['dissatisfaction'] = taf_resignations[['contributing_factors._job_dissatisfaction', \
                                             'contributing_factors._dissatisfaction']].any(axis=1, skipna=False)
# def resignations
dete_resignations['dissatisfaction'] = dete_resignations[['job_dissatisfaction',\
                                                          'dissatisfaction_with_the_department',\
                                                          'physical_work_environment',\
                                                          'lack_of_recognition',\
                                                          'lack_of_job_security',\
                                                          'work_location',\
                                                          'employment_conditions',\
                                                          'work_life_balance',\
                                                          'workload']].any(axis=1, skipna=False)

# copy updated dataframes to work on
dete_resignations_up = dete_resignations.copy()
taf_resignations_up = taf_resignations.copy()

# add extra column for identifiers
dete_resignations_up['institute'] = 'DETE'
taf_resignations_up['institute'] = 'TAFE'

# merge the two dataframes - result called combined
combined = pd.concat([dete_resignations_up, taf_resignations_up])

# get rid of columns with more than 500 nan values
combined_up = combined.copy()
combined_up = combined.dropna(axis = 1, thresh = 500)

# Convert years of service to string
combined_up['institute_service'] = combined['institute_service'].astype('str')
# manually replace the two outliers:
combined_up['institute_service'] = combined_up['institute_service'].str.replace("Less than 1 year", "0.0", regex = False)
combined_up['institute_service'] = combined_up['institute_service'].str.replace("More than 20 years", "20.0", regex = False)
# get first entry of values separated by '-'
combined_up['institute_service'] = combined_up['institute_service'].str.split(pat = '-', expand = True)
# convert to float
combined_up['institute_service'] = combined_up['institute_service'].astype('float')
combined_up['institute_service'].value_counts(dropna = False)

def classify_employee(val):
    if pd.isnull(val):
        return np.nan
    elif val < 3:
        return 'new'
    elif val <= 6:
        return 'experienced'
    elif val <= 10:
        return 'established'
    elif val >= 11.0:
        return 'veteran'
    
combined_up['service_cat'] = combined_up['institute_service'].map(classify_employee)

# fill nan values with False
combined_up = combined_up.fillna(False) # fill nan values with False

combined_up = combined_up.dropna()

# save result to csv file
combined_up.to_csv('aggregated_cleaned_data.csv',index=False)