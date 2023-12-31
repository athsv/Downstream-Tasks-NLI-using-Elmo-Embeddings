# -*- coding: utf-8 -*-
"""sst_embeddings_elmo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mNqJys5BqhAoskpsRxoxZA5-HQaCQ3b5
"""

!pip install datasets
!pip install scikit-learn

from sklearn.metrics import accuracy_score, confusion_matrix, roc_curve, auc
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
import torch.nn as nn
import torch
import numpy as np
import pickle
from tqdm import tqdm
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize
from datasets import load_dataset
from datasets import Dataset as HDataset
import string
import nltk
nltk.download('punkt')
nltk.download('stopwords')

sst_dataset = load_dataset('sst', 'default')

sst_dataset['train'][1]

sst_index = [1]
word_to_index = {'<UNK>': 0}
index_to_word = {0: '<UNK>'}

def preprocess_text(text,i):
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Tokenize the text
    tokens = nltk.word_tokenize(text.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]

    # Stem the tokens
    stemmer = nltk.PorterStemmer()
    tokens = [stemmer.stem(token) for token in tokens]

    # Join the tokens back into a string
    # processed_text = ' '.join(tokens)

    itokens = []
    for token in tokens:
        if (token not in word_to_index):
            word_to_index[token] = i[0]
            itokens.append(i[0])
            index_to_word[i[0]] = token
            i[0] += 1
        else:
            itokens.append(word_to_index[token])

    return itokens



# Preprocess the SST dataset
sst_dataset = sst_dataset.map(
    lambda example: {
        'itokens': preprocess_text(example['sentence'], sst_index), 'label': example['label']
    }
)

with open("sst_pp.pkl", "wb") as f:
    pickle.dump(sst_dataset, f)

with open("sst_word_to_index.pkl", "wb") as f:
    pickle.dump(word_to_index, f)

with open("sst_index_to_word.pkl", "wb") as f:
    pickle.dump(index_to_word, f)

class elmo(nn.Module):
    def __init__(self, vocab_size, embed_size, embeddings):
        super(elmo, self).__init__()
        self.embedding = nn.Embedding.from_pretrained(embeddings, freeze=False)
        self.lstm1 = nn.LSTM(embed_size, embed_size//2, bidirectional=True)
        self.lstm2 = nn.LSTM(embed_size, embed_size//2, bidirectional=True)
        self.fc = nn.Linear(embed_size, vocab_size)

    def forward(self, x):
        out = self.embedding(x)
        out1, _ = self.lstm1(out)
        out2, _ = self.lstm2(out1)
        out_fc = self.fc(out2.view(-1, 100))
        final_elmo = 0.1*out + 0.3*out2 + 0.6*out2
        return out_fc, final_elmo

def get_glove_embeddings():
    word_to_vec = {}
    with open('/home/atharva/Desktop/glove.6B.100d.txt', encoding='utf8') as f:
        for line in tqdm(f):
            line = line.rstrip().split(' ')
            rep = torch.from_numpy(np.array([float(dim) for dim in line[1:]]))
            word_to_vec[line[0]] = rep

    embeddings = torch.zeros(len(word_to_index), 100)
    index = 0
    for word in word_to_index:
        if word in word_to_vec:
            embeddings[index] = word_to_vec[word]
        index += 1
    return embeddings

class TextDataset(Dataset):
    def __init__(self, indexed_data, sent_length):
        print('Building TextDataset...')
        padded_data = []
        for el in indexed_data:
            el += [0]*sent_length
            padded_data.append(el[:sent_length])
        self.data = torch.tensor(padded_data)
        print('Building TextDataset complete...')

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

sst_embeddings = get_glove_embeddings()
with open("sst_word_to_vec.pkl", "wb") as f:
    pickle.dump(sst_embeddings, f)

#model training part
sent_length = 20

train_dataset = TextDataset(sst_dataset['train']['itokens'], sent_length)
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

vocab_size = len(word_to_index)
embed_size = 100
sst_elmo_model = elmo(vocab_size, embed_size, sst_embeddings)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(sst_elmo_model.parameters())
num_epochs = 3
model_name = "sst_elmo_model.pt"



num_epochs = 40
                                                            # TRAINING
# for epoch in range(num_epochs):
#     running_loss = 0.0
#     for i, batch in enumerate(train_loader):
#         batch = batch.permute(1, 0)
#         optimizer.zero_grad()
#         target_tensor = torch.tensor(batch[1:])
#         input_tensor = torch.tensor(batch[:-1])
#         outputs, _ = sst_elmo_model(input_tensor)
#         loss = criterion(outputs, target_tensor.reshape(-1))
#         loss.backward()
#         optimizer.step()
#         running_loss += loss.item()
#     train_loss = running_loss / len(train_loader)
#     print(f'Training loss for epoch {epoch + 1}: {train_loss:.4f}')
#     torch.save(sst_elmo_model.state_dict(), model_name)

