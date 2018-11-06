#"""Python 2.7.12"""
# changed 3.5.2 to 2.7.12
# to run...
# python2.7 CAMPRTdata.py patients/

from collections import OrderedDict
from scipy.stats.stats import pearsonr
from scipy.stats.stats import spearmanr
from scipy import spatial
from sklearn.cluster import KMeans
from operator import itemgetter

#import matplotlib.pyplot as plt

import operator

import sys
import os
import glob
import csv
import json

import pySSIM
import matlab
import math
import numpy as np

import pySSIM
import matlab

np.set_printoptions(threshold=np.nan)
np.seterr(divide='ignore', invalid='ignore')

myssim = pySSIM.initialize()

# replace this with reading in CSV file of partitions
# modify other code relating to checking partition/master organs as well
masterList = [
'Brainstem',
'Cricoid_cartilage',
'Cricopharyngeal_Muscle',
'Esophagus',
'Extended_Oral_Cavity',
'Genioglossus_M',
#'Glottic_Area',
'Hard_Palate',
'Hyoid_bone',
'IPC',
'Larynx',
'Lower_Lip',
'Lt_Ant_Digastric_M',
'Lt_Anterior_Seg_Eyeball',
'Lt_Brachial_Plexus',
'Lt_Lateral_Pterygoid_M',
'Lt_Masseter_M',
'Lt_Mastoid',
'Lt_Medial_Pterygoid_M',
'Lt_Parotid_Gland',
'Lt_Posterior_Seg_Eyeball',
'Lt_Sternocleidomastoid_M',
'Lt_Submandibular_Gland',
'Lt_thyroid_lobe',
'Mandible',
'MPC',
'Mylogeniohyoid_M',
'Rt_Ant_Digastric_M',
'Rt_Anterior_Seg_Eyeball',
'Rt_Brachial_Plexus',
'Rt_Lateral_Pterygoid_M',
'Rt_Masseter_M',
'Rt_Mastoid',
'Rt_Medial_Pterygoid_M',
'Rt_Parotid_Gland',
'Rt_Posterior_Seg_Eyeball',
'Rt_Sternocleidomastoid_M',
'Rt_Submandibular_Gland',
'Rt_thyroid_lobe',
'Soft_Palate',
'SPC',
'Spinal_Cord',
'Supraglottic_Larynx',
'Thyroid_cartilage',
'Tongue',
'Upper_Lip',
'GTVp',
'GTVn'
]	




def RunTestCases(organ):

    # GTVn2 is needed, corresponds to second tumor within patient

    # 'GTV node', 'GTV-N', 'GTV_n', 'GTVn', 'GTVn1', 'GTVn2'
    if organ in ('GTV node', 'GTV-N', 'GTV_n', 'GTVn', 'GTVn1'):
        organ = 'GTVn'
    elif organ in ('GTV primary', 'GTV-P', 'GTV_p', 'GTVp'):
        organ = 'GTVp'

    return organ


def FillOrganData(f, organRef, pID):
    od = OrderedDict()

    reader = csv.reader(f)
    headers = next(reader)

    for row in reader:
        organ = row[0]

        organ = RunTestCases(organ)

        if organ in masterList:

            if organ not in organRef:  # list keeps reference to main
                organRef += [organ]

            od[organ] = OrderedDict()  # organ name

            od[organ]['x'] = float(row[1])         # x pos
            od[organ]['y'] = float(row[2])         # y pos
            od[organ]['z'] = float(row[3])         # z pos
            
            # when data is missing, print it out
            # REPORT EVERYTHING TO TEXANS

            if row[5] != "":
                od[organ]['volume'] = float(row[5])  # volume
            else:
                od[organ]['volume'] = 0.0
                print (str(pID) + " missing volume")
            
            if row[4] != "":
                od[organ]['meanDose'] = float(row[4])  # mean dose
            else:
                od[organ]['meanDose'] = -1.0  # originally assigned (None), but pearson correlation returns Nan which is not JSON friendly
                print (str(pID) + " missing mean dose")
            
            if row[6] != "":
                od[organ]['minDose'] = float(row[6])  # min dose
            else:
                od[organ]['minDose'] = -1.0
                print (str(pID) + " missing min dose")
            
            if row[7] != "":
                od[organ]['maxDose'] = float(row[7])  # max dose
            else:
                od[organ]['maxDose'] = -1.0
                print (str(pID) + " missing max dose")

    return od


