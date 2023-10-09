import os, re, sys # to work with operating system and text 
import json # to read a popular data representation format, JSON
import requests # to handle HTTP (web) requests
import pandas as pd # for tabular manipulation and computation
import numpy as np # for numerical computations
import getpass # to (interactively) request password input for a user 

# access_token=''
class Credentials:
    def __init__(self):
        self.access_token = "empty"

    def setup_credetials(self):
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
            
            body_auth = {'grant_type' : 'password', 
                        'client_id' : client_id, 
                        'client_secret' : client_secret, 
                        'username' : username,
                        'password' : password,
                        'platform' : 'uw-ipynb'}
            res = requests.post(endpoint_auth, data=body_auth)
            auth_json = res.json()
            self.access_token = auth_json['access_token']
        else:
            print('Invalid credential type! Use TEMP, LOCAL, or CLOUD. See the instructions above.')

class Analysis:
    def __init__(self):
        self.ciks=[]
        self.years=[]
        self.fields=[]
        self.concepts=[]
        self.access_token=''

    def set_access_token(self, token):
        self.access_token = token

    def set_ciks(self, ciks):
        self.ciks = ciks

    def set_years(self, years):
        self.years = years

    def set_fields(self, fields):
        self.fields = fields

    def set_concepts(self, concepts):
        self.concepts=concepts


    def execute_query(self):
        all_res_list = []
        done_retrieving_all_results = False
        offset = 0
        offset = 0
        res_df = pd.DataFrame()


        ciks=[]
        str_years=','.join(self.years)
        str_fields=','.join(self.fields)
        str_concepts=','.join(self.concepts)
        # for cik in self.ciks:
        base_url=''.join([
            'https://api.xbrl.us/api/v1/fact/search?report.source-name=sec&','report.document-type=10-K&','entity.code=', ','.join(self.ciks),
            '&period.fiscal-year=',str_years,'&fact.has-dimensions=false&concept.local-name=',str_concepts,
            '&fields=',str_fields
        ])
        res = requests.get(base_url, headers={'Authorization' : 'Bearer {}'.format(self.access_token)})
        while not done_retrieving_all_results:
            ## Interpret as JSON
            res_json = res.json()

            ## Get the results
            ### Retrieve the data list
            res_list = res_json['data']
            ### Add to the results
            all_res_list += res_list

        #     ## Pagination check
            paging_dict = res_json['paging']
            if paging_dict['count'] >= 2000:
                offset += paging_dict['count']
            else:
                done_retrieving_all_results = True
    
        # print(all_res_list)
        res_df = pd.DataFrame(all_res_list)
        res_df.drop_duplicates(inplace=True)
        res_df = res_df.reset_index(drop=True)
        res_df = res_df.sort_values(by=['entity.name','concept.local-name'])
        print(res_df)

this_credentials = Credentials()
this_credentials.setup_credetials()
print(this_credentials.access_token)
# firm_ciks =     ['0001018724','0000320193', '0000354950']
# report_types = ['10-K']
# get_extensions = 'FALSE'
# xbrl_elements = ['CashAndCashEquivalentsAtCarryingValue',]

# with_dimensions = 'TRUE'  ## TRUE for require dimensions, FALSE for no dimensions, ALL for all values
# years = ['2020']
# fields = ['entity.name','concept.local-name','fact.value','period.fiscal-period','period.fiscal-year']
# concept=[
#     'CashAndCashEquivalentsAtCarryingValue',
#     'AccountsReceivableNetCurrent',
#     'AssetsCurrent', 
#     'PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization'
# ]
this_analysis=Analysis()
this_analysis.set_access_token(this_credentials.access_token)
this_analysis.set_ciks(['0001018724','0000320193', '0000354950'])
this_analysis.set_years(['2020'])
this_analysis.set_fields(['entity.name','concept.local-name','fact.value','period.fiscal-period','period.fiscal-year', 'concept.balance-type'])
this_analysis.set_concepts(['CashAndCashEquivalentsAtCarryingValue', 'AccountsReceivableNetCurrent', 'AssetsCurrent', 'PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization'])
# str_concept=','.join(concept)
this_analysis.execute_query()