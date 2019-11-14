import re
import pythainlp.corpus as pycorpus

# prepare for tokenize
def cleanContent(rawContent):
    content = rawContent
    content = re.sub(r'<[^<]+/>|<[^<]+>|\\.{1}|&[^&]+;|\n|\r\n','', content) #0 to msg_clean
    url_rex = r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    content = re.sub(url_rex,'', content) #1 remove url
    content = re.sub(r'â|ä|à|å|á|ã', 'a', content) #2 replace extended vowels a
    content = re.sub(r'Ä|Å|Á|Â|À|Ã', 'A', content) #3 replace extended vowels A
    content = re.sub(r'ê|ë|è', 'e', content) #4 replace extended vowels e
    content = re.sub(r'É|Ð|Ê|Ë|È', 'E', content) #5 replace extended vowels E
    content = re.sub(r'ï|î|ì|í|ı', 'i', content) #6 replace extended vowels i
    content = re.sub(r'Í|Î|Ï', 'I', content) #7 replace extended vowels I
    content = re.sub(r'ô|ö|ò|ó|õ', 'o', content) #8 replace extended vowels o
    content = re.sub(r'Ö|Ó|Ô|Ò|Õ', 'O', content) #9 replace extended vowels O
    content = re.sub(r'ü|û|ù|ú', 'u', content) #10 replace extended vowels u
    content = re.sub(r'Ü|Ú|Û|Ù', 'U', content) #11 replace extended vowels U
    content = re.sub(r'ç', 'c', content) #12 replace extended chars c
    content = re.sub(r'ÿ|ý', 'y', content) #13 replace extended chars y
    content = re.sub(r'Ý', 'Y', content) #14 replace extended chars y
    content = re.sub(r'ñ|Ñ', 'n', content) #15 replace extended chars n
    content = re.sub(r'ß', 's', content) #16 replace extended chars n
    # spechar = r'[^a-zA-Z0-9ก-๙\.\,\s]+|\.{2,}|\xa0+|\d+[\.\,][^\d]+'
    spechar = r'[^a-zA-Zก-๙\s]+|\xa0+|ๆ' #! take numbers out
    content = re.sub(spechar, ' ', content) #17 remove special character
    #18 remove duplicate characters and spaces
    dupGroup = re.finditer(r'\s{2,}|([ก-๙a-zA-Z])\1{2,}', content)
    dupArray = [[c.start(), c.end()] for c in dupGroup]
    # print(dupArray)
    newContent = ""
    if len(dupArray) == 0:
        newContent = content
    else:
        prevIdx = 0
        for idxDup in dupArray:
            newContent += content[prevIdx:idxDup[0]+1]
            prevIdx = idxDup[1]
        newContent += content[prevIdx:]
    return newContent


# prepare stopwords list
def getStopWords(addMore, fname="./utils/stopwords_more_th.txt"):
    stopwords = pycorpus.common.thai_stopwords()
    stopwordsList = set(m.strip() for m in stopwords)
    if addMore:
        f = open(fname, "r", encoding='utf-8')
        stopwordsList = stopwordsList.union(set(m.strip() for m in f.readlines()))
    return stopwordsList