def FillMatrix(f, organRef, pID):
    # od = OrderedDict()
    reader = csv.reader(f)
    headers = next(reader)

    rows = list(reader)

    hasGTVp = False
    hasGTVn = False

    for row in rows:
        #organ1 = row[0]
        #organ2 = row[1]

        organ1 = RunTestCases(row[0])
        organ2 = RunTestCases(row[1])

        row[0] = organ1
        row[1] = organ2


        if organ1 in masterList and organ2 in masterList:

            if organ1 == 'GTVp' or organ2 == 'GTVp':
                hasGTVp = True

            if organ1 == 'GTVn' or organ2 == 'GTVn':
                hasGTVn = True

            if organ1 not in organRef:  # list keeps reference to main
                organRef += [organ1]

            if organ2 not in organRef:  # list keeps reference to main
                organRef += [organ2]

    #array2D = np.zeros((len(organRef), len(organRef)))
    array2D = np.ones((len(organRef), len(organRef)))

    array2D_tDist = np.zeros((len(organRef), len(organRef)))

    for row in rows:
        organ1 = row[0]
        organ2 = row[1]

        if organ1 in masterList and organ2 in masterList:

            if row[2] == "":
                print (str(pID) + " missing distance")

            array2D[organRef.index(organ1), organRef.index(organ2)] = row[2]
            #array2D[organRef.index(organ1), organRef.index(organ2)] = 0.0

            # flip over diagonal
            array2D[organRef.index(organ2), organRef.index(organ1)] = row[2]
            #array2D[organRef.index(organ2), organRef.index(organ1)] = 0.0

            if hasGTVp:
                if organ1 == 'GTVp':
                    array2D_tDist[organRef.index(organ2), organRef.index(organ2)] = row[2]
                elif organ2 == 'GTVp':
                    array2D_tDist[organRef.index(organ1), organRef.index(organ1)] = row[2]
            #elif hasGTVn:
            #    if organ1 == 'GTVn':
            #        array2D_tDist[organRef.index(organ2), organRef.index(organ2)] = row[2]
            #    elif organ2 == 'GTVn':
            #        array2D_tDist[organRef.index(organ1), organRef.index(organ1)] = row[2]

    # print(array2D)
    # print(array2D.shape)

    return [array2D, array2D_tDist, hasGTVp, hasGTVn]


