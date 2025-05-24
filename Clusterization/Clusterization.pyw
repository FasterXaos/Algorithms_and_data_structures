import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import matthews_corrcoef, adjusted_rand_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def loadDataset(filePath: str) -> pd.DataFrame:
    if filePath.lower().endswith('.arff'):
        rawData, meta = arff.loadarff(filePath)
        dataFrame = pd.DataFrame(rawData)
        for column in dataFrame.select_dtypes([object]).columns:
            if isinstance(dataFrame[column].iloc[0], (bytes, bytearray)):
                dataFrame[column] = dataFrame[column].str.decode('utf-8')
        return dataFrame
    else:
        return pd.read_csv(filePath)


def preprocessFeatures(dataFrame: pd.DataFrame):
    dfCopy = dataFrame.copy()
    for column in dfCopy.columns:
        if not pd.api.types.is_numeric_dtype(dfCopy[column]):
            encoder = LabelEncoder()
            dfCopy[column] = encoder.fit_transform(dfCopy[column].astype(str))
    featureMatrix = dfCopy.drop(columns=["label"]).values
    trueLabels = dfCopy["label"].values
    featureNames = dfCopy.drop(columns=["label"]).columns.tolist()
    return featureMatrix, trueLabels, featureNames


def selectTopFeatures(featureMatrix: np.ndarray, featureCount: int):
    variances = np.var(featureMatrix, axis=0)
    return np.argsort(variances)[::-1][:featureCount]


def normalizeMatrix(matrix: np.ndarray):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


def runMaximinClustering(normalizedFeatures: np.ndarray, uniqueCount: int):
    centers = [0]
    for _ in range(1, uniqueCount):
        centersMatrix = normalizedFeatures[centers]
        corrMatrix = normalizedFeatures @ centersMatrix.T
        distanceMatrix = 1.0 - corrMatrix
        minDistances = distanceMatrix.min(axis=1)
        nextCenter = int(np.argmax(minDistances))
        centers.append(nextCenter)
    centersMatrix = normalizedFeatures[centers]
    distanceMatrix = 1.0 - (normalizedFeatures @ centersMatrix.T)
    return np.argmin(distanceMatrix, axis=1)


