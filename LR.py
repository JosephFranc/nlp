import pandas as pd
import string
import re
import nltk
import scipy
import sklearn.feature_extraction.text
import numpy as np

from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn import linear_model
from collections import Counter
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk import word_tokenize
from nltk.util import ngrams
from sklearn.preprocessing import OneHotEncoder

def load(path):
    data = pd.read_csv(path,header = None)
    data = data[[1,2]]
    data.columns = ['labels','news']
    data['news'] = data['news'].map(lambda x: x.lower().translate(dict((ord(char), None) for char in string.punctuation if char!='\'' and char!='-')) )  
    data['news'] = data['news'].map(lambda x: x.replace('\n',' '))
    return data

# if we want to calculate correlation, we shall rewrite those str lables
def repl(t):
    t.replace('half-true','0.5', inplace=True)
    t.replace('mostly-true','0.8', inplace=True)
    t.replace('barely-true','0.3', inplace=True)
    t.replace('pants-fire','-1', inplace=True)

def lex_feature(data,lex):
    data = data.copy()
    data['news'] = data['news'].map(lambda x: [i.lower() for i in re.findall("\S+",x) if re.search('\w',i)!=None])
    for cl in set(lex[1]):
        words = lex[lex[1]==cl][0]
        data[cl] = data.news.map(lambda x: sum([1. for j in words for k in x if re.match('^'+j.replace('*','.+')+'$',k)]))
    return data

def unigrams(data, test):
    data = data.copy()
    Vectorizer = sklearn.feature_extraction.text.TfidfVectorizer(min_df = 20)
    unig = Vectorizer.fit_transform(data.news)
    train_f = pd.DataFrame(unig.todense(),columns = Vectorizer.get_feature_names())
    test_f = pd.DataFrame(Vectorizer.transform(test.news).todense(),columns = Vectorizer.get_feature_names())
    return train_f, test_f

train = load('train.csv')
test = load('test.csv')
# repl(test.iloc[:,0])
# repl(train.iloc[:,0])
liwc = pd.read_csv('LIWC.all.txt',sep= ' ,',header=None)
affect = pd.read_csv('WordNetAffect.all.txt',header=None)
moral = pd.read_csv('Morality.All.txt',header=None)
train_liwc_f = pd.read_csv('liwc_train.csv',index_col=0)
test_liwc_f = pd.read_csv('liwc_test.csv',index_col=0)
train_affect_f = pd.read_csv('train_affect_f',header=None)
test_affect_f = pd.read_csv('test_affect_f',header=None)
sentiment_train = pd.read_csv('sentiment_train.csv',index_col=0)
sentiment_test = pd.read_csv('sentiment_test.csv',index_col=0)
speci_train = pd.read_csv('train_speci_score',header = None)
speci_test = pd.read_csv('test_speci_score',header = None)
train_ful = pd.read_csv('train.csv',header = None)
test_ful = pd.read_csv('test.csv', header = None)

# unigram
# LR 21.78% SVM 20.44%
train_uni,test_uni = unigrams(train,test)
logreg = linear_model.LogisticRegression(multi_class='multinomial',solver='lbfgs',C=1e5,max_iter=1000)
clf = LinearSVC(C=1e3)
clf.fit(train_uni,train.iloc[:,0])
clf.score(test_uni,test.iloc[:,0])
logreg.fit(train_uni,train.iloc[:,0])
logreg.score(test_uni,test.iloc[:,0])
# using lexical features
# LR affect 22.10% SVM 22.10%
# LR liwc 25.33% SVM 25.65%
# LR affect + LIWC: 25.80% SVM: 26.36%
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:]],axis=1),test.iloc[:,0])

param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:]],axis=1),test.iloc[:,0])

# affect + LIWC + sentiment
# LR 25.97%
# SVM 26.52%
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']]],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']]],axis=1),test.iloc[:,0])

# affect + LIWC + moral
# LR 26.04%
# SVM 26.36%
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_moral_f.iloc[:,2:],train_liwc_f.iloc[:,2:]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_moral_f.iloc[:,2:],test_liwc_f.iloc[:,2:]],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4,1e5,1e-3,1e-4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_moral_f.iloc[:,2:],train_liwc_f.iloc[:,2:]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_moral_f.iloc[:,2:],test_liwc_f.iloc[:,2:]],axis=1),test.iloc[:,0])