def main(argv):
    pIDs = []
    patients = []

    organRef = []
    organRef += ['GTVn']
    organRef += ['GTVp']

    count = 1

    # go through each file path from directories
    for fpath in glob.glob(argv + '**/*.csv'):
        with open(fpath, 'r') as f:  # open current file
            fname = os.path.basename(f.name)
            pID = fname[0:fname.index('_')]

            if pID not in pIDs:  # new dictionary entry
                pIDs.append(pID)
                
                pEntry = OrderedDict()  # create new patient entry

                pEntry['ID'] = pID  # converting to float breaks something?
                pEntry['ID_int'] = int(pID)
                pEntry['name'] = "Patient " + str(pID)

                pEntry['tumorVolume'] = 0.0

                if '_cent' in fname:  # parse centroids file
                    pEntry['organData'] = FillOrganData(f, organRef, pID)
                else:
                    pEntry['organData'] = {}  # placeholder

                pEntry['ID_internal'] = count

                if '_dist' in fname:  # parse distances file
                    data = FillMatrix(f, organRef, pID)
                    pEntry['matrix'] = data[0]
                    pEntry['matrix_tumorDistances'] = data[1]
                    pEntry['hasGTVp'] = data[2]
                    pEntry['hasGTVn'] = data[3]
                else:
                    pEntry['matrix'] = []  # placeholder
                    pEntry['matrix_tumorDistances'] = []
                    pEntry['hasGTVp'] = False
                    pEntry['hasGTVn'] = False
                
                pEntry['matrix_ssim'] = []

                pEntry['matrix_ssim_dist'] = []
                pEntry['matrix_ssim_vol'] = []

                pEntry['matrix_dose'] = []

                pEntry['matrix_TumorVolume'] = []

                pEntry['matrix_pos'] = []

                pEntry['similarity'] = []
                pEntry['scores'] = []

                pEntry['similarity_ssim'] = []
                pEntry['scores_ssim'] = []

                pEntry['laterality'] = ""
                pEntry['laterality_int'] = -1
                pEntry['tumorSubsite'] = ""

                patients.append(pEntry)

                count += 1
            else:                # modify existing dictionary entry
                pEntry = next(
                    (item for item in patients if item['ID'] == pID), None)  # find entry

                if '_cent' in fname:  # parse centroids file
                    if pEntry != None:
                        pEntry['organData'] = FillOrganData(f, organRef, pID)

                if '_dist' in fname:  # parse distances file
                    if pEntry != None:
                        data = FillMatrix(f, organRef, pID)
                        pEntry['matrix'] = data[0]
                        pEntry['matrix_tumorDistances'] = data[1]
                        pEntry['hasGTVp'] = data[2]
                        pEntry['hasGTVn'] = data[3]

    #print (organRef)
    #organRef.sort()
    #print ("Organ Reference: ")
    #print("\n")
    #print ("\nLength", len(organRef))

    # alg compares tumor distances, then for laterality left and right are equal? is this right?
    # read in laterality
    with open("laterality.csv", 'rb') as csvFile:
        reader = csv.reader(csvFile)
        header = next(reader)

        for row in reader:
            for p in patients:
                if str(row[0]) == p['ID']:
                    p['laterality'] = str(row[1])
                    p['tumorSubsite'] = str(row[2])

                    if str(row[1]) in ["L", "R"]:
                        p['laterality_int'] = 0
                    elif str(row[1]) == "Bilateral":
                        p['laterality_int'] = 1

    # make sure matrices are all same size [check]
    # fill matrix diagonal [check]
    # ask liz how to handle organ values missing for patients
    # what do do with negative distances

    # delete columns and rows corresponding to GTVn # ---------------------------------------------
    # ended up not using GTVn for similarity computation
    # now deleting both tumors, use has_key or indexOf to make sure the right rows/columns are being deleted
    for currP in patients:

        if organRef[0] != "GTVn" and organRef[1] != "GTVp":
            print ("WARNING: GTV in wrong row/column. Incorrect format.")


        currP['matrix'] = np.delete(currP['matrix'], (0), axis=0) # delete first row
        currP['matrix'] = np.delete(currP['matrix'], (0), axis=1) # delete first column

        currP['matrix_tumorDistances'] = np.delete(currP['matrix_tumorDistances'], (0), axis=0) # delete first row
        currP['matrix_tumorDistances'] = np.delete(currP['matrix_tumorDistances'], (0), axis=1) # delete first column


        # DO IT AGAIN FOR GTVp

        currP['matrix'] = np.delete(currP['matrix'], (0), axis=0) # delete first row
        currP['matrix'] = np.delete(currP['matrix'], (0), axis=1) # delete first column

        currP['matrix_tumorDistances'] = np.delete(currP['matrix_tumorDistances'], (0), axis=0) # delete first row
        currP['matrix_tumorDistances'] = np.delete(currP['matrix_tumorDistances'], (0), axis=1) # delete first column
    
    organRef.remove("GTVp")
    organRef.remove("GTVn")

    for p in patients:
        #p['matrix'].resize((len(organRef), len(organRef)))
        # add padding to matrix so all matrices are the same size
        padSize = len(organRef) - p['matrix'].shape[0]
        p['matrix'] = np.lib.pad(p['matrix'], ((0, padSize), (0, padSize)), mode='constant')
        p['matrix_tumorDistances'] = np.lib.pad(p['matrix_tumorDistances'], ((0, padSize), (0, padSize)), mode='constant')

        organs = p['organData']

        ##posMatrix = np.zeros((3, len(organRef)))
        #posMatrix = np.zeros((1, len(organRef)))

        matrixCopy = np.copy(p['matrix'])

        #print(p['matrix'])

        # initiliaze dose matrix
        p['matrix_dose'] = np.zeros((len(organRef), len(organRef)))

        # initiliaze tumor volume matrix
        p['matrix_TumorVolume'] = np.zeros((len(organRef), len(organRef)))

        #print(p['name'])

        if p['hasGTVp']:
            #print(p['organData']['GTVp']['volume'])
            p['tumorVolume'] = p['organData']['GTVp']['volume']
        #elif p['hasGTVn']:
        #    #print('GTVn: ' + str(p['organData']['GTVn']['volume']))
        #    p['tumorVolume'] = p['organData']['GTVn']['volume']
        #else:
            #print("neither")
        

        for organ in organs.items():  # populate diagonal of matrix with mean dose data
            #if p['ID'] == "222":
            # print(organ)
            #print (organ[1]['meanDose'])
            #print(organ[0], organ[1]['x'], organ[1]['y'], organ[1]['z'], organ[1]['meanDose'])

            if organ[0] != "GTVp" and organ[0] != "GTVn":
                p['matrix'][organRef.index(organ[0]), organRef.index(organ[0])] = organ[1]['meanDose']
                #p['matrix'][organRef.index(organ[0]), organRef.index(organ[0])] = 1.0

                #populate dose matrix
                p['matrix_dose'][organRef.index(organ[0]), organRef.index(organ[0])] = organ[1]['meanDose']
                p['matrix_TumorVolume'][organRef.index(organ[0]), organRef.index(organ[0])] = p['tumorVolume']

                # populate position matrix
                ##posMatrix[0, organRef.index(organ[0])] = organ[1]['x']
                ##posMatrix[1, organRef.index(organ[0])] = organ[1]['y']
                ##posMatrix[2, organRef.index(organ[0])] = organ[1]['z']
        
        #if p['ID'] == "2007":
        #    for x in range(47):
        #        print(p['matrix'][x, x])
        #        #posMatrix[0, x] = int(p['ID'])
        
        ##p['matrix_pos'] = posMatrix
        #print(p['matrix_dose'])
        #print(matrixCopy)

        #p['matrix_ssim'] = np.matmul(matrixCopy, p['matrix_dose'])
        p['matrix_ssim'] = np.dot(matrixCopy, p['matrix_dose'])

        ####
        # SHOULD WE DELETE ROWS/COLS first before dot product?
        #p['matrix_ssim'] = np.dot(matrixCopy, p['matrix_tumorDistances'])

        p['matrix_ssim_dist'] = np.dot(matrixCopy, p['matrix_tumorDistances'])
        p['matrix_ssim_vol'] = np.dot(matrixCopy, p['matrix_TumorVolume'])

        #p['matrix_ssim_dist'] = np.dot(p['matrix_ssim_dist'], p['matrix_dose'])
        #p['matrix_ssim_vol'] = np.dot(p['matrix_ssim_vol'], p['matrix_dose'])

        #print(p['name'])
        #print(p['matrix_tumorDistances'])

        #p['matrix_ssim'] = np.dot(p['matrix_ssim'], p['matrix_TumorVolume'])

        #p['matrix_ssim'] = np.dot(p['matrix_ssim'], p['matrix_dose'])

        ####

        #print(p['name'])
        #print(p['matrix_TumorVolume'])

        #p['matrix_ssim'] = np.copy(p['matrix'])
        #print(p['matrix_ssim'])

    ###########
    print (len(organRef))
    print (organRef)

    ###########

    # delete positions of organs except for GTVp until better method found (e.g. vectors instead of positions)
    #for currP in patients:
    #    currP['matrix_pos'] = currP['matrix_pos'][:,0]
    #    #print (currP['matrix_pos'])
    

    
    pSimMatrix = np.zeros((len(patients) + 1, len(patients) + 1))

    # Calculate Pearson correlation coefficients
    # calculate ssim score
    for currP in patients:
        print(currP['ID_internal'])
        # currP['ID_internal']
        correlations = []
        ssimResults = []
        for nextP in patients:
            pCoeff_1 = pearsonr(currP['matrix'].flat, nextP['matrix'].flat)[0]
            #ssimScor = myssim.ssim(matlab.double(currP['matrix_ssim'].tolist()), matlab.double(nextP['matrix_ssim'].tolist()))
            ssimScor_dist = myssim.ssim(matlab.double(currP['matrix_ssim_dist'].tolist()), matlab.double(nextP['matrix_ssim_dist'].tolist()))
            ssimScor_vol = myssim.ssim(matlab.double(currP['matrix_ssim_vol'].tolist()), matlab.double(nextP['matrix_ssim_vol'].tolist()))

            if currP['laterality_int'] == nextP['laterality_int']:
                ssimScor = (ssimScor_dist + ssimScor_vol + 1) / 3.0
            else:
                ssimScor = (ssimScor_dist + ssimScor_vol + 0) / 3.0
            

            #ssimScor = 1.0
            if (ssimScor <= 0.0):
                #ssimScor = 0
                print (currP['name'])
                print (nextP['name'])
                print (currP['matrix_ssim'])
                print (nextP['matrix_ssim'])
            
            pSimMatrix[currP['ID_internal'], nextP['ID_internal']] = ssimScor
            pSimMatrix[0, currP['ID_internal']] = int(currP['ID'])
            pSimMatrix[currP['ID_internal'], 0] = int(currP['ID'])
            #pSimMatrix[nextP['ID_internal'], currP['ID_internal']] = ssimScor
            #pCoeff_1 = spatial.distance.correlation(currP['matrix'].flat, nextP['matrix'].flat)
            #pCoeff_1 = np.cov(currP['matrix'].flat, nextP['matrix'].flat)[0][1]
            ##pCoeff_1 = ( np.cov(currP['matrix'].flat, bias=True) - 1 ) * ( np.cov(currP['matrix'].flat, nextP['matrix'].flat, bias=True)[0][1] )
            #pCoeff_1 = spearmanr(currP['matrix'].flat, nextP['matrix'].flat)[0]
            #pCoeff_1 = ( currP['matrix'] - 1 ) * ( np.cov(currP['matrix'].flat, nextP['matrix'].flat, bias=True)[0][1] )
            #pCoeff_2 = pearsonr(currP['matrix_pos'].flat, nextP['matrix_pos'].flat)[0]
            #print(pCoeff_1)

            #if math.isnan(pCoeff_2):
            #    pCoeff_2 = 0.0

            #if (pCoeff_1 > 1.0):
            #    pCoeff_1 = 2 - pCoeff_1

            #correlations.append((nextP['ID_internal'], (5*pCoeff_1 + pCoeff_2)/6.0 ))
            correlations.append((nextP['ID_internal'], pCoeff_1))
            ssimResults.append((nextP['ID_internal'], ssimScor))

        correlations = sorted(correlations, key=itemgetter(1), reverse=True)
        ssimResults = sorted(ssimResults, key=itemgetter(1), reverse=True)

        for score in correlations:
            currP["similarity"].append(score[0])
            currP["scores"].append(score[1])

        for score in ssimResults:
            currP["similarity_ssim"].append(score[0])
            currP["scores_ssim"].append(score[1])
        
        # array.reshape(-1, 1) if your data has a single feature or array.reshape(1, -1) if it contains a single sample
        reshaped = np.array(currP["scores_ssim"]).reshape(-1, 1)
        kmeans = KMeans().fit(reshaped)
        print ("")
        print (currP["ID"])
        print (kmeans.cluster_centers_)
        print (kmeans.labels_)
        print ("")
        

        # print(correlations)
        # print('\n')

    #print (organRef)
    #print (len(organRef))


    #for p in patients:
    #    with open("patients_dose/" + p['ID'] + "_dose.csv", "w+") as my_csv:
    #        csvWriter = csv.writer(my_csv, delimiter=',')
    #        csvWriter.writerows(p['matrix'])

    #with open("matrix_p206_ssim.csv", "w+") as my_csv:
    #    csvWriter = csv.writer(my_csv, delimiter=',')
    #    csvWriter.writerows(patients[101]['matrix_ssim'])
    #    #print("ID", patients[50]['ID']) # patients[50]['ID'] corresponds to patient 248

    with open("matrix_p222_ssim_noDoses.csv", "w+") as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=',')
        csvWriter.writerows(patients[0]['matrix_ssim'])
        #print("ID", patients[50]['ID']) # patients[50]['ID'] corresponds to patient 248
    
    with open("pSimMatrix_noDoses.csv", "w+") as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=',')
        csvWriter.writerows(pSimMatrix)
        #print("ID", patients[50]['ID']) # patients[50]['ID'] corresponds to patient 248

    # commented out because deleting all organs except for tumor
    #with open("matrix_pos_test.csv", "w+") as my_csv:
    #    csvWriter = csv.writer(my_csv, delimiter=',')
    #    csvWriter.writerows(patients[50]['matrix_pos'])

    myssim.terminate()

    for p in patients:  # json can't handle too many matrices, delete the matrices
        del p['matrix']
        del p['matrix_pos']
        del p['matrix_ssim']
        del p['matrix_ssim_dist']
        del p['matrix_ssim_vol']
        del p['matrix_dose']
        del p['matrix_tumorDistances']
        del p['matrix_TumorVolume']
    
    # sort patient list before outputting to json
    #sorted_patients = sorted(patients, key=itemgetter('ID_int')) 


    with open('patients_SSIM_wDoses_wDists.json', 'w+') as f:  # generate JSON
        json.dump(patients, f, indent=4)

    #with open('organAtlas.json', 'w+') as f:  # generate JSON
    #    json.dump(organRef, f, indent=4)

    #organRef.sort()
    #print ("\nOrgan Reference Sorted: ")