def anonymizeDf(dataFrame: pd.DataFrame) -> pd.DataFrame:
    anonymizedDataFrame = dataFrame.copy()
    # duration
    bins = [-1,0,1,2,5,10,100,1000,1e6]
    labels = ['0','1','2','3-5','6-10','11-100','101-1000','>1000']
    anonymizedDataFrame['duration'] = pd.cut(anonymizedDataFrame['duration'], bins=bins, labels=labels)
    # service
    webSet = {'http','https','ecr_i'}
    mailSet = {'smtp','pop3','imap'}
    anonymizedDataFrame['service'] = anonymizedDataFrame['service'].apply(
        lambda v: 'web' if v in webSet else ('mail' if v in mailSet else 'other')
    )
    # flag
    topFlags = {'SF','S0','REJ'}
    anonymizedDataFrame['flag'] = anonymizedDataFrame['flag'].apply(lambda v: v if v in topFlags else 'OTHER')
    # bytes
    for col in ['src_bytes','dst_bytes']:
        anonymizedDataFrame[col] = pd.cut(
            np.log1p(anonymizedDataFrame[col]), bins=5,
            labels=[f'bin{i}' for i in range(5)]
        )
    # binary fields
    binaryColumns = ['land','logged_in','lnum_outbound_cmds','is_host_login','is_guest_login']
    for col in binaryColumns:
        anonymizedDataFrame[col] = anonymizedDataFrame[col].astype(str)
    # wrong_fragment, urgent
    anonymizedDataFrame['wrong_fragment'] = anonymizedDataFrame['wrong_fragment'].apply(lambda x: '0' if x==0 else '>0')
    anonymizedDataFrame['urgent'] = anonymizedDataFrame['urgent'].apply(lambda x: '0' if x==0 else '>0')
    # hot
    maxHot = anonymizedDataFrame['hot'].max()
    anonymizedDataFrame['hot'] = pd.cut(anonymizedDataFrame['hot'], bins=[-1,0,1,5,10,maxHot],
                                       labels=['0','1','2-5','6-10','>10'])
    # failed logins
    maxLogins = anonymizedDataFrame['num_failed_logins'].max()
    anonymizedDataFrame['num_failed_logins'] = pd.cut(
        anonymizedDataFrame['num_failed_logins'], bins=[-1,0,1,2,maxLogins], labels=['0','1','2','>2']
    )
    # compromised
    maxCompromised = anonymizedDataFrame['lnum_compromised'].max()
    anonymizedDataFrame['lnum_compromised'] = pd.cut(
        anonymizedDataFrame['lnum_compromised'], bins=[-1,0,1,2,5,maxCompromised], labels=['0','1','2','3-5','>5']
    )
    # root shell, su
    anonymizedDataFrame['lroot_shell'] = anonymizedDataFrame['lroot_shell'].apply(lambda x: '0' if x==0 else '>0')
    anonymizedDataFrame['lsu_attempted'] = anonymizedDataFrame['lsu_attempted'].apply(lambda x: '0' if x==0 else '>0')
    # num_root, file_creations
    maxRoot = anonymizedDataFrame['lnum_root'].max()
    anonymizedDataFrame['lnum_root'] = pd.cut(anonymizedDataFrame['lnum_root'], bins=[-1,0,1,2,5,maxRoot],labels=['0','1','2','3-5','>5'])
    maxFile = anonymizedDataFrame['lnum_file_creations'].max()
    anonymizedDataFrame['lnum_file_creations'] = pd.cut(anonymizedDataFrame['lnum_file_creations'],bins=[-1,0,1,2,5,maxFile],labels=['0','1','2','3-5','>5'])
    anonymizedDataFrame['lnum_shells'] = anonymizedDataFrame['lnum_shells'].apply(lambda x: '0' if x==0 else ('1' if x==1 else '>1'))
    maxAccess = anonymizedDataFrame['lnum_access_files'].max()
    anonymizedDataFrame['lnum_access_files'] = pd.cut(anonymizedDataFrame['lnum_access_files'],bins=[-1,0,1,2,maxAccess],labels=['0','1','2','>2'])
    for col in ['count','srv_count']:
        maxVal = anonymizedDataFrame[col].max()
        anonymizedDataFrame[col] = pd.cut(anonymizedDataFrame[col], bins=[-1,0,1,10,100,maxVal], labels=['0','1','2-10','11-100','>100'])
    # rate columns
    rateColumns = [
        'serror_rate','srv_serror_rate','rerror_rate','srv_rerror_rate',
        'same_srv_rate','diff_srv_rate','srv_diff_host_rate',
        'dst_host_count','dst_host_srv_count','dst_host_same_srv_rate',
        'dst_host_diff_srv_rate','dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate','dst_host_serror_rate',
        'dst_host_srv_serror_rate','dst_host_rerror_rate','dst_host_srv_rerror_rate'
    ]
    for col in rateColumns:
        if pd.api.types.is_numeric_dtype(anonymizedDataFrame[col]):
            if col in ['dst_host_count','dst_host_srv_count']:
                anonymizedDataFrame[col] = pd.cut(anonymizedDataFrame[col], bins=[-1,100,200,256], labels=['[0-100)','[100-200)','[200-255]'])
            else:
                anonymizedDataFrame[col] = pd.cut(anonymizedDataFrame[col], bins=[-1,0,0.5,1], labels=['0','(0,0.5]','(0.5,1]'])
    return anonymizedDataFrame


