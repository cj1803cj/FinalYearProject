from sklearn.metrics.pairwise import cosine_similarity

def recommend(title, df, tfidf_vectorizer):

    try:
        title_iloc = df.index[df['Repository Name'] == title][0]

    except:
        return f'Project with title "{title}" could not be found' 

    print(title_iloc)

    project_cos_sim = cosine_similarity(tfidf_vectorizer[title_iloc], tfidf_vectorizer).flatten()

    top5 = sorted(list(enumerate(project_cos_sim)), key=lambda x: x[1], reverse=True)[1:6]

    response = top5

    return response
    

def find(id, cv):

    try:
        user_cos_sim = cosine_similarity(cv[id - 1], cv).flatten()
        top2 = sorted(list(enumerate(user_cos_sim)), key=lambda x: x[1], reverse=True)[1:3]
        response = top2
    except:
        return f'User with id "{id}" could not be found' 

    return response


def api_recommend(title, df, tfidf_vectorizer):

    try:
        title_iloc = df.index[df['Repository Name'] == title][0]

    except:
        return f'Project with title "{title}" could not be found' 

    project_cos_sim = cosine_similarity(tfidf_vectorizer[title_iloc], tfidf_vectorizer).flatten()

    top5 = sorted(list(enumerate(project_cos_sim)), key=lambda x: x[1], reverse=True)[1:6]
    
    response = {'result': [{'title':df.iloc[t_vect[0]][0], 'confidence': round(t_vect[1],1)} for t_vect in top5]}

    return response