# affect + LIWC + sentiment + moral
# LR 26.99%
# SVM 26.44%
lr = linear_model.LogisticRegression(multi_class='multinomial',solver='lbfgs',max_iter=1000)
param_grid = {'C': [1, 1e2, 1e-2, 1e-3,1e-4],}
logreg = GridSearchCV(lr, param_grid)
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_moral_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_moral_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']]],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4,1e5,1e-3,1e-4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_moral_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_moral_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']]],axis=1),test.iloc[:,0])

# affect + LIWC + sentiment + speci
# LR 25.57%
# SVM 25.49%
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']],speci_train[0]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']],speci_test[0]],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']],speci_train[0]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']],speci_test[0]],axis=1),test.iloc[:,0])

# unigrams + affect + LIWC + sentiment
# LR 24.07%
# SVM 26.52%
lr = linear_model.LogisticRegression(multi_class='multinomial',solver='lbfgs',max_iter=1000)
param_grid = {'C': [1, 1e2, 1e-2, 1e3,1e4],}
logreg = GridSearchCV(lr, param_grid)
logreg.fit(pd.concat([train_uni,train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_uni,test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']]],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_uni,train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_uni,test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']]],axis=1),test.iloc[:,0])

# affect + LIWC + sentiment + credit history 
# LR: 30.86%
# SVM: 30.14%
lr = linear_model.LogisticRegression(multi_class='multinomial',solver='lbfgs',max_iter=1000)
param_grid = {'C': [1, 1e2, 1e-2, 1e3,1e4],}
logreg = GridSearchCV(lr, param_grid)
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']],train_ful.iloc[:,8:13]],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']],test_ful.iloc[:,8:13]],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']],train_ful.iloc[:,8:13]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']],test_ful.iloc[:,8:13]],axis=1),test.iloc[:,0])

# affect + LIWC + sentiment + speaker  
# LR 30.94% 
# SVM 42.14%
enc = OneHotEncoder()
le = LabelEncoder()
train_ful = train_ful.fillna('0')
test_ful = test_ful.fillna('0')
temp = le.fit_transform(train_ful.iloc[:,4])
enc.fit(temp)
lr = linear_model.LogisticRegression(multi_class='multinomial',solver='lbfgs',max_iter=1000)
param_grid = {'C': [1, 1e2, 1e-2, 1e3,1e4],}
logreg = GridSearchCV(lr, param_grid)
logreg.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']],enc.transform(le.transform(train_ful.iloc[:,4])).T],axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']],enc.transform(le.transform(test_ful.iloc[:,4])).T],axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_affect_f.iloc[:,2:],train_liwc_f.iloc[:,2:],sentiment_train[['NEG','POS']],enc.transform(le.transform(train_ful.iloc[:,4]))]],axis=1),train.iloc[:,0])
clf.score(pd.concat([test_affect_f.iloc[:,2:],test_liwc_f.iloc[:,2:],sentiment_test[['NEG','POS']],enc.transform(le.transform(test_ful.iloc[:,4]))]],axis=1),test.iloc[:,0])


# purely credit history 
# LR 30.94%
# SVM 42.14%
lr = linear_model.LogisticRegression(multi_class='multinomial',solver='lbfgs',max_iter=1000)
param_grid = {'C': [1, 1e2, 1e-2, 1e3,1e4],}
logreg = GridSearchCV(lr, param_grid)
logreg.fit(pd.concat([train_ful.iloc[:,8:13]], axis=1),train.iloc[:,0])
logreg.score(pd.concat([test_ful.iloc[:,8:13]], axis=1),test.iloc[:,0])
param_grid = {'C': [1, 1e2, 1e-2, 1e3, 1e4],}
clf = GridSearchCV(LinearSVC(), param_grid)
clf.fit(pd.concat([train_ful.iloc[:,8:13]], axis=1),train.iloc[:,0])
clf.score(pd.concat([test_ful.iloc[:,8:13]], axis=1),test.iloc[:,0])
