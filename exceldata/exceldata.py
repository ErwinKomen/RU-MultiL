""""exceldata

Read contents of the Excel fie used for MultiL
"""
import sys, getopt, os.path, importlib
import os, sys
import json

# Provide our standard error handling
from utils import ErrHandle

# Processing Excel
import openpyxl
from openpyxl.utils.cell import get_column_letter
from openpyxl.cell import Cell
from openpyxl import Workbook

def process_excel(oArgs):
    """"""

    lExtracted = []
    bBack = False
    oErr = ErrHandle()
    try:
        # Retrieve the parameters
        flInput = oArgs.get("input")
        flOutput = oArgs.get("output")

        if flInput is None or flOutput is None:
            return False

        # Load the Excel workbook
        wb = openpyxl.load_workbook(flInput, read_only=True)
        sheetnames = wb.sheetnames
        ws_data = None
        ws_features = None
        for sname in sheetnames:
            if "dataset" in sname.lower():
                ws_data = wb[sname]
            elif "explanation column" in sname.lower():
                ws_features = wb[sname]
        # Do we have the right columns
        if ws_data is None or ws_features is None:
            return False

        flOutput = "extracted.json"

        # Save output
        with open(flOutput, "w", encoding="utf-8-sig") as fp:
            json.dump(lExtracted, fp, indent=2)
    except:
        msg = oErr.get_error_message()
        oErr.DoError("process_excel")

    return bBack

def main(prgName, argv) :
    flInput = ''        # input file name: XML with author definitions
    flOutput = ''       # output file name
    lExtracted = []
    keywords = ['sermon', 'sermons', 'homélie', 'homélies', 'homéliaire', 'homiliaire', 'liturgie', 'liturgique', 'sermonnaire', 'lectionnaire', 'bréviaire']

    oErr = ErrHandle()
    try:
        sSyntax = prgName + ' -i <Excel file> -o <Json output file name>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:", ["-ifile=", "-ofile"])
        except getopt.GetoptError:
            print(sSyntax)
            sys.exit(2)
        # Walk all the arguments
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-i", "--ifile"):
                flInput = arg
            elif opt in ("-o", "--ofile"):
                flOutput = arg
        # Check if all arguments are there
        if (flInput == '' or flOutput == ''):
            oErr.DoError(sSyntax)

        # Continue with the program
        oErr.Status('Input is "' + flInput + '"')
        oErr.Status('Output is "' + flOutput + '"')

        oArgs = dict(input=flInput, output=flOutput)

        # Process the Excel
        if not process_excel(oArgs):
            oErr.DoError("Could not complete reading CorpusSearch results", True)


        # All went fine  
        oErr.Status("Ready")
    except:
        # act
        oErr.DoError("main")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call the main function with two arguments: program name + remainder
    main(sys.argv[0], sys.argv[1:])
