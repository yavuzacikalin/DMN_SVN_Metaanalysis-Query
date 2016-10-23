# Note: Written using Python 3, runs with Python 3

# Load python unix tools
import os
# Load pandas
import pandas as pd
# Load numpy
import numpy as np
# Load ast
import ast

# Read spreadsheet
worksheet = pd.ExcelFile('RVS_streamlined.xls')

# Parse spreadsheet
sv_spreadsheet_data = worksheet.parse("Data")

# Look at variable names
colnames = list(sv_spreadsheet_data.columns.values)


# Translating 'tal2icbm_other.m' from matlab to python for this purpose only,
# assuming only one input of x, y, z values at a time
def tal2icbm_other(inpoints):
    inpoints.append(1)
    inpoints_array = np.array(inpoints)
    icbm_other = np.array([
        [0.9357, 0.0029, -0.0072, -1.0423],
        [-0.0065, 0.9396, -0.0726, -1.3940],
        [0.0103, 0.0752, 0.8967, 3.6475],
        [0.0000, 0.0000, 0.0000, 1.0000]])
    icbm_other_inv = np.linalg.inv(icbm_other)
    return np.inner(icbm_other_inv, inpoints_array).T


data_tlrch = sv_spreadsheet_data.loc[
    (sv_spreadsheet_data[colnames[13]] == 'Talairach')]

# Loop over all studies with tlrch Coordinates to transform their coordinates
# into MNI space and save under the MNI coordinates column in the same format

for row in data_tlrch.index:
    foci_string_list_in = sv_spreadsheet_data[colnames[15]][row].split('\n')
    foci_string_list_out = []
    for tlrchfoci_index in range(len(foci_string_list_in)):
        string_in = foci_string_list_in[tlrchfoci_index]
        if '-(' in string_in:
            string_in = "[{0}]".format(string_in[2:-1])
            string_in_val = ast.literal_eval(string_in)
            string_out_val = tal2icbm_other(string_in_val)[:-1]
            string_out = ",".join([
                str(round(i, 2)) for i in string_out_val.tolist()])
            string_out = "-({0})".format(string_out)
        else:
            string_in = "[{0}]".format(string_in)
            string_in_val = ast.literal_eval(string_in)
            string_out_val = tal2icbm_other(string_in_val)[:-1]
            string_out = ",".join([
                str(round(i, 2)) for i in string_out_val.tolist()])
        foci_string_list_out.append(string_out)
    tlrch_foci_string_out = "\n".join(foci_string_list_out)
    sv_spreadsheet_data.loc[row, [colnames[14]]] = tlrch_foci_string_out


def query_spreadsheet(data):
    # Decision stage or reward stage, any outcome modality including those
    # unspecified, excluding studies with ambiguous valence
    decision_or_reward_stage_data = data.loc[
        ((data[colnames[16]] == 'Y') | (data[colnames[18]] == 'Y')) &
        (data[colnames[12]] != 0)]
    # Decision stage only, any outcome modality including those unspecified,
    # excluding studies with ambiguous valence
    decision_stage_only_data = data.loc[
        (data[colnames[16]] == 'Y') &
        (data[colnames[12]] != 0)]
    # Outcome/reward stage only, any outcome modality including those
    # unspecified, excluding studies with ambiguous valence
    reward_stage_only_data = data.loc[
        (data[colnames[18]] == 'Y') &
        (data[colnames[12]] != 0)]
    # Any outcome modality including those unspecified, any decision stage
    # including mid-anticipation, excluding studies with ambiguous valence
    any_outcome_any_stage_data = data.loc[(data[colnames[12]] != 0)]
    # Primary outcome modality only, any decision stage including mid-
    # anticipation, excluding studies with ambiguous valence
    primary_data = data.loc[
        (data[colnames[10]] == 'PRIMARY') &
        (data[colnames[12]] != 0)]
    # Monetary outcome modality only, any decision stage including mid-
    # anticipation, excluding studies with ambiguous valence
    monetary_data = data.loc[
        (data[colnames[10]] == 'MONEY') &
        (data[colnames[12]] != 0)]
    # Return all these subsets of data as a dictionary
    return {
        'dnr': decision_or_reward_stage_data,
        'd': decision_stage_only_data,
        'r': reward_stage_only_data,
        'ao': any_outcome_any_stage_data,
        'p': primary_data,
        'm': monetary_data}


mni_queries = query_spreadsheet(sv_spreadsheet_data)


try:
    os.chdir('./ALEInput')
except OSError:
        os.mkdir('./ALEInput')
        os.chdir('./ALEInput')

query_keys = [query_key for query_key, data_subset in mni_queries.items()]

# For loop over the dictionary
for q_key in query_keys:
    data = mni_queries[q_key]

    # Create .txt files
    pos_text_file = open("SV_Pos_MNIOutput_" + q_key + ".txt", "w")
    neg_text_file = open("SV_Neg_MNIOutput_" + q_key + ".txt", "w")

    pos_text_file.write("// Reference=MNI\n")
    neg_text_file.write("// Reference=MNI\n")
    # For loop over studies in each subset of data in the dictionary
    for row in data.index:
        authors = str(data[colnames[4]][row]).replace(".", "")
        authors = authors.replace(",", "")
        authorlist = authors.split("\n")
        firstauthorstring = authorlist[0]

        year = str(data[colnames[8]][row])

        contrastnote = str(data[colnames[11]][row])

        numSubjects = str(data[colnames[2]][row])

        firstlinestring = "// " + firstauthorstring + "," \
            + year + ": " + contrastnote
        secondlinestring = "// Subjects=" + numSubjects
        foci = data[colnames[14]][row].split('\n')
        posfoci = [x.replace(", ", "\t") for x in foci if '-(' not in x]
        negfoci = [x.replace(", ", "\t") for x in foci if '-(' in x]
        posfoci = [x.replace(",", "\t") for x in posfoci]
        negfoci = [x.replace(",", "\t") for x in negfoci]
        negfociClean = [y[2:-1] for y in negfoci]
        posfocistring = "\n".join(posfoci)
        negfocistring = "\n".join(negfociClean)
        if len(negfocistring) > 1:
            negstringoutput = firstlinestring + '\n' + secondlinestring + \
                '\n' + negfocistring + '\n\n'
            neg_text_file.write(negstringoutput)
        if len(posfocistring) > 1:
            posstringoutput = firstlinestring + '\n' + secondlinestring +  \
                '\n' + posfocistring + '\n\n'
            pos_text_file.write(posstringoutput)

    neg_text_file.close()
    pos_text_file.close()
