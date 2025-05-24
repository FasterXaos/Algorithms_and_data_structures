import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import matthews_corrcoef, adjusted_rand_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt


def loadDataset(filePath: str) -> pd.DataFrame:
    if filePath.lower().endswith('.arff'):
        data, meta = arff.loadarff(filePath)
        df = pd.DataFrame(data)
        for col in df.select_dtypes([object]).columns:
            if isinstance(df[col].iloc[0], (bytes, bytearray)):
                df[col] = df[col].str.decode('utf-8')
        return df
    else:
        return pd.read_csv(filePath)

def preprocessFeatures(dataFrame: pd.DataFrame):
    dfCopy = dataFrame.copy()
    for columnName in dfCopy.columns:
        if not pd.api.types.is_numeric_dtype(dfCopy[columnName]):
            encoder = LabelEncoder()
            dfCopy[columnName] = encoder.fit_transform(
                dfCopy[columnName].astype(str)
            )
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

def anonymizeDf(df: pd.DataFrame) -> pd.DataFrame:
    anonymized = df.copy()
    # duration
    bins = [-1,0,1,2,5,10,100,1000,1e6]
    labels = ['0','1','2','3-5','6-10','11-100','101-1000','>1000']
    anonymized['duration'] = pd.cut(anonymized['duration'], bins=bins, labels=labels)
    # service
    web = {'http','https','ecr_i'}
    mail = {'smtp','pop3','imap'}
    anonymized['service'] = anonymized['service'].apply(
        lambda v: 'web' if v in web else ('mail' if v in mail else 'other')
    )
    # flag
    top = {'SF','S0','REJ'}
    anonymized['flag'] = anonymized['flag'].apply(lambda v: v if v in top else 'OTHER')
    # bytes
    for col in ['src_bytes','dst_bytes']:
        anonymized[col] = pd.cut(
            np.log1p(anonymized[col]), bins=5,
            labels=[f'bin{i}' for i in range(5)]
        )
    # binary fields
    binCols = ['land','logged_in','lnum_outbound_cmds','is_host_login','is_guest_login']
    for c in binCols:
        anonymized[c] = anonymized[c].astype(str)
    # wrong_fragment, urgent
    anonymized['wrong_fragment'] = anonymized['wrong_fragment'].apply(lambda x: '0' if x==0 else '>0')
    anonymized['urgent'] = anonymized['urgent'].apply(lambda x: '0' if x==0 else '>0')
    # hot
    maxHot = anonymized['hot'].max()
    anonymized['hot'] = pd.cut(anonymized['hot'], bins=[-1,0,1,5,10,maxHot],
                                labels=['0','1','2-5','6-10','>10'])
    # failed logins
    maxLog = anonymized['num_failed_logins'].max()
    anonymized['num_failed_logins'] = pd.cut(
        anonymized['num_failed_logins'], bins=[-1,0,1,2,maxLog], labels=['0','1','2','>2']
    )
    # compromised
    maxComp = anonymized['lnum_compromised'].max()
    anonymized['lnum_compromised'] = pd.cut(
        anonymized['lnum_compromised'], bins=[-1,0,1,2,5,maxComp], labels=['0','1','2','3-5','>5']
    )
    # root shell, su
    anonymized['lroot_shell'] = anonymized['lroot_shell'].apply(lambda x: '0' if x==0 else '>0')
    anonymized['lsu_attempted'] = anonymized['lsu_attempted'].apply(lambda x: '0' if x==0 else '>0')
    # num_root, file_creations
    maxRoot = anonymized['lnum_root'].max()
    anonymized['lnum_root'] = pd.cut(anonymized['lnum_root'], bins=[-1,0,1,2,5,maxRoot],labels=['0','1','2','3-5','>5'])
    maxFile = anonymized['lnum_file_creations'].max()
    anonymized['lnum_file_creations'] = pd.cut(anonymized['lnum_file_creations'],bins=[-1,0,1,2,5,maxFile],labels=['0','1','2','3-5','>5'])
    anonymized['lnum_shells'] = anonymized['lnum_shells'].apply(lambda x: '0' if x==0 else ('1' if x==1 else '>1'))
    maxAccess = anonymized['lnum_access_files'].max()
    anonymized['lnum_access_files'] = pd.cut(anonymized['lnum_access_files'],bins=[-1,0,1,2,maxAccess],labels=['0','1','2','>2'])
    for col in ['count','srv_count']:
        maxv = anonymized[col].max()
        anonymized[col] = pd.cut(anonymized[col], bins=[-1,0,1,10,100,maxv], labels=['0','1','2-10','11-100','>100'])
    # rates
    rateCols = [
        'serror_rate','srv_serror_rate','rerror_rate','srv_rerror_rate',
        'same_srv_rate','diff_srv_rate','srv_diff_host_rate',
        'dst_host_count','dst_host_srv_count','dst_host_same_srv_rate',
        'dst_host_diff_srv_rate','dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate','dst_host_serror_rate',
        'dst_host_srv_serror_rate','dst_host_rerror_rate','dst_host_srv_rerror_rate'
    ]
    for col in rateCols:
        if pd.api.types.is_numeric_dtype(anonymized[col]):
            if col in ['dst_host_count','dst_host_srv_count']:
                anonymized[col] = pd.cut(anonymized[col], bins=[-1,100,200,256], labels=['[0-100)','[100-200)','[200-255]'])
            else:
                anonymized[col] = pd.cut(anonymized[col], bins=[-1,0,0.5,1], labels=['0','(0,0.5]','(0.5,1]'])
    return anonymized

