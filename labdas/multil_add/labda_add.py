""" multil_list

This implements the /list functionality for the Multi-Lingual Meta analysis web application

"""

import json
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

    bFindBucket = False
    debug_level = 2

    try:
        print("Setting up S3 resource")
        s3 = boto3.resource('s3', region_name='eu-north-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY )

        print("Setting up S3 client")
        client = boto3.client('s3',  region_name='eu-north-1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

        # Initialisations
        data = "none"

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


        # Build the body that is going to be returned
        body = dict(status="ok", data=oAllData )
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
