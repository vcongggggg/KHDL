from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import f1_score, classification_report
import numpy as np

categories = ['sci.space', 'sci.med', 'talk.politics.misc', 'comp.graphics', 'rec.autos']
print('Load data...')
train = fetch_20newsgroups(subset='train', categories=categories, shuffle=True, random_state=42, remove=('headers', 'footers', 'quotes'))
test  = fetch_20newsgroups(subset='test',  categories=categories, shuffle=True, random_state=42, remove=('headers', 'footers', 'quotes'))
print(f'Train: {len(train.data)}, Test: {len(test.data)}, Classes: {train.target_names}')

tfidf = TfidfVectorizer(max_features=5000, min_df=2, stop_words='english', sublinear_tf=True)
X_tr = tfidf.fit_transform(train.data)
X_te = tfidf.transform(test.data)
print(f'TF-IDF shape: {X_tr.shape}')

svd = TruncatedSVD(n_components=100, random_state=42)
X_tr_svd = svd.fit_transform(X_tr)
X_te_svd  = svd.transform(X_te)
print(f'SVD shape: {X_tr_svd.shape}, Explained variance: {svd.explained_variance_ratio_.sum():.2%}')

sc = StandardScaler()
X_tr_sc = sc.fit_transform(X_tr_svd)
X_te_sc = sc.transform(X_te_svd)

model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv = cross_val_score(model, X_tr_sc, train.target, cv=skf, scoring='f1_macro')
print(f'CV F1-macro: {cv.mean():.4f} +- {cv.std():.4f}')

model.fit(X_tr_sc, train.target)
y_pred = model.predict(X_te_sc)
f1 = f1_score(test.target, y_pred, average='macro')
print(f'Test F1-macro: {f1:.4f}')
print(classification_report(test.target, y_pred, target_names=train.target_names, digits=4))
print('OK - Pipeline chay thanh cong!')