def main(path: str):
    df = loadDataset(path)

    # Raw data clustering and PCA
    featsRaw, labelsRaw, namesRaw = preprocessFeatures(df)
    idxRaw = selectTopFeatures(featsRaw, 5)
    selNamesRaw = [namesRaw[i] for i in idxRaw]
    redRaw = featsRaw[:, idxRaw]
    normRaw = normalizeMatrix(redRaw)
    k = len(np.unique(labelsRaw))
    predRaw = runMaximinClustering(normRaw, k)
    print('Raw Top features:', selNamesRaw)
    print('Raw Phi:', matthews_corrcoef(labelsRaw, predRaw))
    print('Raw ARI:', adjusted_rand_score(labelsRaw, predRaw))

    pRaw = PCA(2).fit_transform(normRaw)
    countsRaw = pd.Series(predRaw).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8,6))
    for lbl, cnt in countsRaw.items():
        mask = predRaw == lbl
        ax.scatter(pRaw[mask,0], pRaw[mask,1], label=f'{lbl} ({cnt})', alpha=0.7)
    ax.set_title('PCA Projection Before Anonymization')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.legend(title='Cluster', bbox_to_anchor=(1.02,1.1), loc='upper left')
    fig.subplots_adjust(right=0.70, top=0.90)
    plt.show()

    # Anonymize
    dfAnon = anonymizeDf(df)
    featsAnon, labelsAnon, namesAnon = preprocessFeatures(dfAnon)
    idxAnon = selectTopFeatures(featsAnon, 5)
    selNamesAnon = [namesAnon[i] for i in idxAnon]
    redAnon = featsAnon[:, idxAnon]
    normAnon = normalizeMatrix(redAnon)
    predAnon = runMaximinClustering(normAnon, k)
    print('Anon Top features:', selNamesAnon)
    print('Anon Phi:', matthews_corrcoef(labelsAnon, predAnon))
    print('Anon ARI:', adjusted_rand_score(labelsAnon, predAnon))

    pAnon = PCA(2).fit_transform(normAnon)
    countsAnon = pd.Series(predAnon).value_counts().sort_index()
    fig2, ax2 = plt.subplots(figsize=(8,6))
    for lbl, cnt in countsAnon.items():
        mask = predAnon == lbl
        ax2.scatter(pAnon[mask,0], pAnon[mask,1], label=f'{lbl} ({cnt})', alpha=0.7)
    ax2.set_title('PCA Projection After Anonymization')
    ax2.set_xlabel('PC1')
    ax2.set_ylabel('PC2')
    ax2.legend(title='Cluster', bbox_to_anchor=(1.02,1.15), loc='upper left')
    fig2.subplots_adjust(right=0.70, top=0.88)
    plt.show()


if __name__ == '__main__':
    main("KDDCup99.arff")
