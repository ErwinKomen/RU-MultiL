""" multil_add

This implements the /add functionality for the Multi-Lingual Meta analysis web application

"""

import json
import os, sys
import boto3
from datetime import date, datetime

from settings import ACCESS_KEY, SECRET_KEY, EDIT_KEY

MULTIL_BUCKET = "multiling-data"
MULTIL_DATA = "multilingual_data.json"

# The keys that should at least be in the dataset rows
data_keys = [
    "observation", "short_cite", "published", "data_collection", "task_number",
    "target_language", "other_language", "task_type", "task_detailed", "linguistic_property",
    "linguistic_property_detailed","bilingual_group", "monolingual_group",
    "surface_overlap_author", "target_or_child_system", "dominance", "language_home",
    "societal_language", "CLI_predicted", "predicted_direction_difference_2L1",
    "mean_age_2L1", "sd_age_2L1", "age_min_2L1", "age_max_2L1", "mean_age_L1",
    "sd_age_L1", "age_min_L1", "age_max_L1", "n_2L1", "n_L1", "mean_2L1",
    "mean_L1", "SD_2L1", "SD_L1", "mean_difference", 
    "d", "g", "g_correct_sign", "g_var", "g_SE", "g_W", "num_trials",
    # See issue #35.1 (=verified by authors)
    "verified_by_administrators",

    # Newly added keys:
    "research_group", "sample",

    # New keys added via issue #37
    "comments", "dependant_variable"

    # Obsolete keys:
    # "t", "t_correct_sign",

    # Keys that are not checked:
    # "email_address",  "task_detailed_other",
    # "linguistic_property_other"
    ]

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

def check_rights(oData, key):
    """Check whether 'key' coincides with the needed editing rights key"""

    bBack = False
    oErr = ErrHandle()
    try:
        edit_key = oData.get("edit_key", "")
        msg = "Found key: [{}]".format(edit_key)
        bBack = (edit_key == key)
    except:
        msg = oErr.get_error_message()
        oErr.DoError("check_rights")
        bBack = False
    return bBack, msg

def is_good_datarow(oRow):
    """Check whether this is a row of data that is correct"""

    oErr = ErrHandle()
    bBack = False
    msg = ""
    try:
        # Double check that this is in fact a dictionary
        if isinstance(oRow, dict):
            # Good, we have a dictionary: check whether all keys are there
            lst_keys = []
            # Old method: oKeys = {}
            for k,v in oRow.items():
                # Old method:
                #if k in oKeys:
                #    oKeys[k] += 1
                #else:
                #    oKeys[k] = 0

                # New method, see issue #32
                if k in data_keys and not k in lst_keys:
                    lst_keys.append(k)
            # Old method: bBack = (len(data_keys) == len(oKeys))
            bBack = (len(data_keys) == len(lst_keys))
            if not bBack:
                # Create a message
                # Old method msg = "Datarow should contain {} keys, but only {} were found.".format(len(data_keys), len(oKeys))
                msg = "Datarow should contain {} obl. keys, but only {} of them were found.".format(len(data_keys), len(lst_keys))
    except:
        msg = oErr.get_error_message()
        print(msg)
        oErr.DoError("is_good_datarow")
        bBack = False
    return bBack, msg

def dataset_contains(lst_dataset, oRow):
    """Check whether the list of data in lst_dataset contains oRow already"""

    oErr = ErrHandle()
    bBack = False
    debug_level = 2
    msg = ""
    row_id = -1
    try:
        html = []
        if debug_level > 2:
                html.append("dataset size = {}".format(len(lst_dataset)))
        # Walk the whole data set
        for idx, datasetRow in enumerate(lst_dataset):
            # Get the observation ID
            observation_id = datasetRow['observation']

            if debug_level > 2:
                html.append( "checking observation {}".format(observation_id))
            # Check if the current row is inside the dataset
            iCount = 0
            for k in data_keys:
                if oRow[k] != datasetRow[k]:
                    iCount += 1
            # If the count is zero, this row is already in the dataset
            if iCount == 0:
                # Make sure that we return the right info: True 
                bBack = True

                # --------- DEBUGGING -------------------------
                if debug_level > 1:
                    print("dataset_contains: count is zero")
                    html.append( "The row exists as observation {}".format(observation_id))
                # ---------------------------------------------

                break
            elif observation_id == oRow['observation']:
                # Make sure that we return the right info: True + row index
                row_id = idx
                bBack = True

                if debug_level > 2:
                    html.append("Observation {}, count={}".format(observation_id, iCount))
                # The observation is the same: where is the first difference?
                for k in data_keys:
                    if debug_level > 2:
                        html.append("Checking key: {}".format(k))
                    if oRow[k] != datasetRow[k]:
                        html.append( "Same observation {} differs at key {}: '{}' versus '{}'".format(
                            observation_id, k, oRow[k], datasetRow[k]
                            ) )
                        break
                break
        msg = "\n".join(html)

    except:
        msg = oErr.get_error_message()
        print(msg)
        oErr.DoError("dataset_contains")
        bBack = False
    return bBack, msg, row_id

