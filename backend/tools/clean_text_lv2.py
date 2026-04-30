from nltk.tokenize import word_tokenize
import nltk
import string
from nltk.tokenize.treebank import TreebankWordDetokenizer
import os


dict_file = f'{os.getcwd()}/tools/wordlist.10000.txt'
with open(dict_file) as f:
    dict_list = f.read().splitlines()

finished_mark ='@FED1@'
def insert_finished_mark(string, index=1):
  return string[:index] + finished_mark + string[index:]

#Check 2 tokens
def integration_step1(tokens):
  new_tokens = []
  skip = False
  for index, token in enumerate(tokens):
    if skip:
      skip = False
      continue
    if token.lower() in dict_list or token in string.punctuation:
      #print("1 " +token)
      new_tokens.append(token)
    else:
      if index+1 == len(tokens):
        combined_token = tokens[index-1] + token
        if combined_token.lower() in dict_list:
          if len(new_tokens) > 0:
            new_tokens.pop()
          new_tokens.append(combined_token)
        else:
          new_tokens.append(token)
        return new_tokens
      else:
        combined_token = token + tokens[index+1]
        if combined_token.lower() in dict_list:
          new_tokens.append(combined_token)
          skip = True
          #print("2 " +combined_token)
        elif index != 0:
          combined_token = tokens[index-1] + token
          if combined_token.lower() in dict_list:
            new_tokens.pop()
            new_tokens.append(combined_token)
            #print("3 " +combined_token)
          else:
            new_tokens.append(token)
            #print("4a " +token)
        else:
          new_tokens.append(token)
          #print("4b " +token)
  return new_tokens

#Check 3 tokens
def integration_step2(tokens):
  if len(tokens) <= 2:
    return tokens
  new_tokens = []
  while len(tokens) > 0:
    token = tokens.pop(0)
    if token.lower() in dict_list:
      new_tokens.append(token)
    elif len(tokens) >= 2:
      combined_token = token + tokens[0] + tokens[1]
      if combined_token.lower() in dict_list:
        new_tokens.append(combined_token)
        tokens.pop(0)
        tokens.pop(0)
      else:
        new_tokens.append(token)
    else:
      new_tokens.append(token)
  return new_tokens

#Check punctuation
def integration_step3(sentence):
  return sentence.replace(' .', '.').replace(' ’ ', '’')

def clean_content_Level2(sentence):
  tokens = word_tokenize(sentence)
  result = integration_step1(tokens)
  result = integration_step2(result)

  result = TreebankWordDetokenizer().detokenize(result)
  output = integration_step3(result)
  return output