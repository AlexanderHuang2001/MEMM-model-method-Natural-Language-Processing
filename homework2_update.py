#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os, re

sentence_list = []
with open(os.path.abspath('../pku_training.txt'), 'rb') as f:
    # 每次读取一行数据
    line = f.readline()
    while line:
        line = line.decode("gb18030", "ignore")
        # 每一行为一个段落，按句号将段落切分成句子
        sentence = line.split('。')
        sentence_list.extend(sentence)
        line = f.readline()
# 打印出数据的前 5 句
# for i in range(5):
#     print(sentence_list[i])
#     print('-'*100)
def get_tag(word):
    tags = []  # 创建一个空列表用来存放标注数据
    word_len = len(word)
    if word_len == 1:  # 如果是单字成词，标记为 S
        tags = ['S']
    elif word_len == 2:  # 如果该词仅有两个字，则标记为 B 和 E
        tags = ['B', 'E']
    else:
        tags.append('B')  # 第一个字标记为 B
        tags.extend(['M']*(len(word)-2))  # 中间标记为 M ，
        tags.append('E')  # 最后一个标记为 E
    return tags


# # 测试标注函数
# get_tag('刘德华')
def pre_data(data):
    X = []  # 创建一个空列表来存放每个中文句子
    y = []  # 创建一个空列表来存放每个句子标注结果
    word_dict = []  # 创建一个空列表来存放每个句子的正确分词结果
    for sentence in data:
        sentence = sentence.strip()
        if not sentence:
            continue
        # 将句子按空格进行切分，得到词
        words = sentence.split("  ")
        word_dict.append(words)
        sent = []  # 用于临时存放一个中文句子
        tags = []  # 用于临时存放一个句子对应的标注
        for word in words:
            sent.extend(list(word))
            tags.extend(get_tag(word))  # 获得标注结果
        X.append(sent)
        y.append(tags)
    return X, y, word_dict
train_data = sentence_list[:-60]
test_data = sentence_list[-60:]
train_X, train_y, train_word_dict = pre_data(train_data)
test_X, test_y, test_word_dict = pre_data(test_data)

# print(train_X[0])
# print('-'*100)
# print(train_y[0])
# print('-'*100)
# print(train_word_dict[0])
# print('='*100)
# print(test_X[0])
# print('-'*100)
# print(test_y[0])
# print('-'*100)
# print(test_word_dict[0])

states = {'B', 'M', 'E', 'S'}

def para_init():
    init_mat = {}  # 初始状态矩阵
    emit_mat = {}  # 发射矩阵
    tran_mat = {}  # 转移状态矩阵
    state_count = {}  # 用于统计每个隐藏状态（即 B,M,E,S）出现的次数
    for state in states:
        tran_mat[state] = {}
        for state1 in states:
            tran_mat[state][state1] = 0.0  # 初始化转移状态矩阵
        emit_mat[state] = {}  # 初始化发射矩阵
        init_mat[state] = 0.0  # 初始化初始状态矩阵
        state_count[state] = 0.0  # 初始化状态计数变量
    return init_mat, emit_mat, tran_mat, state_count

import pandas as pd
init_mat, emit_mat, tran_mat, state_count = para_init()
# print(pd.DataFrame(init_mat, index=['init']))
# print('-'*100)
# print(pd.DataFrame(tran_mat).T)
# print('-'*100)
# print((pd.DataFrame(emit_mat)).T)

def count(train_X, train_y):
    """
    train_X: 中文句子
    train_Y: 句子对应的标注
    """
    # 初始化三个矩阵
    init_mat, emit_mat, tran_mat, state_count = para_init()
    sent_count = 0
    for j in range(len(train_X)):
        # 每次取一个句子进行统计
        sentence = train_X[j]
        sent_state = train_y[j]
        for i in range(len(sent_state)):
            if i == 0:
                # 统计每个状态（即 B,M,E,S）在每个句子对应的标注序列中第一个位置的次数
                init_mat[sent_state[i]] += 1
                # 统计每个隐藏状态（即 B,M,E,S）在整个训练样本中出现的次数
                state_count[sent_state[i]] += 1
                # 统计有多少个句子。
                sent_count += 1
            else:
                # 统计两个相邻时刻的不同状态组合同时出现的次数
                tran_mat[sent_state[i-1]][sent_state[i]] += 1
                state_count[sent_state[i]] += 1
                # 统计每个状态对应于每个文字的次数
                if sentence[i] not in emit_mat[sent_state[i]]:
                    emit_mat[sent_state[i]][sentence[i]] = 1
                else:
                    emit_mat[sent_state[i]][sentence[i]] += 1
    return init_mat, emit_mat, tran_mat, state_count, sent_count