def lambda_handler(event, context):
    """Get to the data and return a list of it"""

    oErr = ErrHandle()
    body = dict(status="error", data="empty")

    debug_level = 2

    try:
        print("Setting up S3 resource")
        s3 = boto3.resource('s3', region_name='eu-north-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY )

        print("Setting up S3 client")
        client = boto3.client('s3',  region_name='eu-north-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

        # Initialisations
        data = []           # List into which the items to be added are put
        lst_result = []     # The result we provide for the user

        # Get the new data, which should be inside 'event.body' as a string
        if 'body' in event:
            body = json.loads(event['body'])
            if 'data' in body:
                data = body['data']

                if not data is None and len(data) > 0:
                    lst_result.append(
                        dict(
                            msg="reading data size={} body size={}".format(
                                len(data), 
                                len(event['body'])
                                )
                            )
                        )

                if debug_level > 2:
                    if not data is None and len(data) > 0:
                        # Okay there is some data: process it
                        print("there is body-data! Length is: {}".format(len(data)))
                        # Walk the data using k/v
                        for k,v in data.items():
                            kv = "body-data parameter '{}' = '{}'".format(k,v)
                            print(kv)
                            lst_result.append(dict(item=kv))
                    else:
                        print("there is no data...")
                        lst_result.append(dict(item="body-data is empty"))

            # Since this involves editing, see whether this caller has editing rights
            bHasEditingRights, msg = check_rights(body, EDIT_KEY)

        else:
            lst_result.append(dict(item="no data in event"))
            lst_result.append(dict(test=event['multiValueQueryStringParameters']))

        # Do we actually have 1 or more data items to be added?
        if bHasEditingRights and len(data) > 0:
            # Load the bucket object
            objBucket = s3.Object(MULTIL_BUCKET, MULTIL_DATA)

            print("[1] Read body data")
            sAllData = objBucket.get()['Body'].read().decode('utf-8')
            
            oAllData = json.loads(sAllData)

            # Double check if we have a dataset in there
            if bHasEditingRights and 'Dataset' in oAllData:
                # Read the dataset into a list
                lst_input = oAllData['Dataset']

                # Check whether we need to save this or not
                bNeedSaving = False

                # Walk the data to be added
                for idx, oNewData in enumerate(data):
                    # Double check that this is in fact a dictionary
                    bBack, msg = is_good_datarow(oNewData)
                    if not bBack:
                        # Provide a message
                        lst_result.append(dict(row=idx, msg=msg))
                    else:
                        # The data is good, try to get at least the observation id
                        observation_id = oNewData.get("observation", -1)

                        # The data is good, check if it is already there or not
                        bBack, sErr, row_id = dataset_contains(lst_input, oNewData)
                        if bBack:
                            if row_id >= 0:
                                # The data is already there: overwrite it
                                lst_input[row_id] = oNewData
                                bNeedSaving = True
                                # Provide a message
                                msg = "Updating this row, since the data is already in S3"
                                lst_result.append(dict(observation=observation_id, msg=msg, check=sErr))
                            else:
                                # Provide a message
                                msg = "Skipping this row, since the same data is already in S3"
                                lst_result.append(dict(observation=observation_id, msg=msg))
                        elif sErr != "":
                            msg = "Error"
                            lst_result.append(dict(observation=observation_id, msg=msg, err=sErr))
                        else:
                            # Add this row to the data
                            msg = "Adding this row"
                            lst_result.append(dict(observation=observation_id, msg=msg))
                            lst_input.append(oNewData)
                            # Indicate that saving is needed
                            bNeedSaving = True

                # Should we save the results to S3?
                if bNeedSaving:
                    sData = json.dumps(oAllData, indent=2)
                    objBucket.put(Body=sData)

        else:
            if not bHasEditingRights:
                # User has no editing rights
                lst_result.append(dict(msg="No editing rights", check=msg))
            else:
                # There is no data, so just state that
                lst_result.append(dict(msg="The /add function works fine, but the list of data objects is empty"))


        # Build the body that is going to be returned
        body = dict(status="ok", data=lst_result )
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


