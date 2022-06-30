""" multil_filter

This implements the /filter functionality for the Multi-Lingual Meta analysis web application

"""

import json
from logging import debug
import os, sys
import boto3
from datetime import date, datetime

from settings import ACCESS_KEY, SECRET_KEY

MULTIL_BUCKET = "multiling-data"
MULTIL_DATA = "multilingual_data.json"

class ErrHandle:
    """Error handling"""

    # ======================= CLASS INITIALIZER ========================================
    def __init__(self):
        # Initialize a local error stack
        self.loc_errStack = []

    # ----------------------------------------------------------------------------------
    # Name :    Status
    # Goal :    Just give a status message
    # History:
    # 6/apr/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def Status(self, msg):
        """Put a status message on the standard error output"""

        print(msg, file=sys.stderr)

    # ----------------------------------------------------------------------------------
    # Name :    DoError
    # Goal :    Process an error
    # History:
    # 6/apr/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def DoError(self, msg, bExit = False):
        """Show an error message on stderr, preceded by the name of the function"""

        # Append the error message to the stack we have
        self.loc_errStack.append(msg)
        # get the message
        sErr = self.get_error_message()
        # Print the error message for the user
        print("Error: {}\nSystem:{}".format(msg, sErr), file=sys.stderr)
        # Is this a fatal error that requires exiting?
        if (bExit):
            sys.exit(2)
        # Otherwise: return the string that has been made
        return "<br>".join(self.loc_errStack)

    def get_error_message(self):
        """Retrieve just the error message and the line number itself as a string"""

        arInfo = sys.exc_info()
        if len(arInfo) == 3 and arInfo[0] != None:
            sMsg = str(arInfo[1])
            if arInfo[2] != None:
                sMsg += " at line " + str(arInfo[2].tb_lineno)
            return sMsg
        else:
            return ""

    def get_error_stack(self):
        return " ".join(self.loc_errStack)


def lambda_handler(event, context):
    """Get to the data and return a list of it"""

    oErr = ErrHandle()
    body = dict(status="error", data="empty")
    filter_spec_int = {}
    filter_spec_str = {}
    filter_keys_int = [
        'observation', 'experiment_number', 'task_number', 'mean_age_2L1', 'mean-age_L1', 'n_2L1', 'n_L1'
        ]
    filter_keys_str = [
        'peer_reviewed', 'target_language', 'other_language', 'task_type', 'task_detailed',
        ]
    filter_count = 0

    bFindBucket = False
    debug_level = 2

    try:
        print("Setting up S3 resource")
        s3 = boto3.resource('s3', region_name='eu-north-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY )

        print("Setting up S3 client")
        client = boto3.client('s3',  region_name='eu-north-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

        # Initialisations
        data = "none"

        # Get any filter parameters
        parameters = event['multiValueQueryStringParameters']
        if not parameters is None:
            for k, item in parameters.items():
                bFound = False
                item_first = item[0]
                # Can we take over this filter as INT?   
                try:             
                    iItem = int(item_first)
                    for key in filter_keys_int:
                        if k == key:
                            filter_spec_int[k] = iItem
                            bFound = True
                            filter_count += 1
                            break
                except:
                    pass
                if not bFound:
                    for key in filter_keys_str:
                        if k == key:
                            filter_spec_str[k] = item_first
                            bFound = True
                            filter_count += 1
                            break

        if debug_level >=2:
            for k,v in filter_spec_int.items():
                print("Found integer filter {}: {}".format(k, v))
            for k,v in filter_spec_str.items():
                print("Found string filter {}: {}".format(k, v))

        # Find the right bucket
        if bFindBucket:
            s3_bucket = None
            for bucket in s3.buckets.all():
                if bucket.name == MULTIL_BUCKET:
                    s3_bucket = bucket
                    print("Found bucket: {}".format(bucket.name))
                    break

        # Load the bucket object
        objBucket = s3.Object(MULTIL_BUCKET, MULTIL_DATA)

        if debug_level >= 3:
            print("[1] S3 object")
            objGet = objBucket.get()

            print("[2] get Body")
            objBody = objGet['Body']

            print("[3] read and decode")
            sData = objBody.read().decode('utf-8')

            oAllData = json.loads(sData)
            print("[4] after oAllData: {}".format(str(oAllData)))

        else:

            print("[1] Read body data")
            sAllData = objBucket.get()['Body'].read().decode('utf-8')

            oAllData = json.loads(sAllData)

        # Possibly apply filtering
        lst_input = oAllData['Dataset']
        lst_output = []
        if filter_count == 0:
            lst_output = lst_input
        else:
            for oRecord in lst_input:
                bAnd = True
                bOr = False

                # Check if this record fits an integer match
                for k, iValue in filter_spec_int.items():
                    bValue = ( oRecord[k] == iValue)
                    bAnd &= bValue
                    bOr |= bValue

                # Check if this record fits a string match: the filter value must be contained in the record
                for k, sValue in filter_spec_str.items():
                    bValue = ( sValue.lower() in oRecord[k].lower())
                    bAnd &= bValue
                    bOr |= bValue
                # For the moment we are taking a logical 'AND'
                if bAnd:
                    lst_output.append(oRecord)

        #if debug_level >= 3: 
        #    print("before dumps")
        #    data = json.dumps(oAllData['Dataset'])
        #    print("Data: {}".format(data))
        #else:
        #    data = json.dumps(oAllData['Dataset'])

        # Build the body that is going to be returned
        body = dict(status="ok", filters=filter_count, size=len(lst_output), data=lst_output )
    except:
        print("ERROR...")
        msg = oErr.get_error_message()
        print(msg)
        oErr.DoError("lambda_handler")
        body['data'] = msg

    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "body": json.dumps(body)
        }