init_mat, emit_mat, tran_mat, state_count, sent_count = count(train_X, train_y)
# print(pd.DataFrame(init_mat, index=['init']))
# print('-'*100)
# print(pd.DataFrame(tran_mat).T)
# print('-'*100)
# # 随机取 6 个观测字
# print((pd.DataFrame(emit_mat)).iloc[94:100, :].T)

def get_prob(init_mat, emit_mat, tran_mat, state_count, sent_count):
    tran_prob_mat = {}  # 状态转移矩阵
    emit_prob_mat = {}  # 发射矩阵
    init_prob_mat = {}  # 初始状态矩阵
    # 计算初始状态矩阵
    for state in init_mat:
        init_prob_mat[state] = float(
            init_mat[state]/sent_count)
    # 计算状态转移矩阵
    for state in tran_mat:
        tran_prob_mat[state] = {}
        for state1 in tran_mat[state]:
            tran_prob_mat[state][state1] = float(
                tran_mat[state][state1]/state_count[state])
    # 计算发射矩阵
    for state in emit_mat:
        emit_prob_mat[state] = {}
        for word in emit_mat[state]:
            emit_prob_mat[state][word] = float(
                emit_mat[state][word]/state_count[state])

    return tran_prob_mat, emit_prob_mat, init_prob_mat


tran_prob_mat, emit_prob_mat, init_prob_mat = get_prob(
    init_mat, emit_mat, tran_mat, state_count, sent_count)
# print(pd.DataFrame(init_prob_mat, index=['init']))
# print('-'*100)
# print(pd.DataFrame(tran_prob_mat).T)
# print('-'*100)
# print((pd.DataFrame(emit_prob_mat)).iloc[94:100, :].T)


# print(pd.DataFrame(init_prob_mat, index=['init']))
# print('-'*100)
# print(pd.DataFrame(tran_prob_mat).T)
# print('-'*100)
# print((pd.DataFrame(emit_prob_mat)).loc[['明', '天', '要', '下', '雨'], :].T)


def predict(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat):
        tab = [{}]  # 用于存放对应节点的 𝛿 值
        path = {}   # 用于存放对应节点所经过的最优路径
        # 求出 T0 时刻的 𝛿 值
        try:
            for state in states:
                tab[0][state] = init_prob_mat.get(
                    state) * emit_prob_mat[state].get(sentence[0], 0.000000001)
                path[state] = [state]
        except:
            print(sentence)
            os.system('pause')
        for t in range(1, len(sentence)):
            tab.append({})  # 创建一个元组来存放 𝛿 值和对应的节点
            new_path = {}
            for state1 in states:
                # state1 为后一个时刻的状态
                items = []
                for state2 in states:
                     # state2 为前一个时刻的状态
                    if tab[t - 1][state2] == 0:
                        continue
                    # 计算上一个时刻状态 state2 到当前时刻的状态 state1 的转移概率值
                    tr_prob = tran_prob_mat[state2].get( 
                        state1, 0.000000001) * emit_prob_mat[state1].get(sentence[t], 0.0000001)
                    # 计算当前的状态为 state1 时经过上一个时刻状态 state2 的概率值
                    prob = tab[t - 1][state2] * tr_prob
                    items.append((prob, state2))
                if not items:
                    items.append((0.000000001, 'S'))
                # 求出某个时刻的每个状态节点对应的最优路径
                best = max(items)  # best: (prob, state)
                tab[t][state1] = best[0]
                new_path[state1] = path[best[1]] + [state1]
            path = new_path
        # 寻找最后一个时刻最大的 𝛿 值以及所对应的节点（即状态）。
        prob, state = max([(tab[len(sentence) - 1][state], state)
                           for state in states])
        return path[state]  # 返回最大 𝛿 值节点所对应的路径
    