if __name__ == '__main__':
    # command-line argument specifies
    # patients parent directory
    main(sys.argv[1])


# ---------------------------------------------------------------------
# Input: 2 objects
# Output: Pearson Correlation Score
def pearson_correlation(object1, object2):
    values = range(len(object1))
    
    # Summation over all attributes for both objects
    sum_object1 = sum([float(object1[i]) for i in values]) 
    sum_object2 = sum([float(object2[i]) for i in values])

    # Sum the squares
    square_sum1 = sum([pow(object1[i],2) for i in values])
    square_sum2 = sum([pow(object2[i],2) for i in values])

    # Add up the products
    product = sum([object1[i]*object2[i] for i in values])

    #Calculate Pearson Correlation score
    numerator = product - (sum_object1*sum_object2/len(object1))
    denominator = ((square_sum1 - pow(sum_object1,2)/len(object1)) * (square_sum2 - 
    	pow(sum_object2,2)/len(object1))) ** 0.5
        
    # Can"t have division by 0
    if denominator == 0:
        return 0

    result = numerator/denominator
    return result

def mean2(x):
    y = np.sum(x) / np.size(x)
    return y

def corr2(a,b):
    a = a - mean2(a)
    b = b - mean2(b)

    r = (a*b).sum() / math.sqrt((a*a).sum() * (b*b).sum())
    return r

def scale_linear_bycolumn(rawpoints, high, low):
    #mins = np.min(rawpoints, axis=0)
    #maxs = np.max(rawpoints, axis=0)
    rng = high - low
    return 1.0 - (((1.0 - 0.0) * (high - rawpoints)) / rng)
    #return high - (((high - low) * (maxs - rawpoints)) / rng)