def main(filePath: str, featureCount: int):
    dataFrame = loadDataset(filePath)

    # Clustering and PCA on raw data
    featuresRaw, labelsRaw, featureNamesRaw = preprocessFeatures(dataFrame)
    indicesRaw = selectTopFeatures(featuresRaw, featureCount)
    selectedFeatureNamesRaw = [featureNamesRaw[i] for i in indicesRaw]
    reducedRaw = featuresRaw[:, indicesRaw]
    normalizedRaw = normalizeMatrix(reducedRaw)
    clusterCount = len(np.unique(labelsRaw))
    predictionsRaw = runMaximinClustering(normalizedRaw, clusterCount)

    print('Raw Top features:', selectedFeatureNamesRaw)
    print('Raw Phi:', matthews_corrcoef(labelsRaw, predictionsRaw))
    print('Raw ARI:', adjusted_rand_score(labelsRaw, predictionsRaw))

    # 2D PCA before anonymization
    pca2dRaw = PCA(2).fit_transform(normalizedRaw)
    countsRaw = pd.Series(predictionsRaw).value_counts().sort_index()
    fig1, ax1 = plt.subplots(figsize=(8,6))
    for lbl, cnt in countsRaw.items():
        mask = predictionsRaw == lbl
        ax1.scatter(pca2dRaw[mask,0], pca2dRaw[mask,1], label=f'{lbl} ({cnt})', alpha=0.7)
    ax1.set_title('PCA Projection Before Anonymization (2D)')
    ax1.set_xlabel('PC1')
    ax1.set_ylabel('PC2')
    ax1.legend(title='Cluster', bbox_to_anchor=(1.02,1.1), loc='upper left')
    fig1.subplots_adjust(right=0.70, top=0.90)
    plt.show()

    # Anonymize and repeat
    anonymizedDataFrame = anonymizeDf(dataFrame)
    featuresAnon, labelsAnon, featureNamesAnon = preprocessFeatures(anonymizedDataFrame)
    indicesAnon = selectTopFeatures(featuresAnon, featureCount)
    selectedFeatureNamesAnon = [featureNamesAnon[i] for i in indicesAnon]
    reducedAnon = featuresAnon[:, indicesAnon]
    normalizedAnon = normalizeMatrix(reducedAnon)
    predictionsAnon = runMaximinClustering(normalizedAnon, clusterCount)

    print('Anon Top features:', selectedFeatureNamesAnon)
    print('Anon Phi:', matthews_corrcoef(labelsAnon, predictionsAnon))
    print('Anon ARI:', adjusted_rand_score(labelsAnon, predictionsAnon))

    # 2D PCA after anonymization
    pca2dAnon = PCA(2).fit_transform(normalizedAnon)
    countsAnon = pd.Series(predictionsAnon).value_counts().sort_index()
    fig2, ax2 = plt.subplots(figsize=(8,6))
    for lbl, cnt in countsAnon.items():
        mask = predictionsAnon == lbl
        ax2.scatter(pca2dAnon[mask,0], pca2dAnon[mask,1], label=f'{lbl} ({cnt})', alpha=0.7)
    ax2.set_title('PCA Projection After Anonymization (2D)')
    ax2.set_xlabel('PC1')
    ax2.set_ylabel('PC2')
    ax2.legend(title='Cluster', bbox_to_anchor=(1.02,1.15), loc='upper left')
    fig2.subplots_adjust(right=0.70, top=0.88)
    plt.show()

    # 3D PCA before and after anonymization (third graph)
    pca3dRaw = PCA(3).fit_transform(normalizedRaw)
    pca3dAnon = PCA(3).fit_transform(normalizedAnon)
    fig3 = plt.figure(figsize=(16,6))
    ax3 = fig3.add_subplot(121, projection='3d')
    for lbl in np.unique(predictionsRaw):
        mask = predictionsRaw == lbl
        ax3.scatter(pca3dRaw[mask,0], pca3dRaw[mask,1], pca3dRaw[mask,2], label=f'{lbl}', alpha=0.7)
    ax3.set_title('PCA Projection Before Anonymization (3D)')
    ax3.set_xlabel('PC1')
    ax3.set_ylabel('PC2')
    ax3.set_zlabel('PC3')
    ax3.legend(title='Cluster', bbox_to_anchor=(1.02,1.1), loc='upper left')

    ax4 = fig3.add_subplot(122, projection='3d')
    for lbl in np.unique(predictionsAnon):
        mask = predictionsAnon == lbl
        ax4.scatter(pca3dAnon[mask,0], pca3dAnon[mask,1], pca3dAnon[mask,2], label=f'{lbl}', alpha=0.7)
    ax4.set_title('PCA Projection After Anonymization (3D)')
    ax4.set_xlabel('PC1')
    ax4.set_ylabel('PC2')
    ax4.set_zlabel('PC3')
    ax4.legend(title='Cluster', bbox_to_anchor=(1.02,1.1), loc='upper left')

    fig3.subplots_adjust(right=0.85, top=0.90)
    plt.show()


if __name__ == '__main__':
    main("KDDCup99.arff", 10)