# sentence = "明天要下雨"
# # tag = predict(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat)
# # '  '.join(tag)

def cut_sent(sentence, tags):
    """
    sentence:句子
    tags:标注
    """
    word_list = []  # 存放切分结果
    start = -1
    started = False

    if len(tags) != len(sentence):
        return None

    if tags[-1] not in {'S', 'E'}:
        if tags[-2] in {'S', 'E'}:  # 如果最后一个没有标记为 'S', 'E'，并且倒数
            tags[-1] = 'S'  # 第二个标记为 'S','E'则将最后一个标记为 'S'
        else:  # 如果最后一个没有标记为 'S', 'E'，并且倒数
            tags[-1] = 'E'  # 第二个标记为 'B','M'则将最后一个标记为 'E'
    for i in range(len(tags)):
        if tags[i] == 'S':
            if started:
                started = False
                word_list.append(''.join(sentence[start:i]))
            word_list.append(sentence[i])
        elif tags[i] == 'B':
            if started:
                word_list.append(''.join(sentence[start:i]))
            start = i
            started = True
        elif tags[i] == 'E':
            started = False
            word = sentence[start:i + 1]
            word_list.append(''.join(word))
        elif tags[i] == 'M':
            continue
    return word_list

# result = cut_sent(sentence, tag)
# ' | '.join(result)

def word_seg(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat):
    tags = predict(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat)
    result = cut_sent(sentence, tags)
    return result

# 测试定义的函数
# result = word_seg(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat)
# ' | '.join(result)

# def accurency(y_pre, y):
#     """
#     分词准确率计算函数
#     y_pre：预测结果
#     y:     正确结果
#     """
#     count = 0
#     n = len(y_pre)
#     for i in range(len(y_pre)):
#         # 统计每个句子切分出来的词数
#         n += len(y_pre[i])
#         for word in y_pre[i]:
#             # 统计每个句子切词正确的词数
#             if word in y[i]:
#                 count += 1
#     return count/n

# from tqdm.notebook import tqdm

# word_cut_result = []  # 创建一个空列表来存放分词结果

# # 每次切一个句子
# for sent in tqdm(test_X):
#     # 使用前面所构建的分词器进行切词
#     temp = word_seg(sent, tran_prob_mat, emit_prob_mat, init_prob_mat)
#     # 存放分词后的数据
#     word_cut_result.append(temp)


# # 计算准确率
# acc = accurency(word_cut_result, test_word_dict)
# acc

# print(' | '.join(word_cut_result[0]))
# print('-'*100)
# print(' | '.join(test_word_dict[0]))

# sentence = '实现自分割分词或结合统计消歧的分词算法或基于神经网络的分词算法，或对机械分词进行很好的优化'
# result = word_seg(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat)
# ' | '.join(result)


# In[2]:

# while True:
#   sentence = input("请输入分词语句：\n")
#   result = word_seg(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat)
#   a=' | '.join(result)

#   print(a)
# input("Press <enter>")

def cut_sentence(test_file):
    """
    切分句子。
    test_file ：测试文件
    """
    para_list = []
    with open(os.path.abspath(test_file), 'r', encoding='gb18030') as f:
        para = f.readline()
        while para:
            para_list.append(para)
            para = f.readline()

    sentence_list = []
    for para in para_list:
        sentence = re.split('([。？！\n])', para)
        while '' in sentence:
            sentence.remove('')
        sentence_list.extend(sentence)
    return sentence_list

test_sentence_list = cut_sentence("../testing/pku_test.txt")
with open('pku_test_seg_Huang.txt', 'w', encoding='utf-8') as f:
    for sentence in test_sentence_list:
        if sentence == '。' or sentence == '！' or sentence == '？':
            f.write(' ' + sentence + ' ')
        elif sentence == '\n':
            f.write(sentence)
        else:
            sent = word_seg(sentence, tran_prob_mat, emit_prob_mat, init_prob_mat)
            f.write(' '.join(sent))






