""" multil_delete

This implements the /delete functionality for the Multi-Lingual Meta analysis web application

"""

import json
import os, sys
import copy
import boto3
from datetime import date, datetime

from settings import ACCESS_KEY, SECRET_KEY, EDIT_KEY

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

def dataset_contains_observation(lst_dataset, observations, rows):
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
        # Walk all observations to be checked
        for observation_id in observations:
            # Walk the whole data set
            for idx, datasetRow in enumerate(lst_dataset):
                if debug_level > 2:
                    html.append( "checking observation {}".format(observation_id))
                # Check the observation ID
                if 'observation' in datasetRow and datasetRow['observation'] == observation_id:
                    # Get the row index
                    row_id = idx
                    # Add the row index to the output [rows]
                    rows.append(row_id)

                    # --------- DEBUGGING -------------------------
                    if debug_level > 1:
                        print("dataset_contains_observation: found observation to be deleted")
                        html.append( "Row {} contains observation {}".format(row_id, observation_id))
                    # ---------------------------------------------

                    # Make sure to leave this loop so as to go for the next possibility
                    break
        msg = "\n".join(html)

    except:
        msg = oErr.get_error_message()
        print(msg)
        oErr.DoError("dataset_contains_observation")
        bBack = False
    return bBack, msg

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
        lst_result = []     # The result we provide for the user
        observations = []   # List of observations to be deleted

        # Get the new data, which should be inside 'event.body' as a string
        if 'body' in event:
            body = json.loads(event['body'])
            # Get the observation id from the data
            data = body.get("observations", None)
            if not data is None and isinstance(data, list):
                for obs in data:
                    if isinstance(obs, int):
                        observations.append(obs)
                if debug_level > 2:
                    print("Task is to delete observation(s): {}".format(str(observations)))

            # Since this involves editing, see whether this caller has editing rights
            bHasEditingRights, msg = check_rights(body, EDIT_KEY)

        else:
            lst_result.append(dict(item="no data in event"))
            lst_result.append(dict(test=event['multiValueQueryStringParameters']))

        # Do we actually have 1 or more data items to be deleted?
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
                lst_output = []
                lst_rowids = []

                # Check whether we need to save this or not
                bNeedSaving = False

                # Get the datarow that contains the observation to be deleted
                bBack, sErr = dataset_contains_observation(lst_input, observations, lst_rowids)

                lst_result.append(dict(msg="Observation ids {} are in rows {}".format(observations, lst_rowids)))

                # Have rows to be deleted been found?
                count_del = len(lst_rowids)
                if count_del > 0:
                    lst_result.append(dict(msg="There are {} observations to be deleted".format(count_del)))
                    # Yes, the rows have been found: delete them from the lst_input
                    for row_id, oNewData in enumerate(lst_input):
                        obs_id = oNewData['observation']
                        if obs_id in observations and row_id in lst_rowids:
                            # Indicate that we are deleting this one
                            lst_result.append(dict(msg="Deleting observation id {} at row {}".format(obs_id, row_id)))
                        else:
                            # Add a copy of the data to the output
                            lst_output.append(copy.copy(oNewData))
                    # Replace the existing dataset
                    oAllData['Dataset'] = lst_output
                    lst_result.append(dict(msg="Replacing the Dataset with the emended one"))
                    bNeedSaving = True
                else:
                    lst_result.append(dict(msg="No observations found matching these id's: {}".format(observations)))

                # Should we save the results to S3?
                if bNeedSaving:
                    sData = json.dumps(oAllData, indent=2)
                    objBucket.put(Body=sData)
                    lst_result.append(dict(msg="The updated dataset has been put back to S3"))

        else:
            if not bHasEditingRights:
                # User has no editing rights
                lst_result.append(dict(msg="No editing rights", check=msg))
            else:
                # There is no data, so just state that
                lst_result.append(dict(msg="The /delete function works fine, but the list of data objects is empty"))


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



