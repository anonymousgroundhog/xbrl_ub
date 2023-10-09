import os, re, sys # to work with operating system and text 
import json # to read a popular data representation format, JSON
import requests # to handle HTTP (web) requests
import pandas as pd # for tabular manipulation and computation
import numpy as np # for numerical computations
import getpass # to (interactively) request password input for a user 

CREDENTIAL_TYPE = 'LOCAL'
# the following code generates an access token for XBRL US API

if CREDENTIAL_TYPE == 'TEMP':
    user_email = "username@buffalo.edu"
    access_token = requests.get('https://tdekok-xbrlapi.builtwithdark.com/gettoken?platform=aaa-{}'.format(user_email)).text.replace('"', "")
elif CREDENTIAL_TYPE in ['LOCAL', 'CLOUD']:
    # endpoint = 'https://api.xbrl.us'
    endpoint_auth = 'https://api.xbrl.us/oauth2/token'
    
    if CREDENTIAL_TYPE == 'LOCAL':
        with open('login_cred.json', 'r') as f:
            login_cred = json.loads(f.read())
            client_id = login_cred['client_id']
            client_secret = login_cred['client_secret']
            username = login_cred['username']
            password = login_cred['password']
            
    else:
        client_id = input(prompt='Please input your client id here:')
        client_secret = getpass.getpass(prompt = 'Please input your client secret here:')
        username = input(prompt='Please input your username here:')
        
#     password = getpass.getpass(prompt = 'Password: ')
    
    body_auth = {'grant_type' : 'password', 
                'client_id' : client_id, 
                'client_secret' : client_secret, 
                'username' : username,
                'password' : password,
                'platform' : 'uw-ipynb'}
    res = requests.post(endpoint_auth, data=body_auth)
    auth_json = res.json()
    access_token = auth_json['access_token']
else:
    print('Invalid credential type! Use TEMP, LOCAL, or CLOUD. See the instructions above.')

def execute_query(access_token, firm_ciks, years, report_types, get_extensions, xbrl_elements, with_dimensions):
    
    # below is fields (variable) to be output by XBRL US API. 
    # this list can be modified if other/additional information is needed
    # see XBRL US API documentation for a list of all possible fields
    fields = ['entity.cik',
         'entity.name.sort(ASC)',
         'dts.id',
         'fact.id',
         'report.filing-date',
         'period.fiscal-year',
         'period.instant',
         'report.document-type',
         'concept.id',
         'concept.local-name',
         'dimensions.count',
         'dimension.local-name.sort(ASC)',
         'member.local-name',
         'fact.value',
         'unit',
         'fact.decimals',
         'dimension.namespace',
         'member.namespace',
          'fact.has-dimensions',
          'concept.balance-type'
         ]
    
    search_endpoint = 'https://api.xbrl.us/api/v1/fact/search'


    params = {  
         'period.fiscal-period': 'Y',
         'period.fiscal-year': ','.join(years),
         'unit': 'USD',
         'entity.cik': ','.join(firm_ciks),
         'report.document-type': ','.join(report_types)
         }  
    
    if get_extensions == 'TRUE':
        params['concept.is-base'] = 'FALSE'
    else:
        params['concept.local-name'] =  ','.join(xbrl_elements)
    
    if with_dimensions == 'ALL':
        dimension_options = ['TRUE', 'FALSE']
    else:
        dimension_options = [with_dimensions]

    all_res_list = []
    for dimensions_param in dimension_options:
        print('Getting the data for: "fact.has-dimensions" = {}'.format(dimensions_param))
        ### Every request will return a max of 2000 results. So we loop until all results are retrieved. 
        done_retrieving_all_results = False
        offset = 0
        while not done_retrieving_all_results:
            params['fact.has-dimensions'] = dimensions_param
            params['fields'] = ','.join(fields) + ',fact.offset({})'.format(offset) 
            res = requests.get(search_endpoint, params=params, headers={'Authorization' : 'Bearer {}'.format(access_token)})

            ## Interpret as JSON
            res_json = res.json()
            ## Get the results
            ### Retrieve the data list
            res_list = res_json['data']

            ### Add to the results
            all_res_list += res_list

            ## Pagination check
            paging_dict = res_json['paging']
            if paging_dict['count'] >= 2000:
                offset += paging_dict['count']
            else:
                done_retrieving_all_results = True

    ## convert to a DataFrame
    res_df = pd.DataFrame(all_res_list)
    ## remove duplciates; sometimes the same item is reported multiple times throughout the document
    res_df.drop_duplicates(subset = ['entity.name','period.fiscal-year', 'concept.local-name', 'dimension.local-name', 'member.local-name', 'fact.value'], inplace = True)
    ## sort data
    res_df = res_df.sort_values(by=['entity.name','dts.id','concept.local-name','dimension.local-name']).reset_index(drop = True)
    ## reorder table columns
    first_columns = ['entity.name', 'period.fiscal-year', 'report.filing-date', 'concept.local-name', 'fact.value', 'unit','dimension.local-name', 'member.local-name','dimensions.count']
    columns = first_columns + [c for c in res_df.columns if c not in first_columns]
    res_df = res_df[columns]
    
    print('\nNumber of results that meet the criteria: {}'.format(len(res_df)))

    return res_df

# firm_ciks =     ['0001018724', '0000320193','0000354950' ]
firm_ciks =     ['0001018724']

years = ['2020'] ## Use commas between for multiple years, e.g., '2018','2019','2020'
#years = [str(2013 + i) for i in range(8)] ## Years 2013 to 2020
#report_types = ['10-K', '10-K/A']
report_types = ['10-K']
get_extensions = 'FALSE'
xbrl_elements = [
    'CashAndCashEquivalentsAtCarryingValue',
    'RevenueFromContractWithCustomerExcludingAssessedTax',
    'RevenueFromContractWithCustomerIncludingAssessedTax'
                ]

with_dimensions = 'TRUE'  ## TRUE for require dimensions, FALSE for no dimensions, ALL for all values
res_df = execute_query(access_token, firm_ciks, years, report_types, get_extensions, xbrl_elements, with_dimensions)
res_df['entity.name'].str.strip()
res_df['entity.name'] = res_df['entity.name'].str.replace(',', '')

#choose which columns to hide
columns_to_hide = ['entity.cik', 'fact.decimals', 'dimension.namespace', 'member.namespace', 'concept.local-name', 'period.instant']
columns_to_show = [column for column in res_df.columns if column not in columns_to_hide]
print(columns_to_show)

#display the first 40 results

print(res_df[columns_to_show])
res_df[columns_to_show].to_csv("example.csv",index=False)