import os
from typing import List
from fastapi import FastAPI
from schema import PostGet
from schema import Response
from datetime import datetime
import pandas as pd
import hashlib
from sqlalchemy import create_engine
from catboost import CatBoostClassifier

MODEL_CONTROL_PATH = os.getenv("MODEL_CONTROL_PATH", "models/catboost_model.cbm")
MODEL_TEST_PATH    = os.getenv("MODEL_TEST_PATH",    "models/catboost_model.cbm")
IS_LMS = os.getenv("IS_LMS") == "1"

app = FastAPI()
SQLALCHEMY_DATABASE_URL = "postgresql://robot-startml-ro:pheiph0hahj1Vaif@postgres.lab.karpov.courses:6432/startml"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
connect = engine.connect().execution_options(stream_results=True)

# Функция для загрузки признаков из базы данных
def batch_load_sql(query: str, CHUNKSIZE: int = 200000, engine=engine) -> pd.DataFrame:
    """Выполнение sql-запроса и выгрузка результата по чанкам."""
    connect = engine.connect().execution_options(stream_results=True)
    chunks = []
    for ind, chunk_dataframe in enumerate(pd.read_sql(query, connect, chunksize=CHUNKSIZE)):
        chunk_dataframe.to_csv(f'temp_chunk_{ind}.csv', index=False)
        chunks.append(f'temp_chunk_{ind}.csv')
        print(f'{ind} загрузка данных по чанкам {CHUNKSIZE}')
    connect.close()

    # Загрузка всех чанков из временных файлов и объединение их в один DataFrame
    all_chunks = pd.concat([pd.read_csv(f) for f in chunks], ignore_index=True)

    # Удаление временных файлов
    for f in chunks:
        os.remove(f)

    print('Загрузка завершена')
    return all_chunks


# Функция для загрузки всех признаков
def load_user_features_control_model() -> pd.DataFrame:
    query = 'SELECT * FROM fsb_1502_features_lesson_22_new'
    features_df = batch_load_sql(query)
    return features_df

def load_user_features_test_model() -> pd.DataFrame:
    query = 'SELECT * FROM fsb_1502_features_lesson_22_new_model'
    features_df = batch_load_sql(query)
    return features_df

def load_post_control_features() -> pd.DataFrame:
    query = 'SELECT * FROM fsb_1502_features_lesson_22_post_new'
    features_df = batch_load_sql(query)
    return features_df

def load_post_test_features() -> pd.DataFrame:
    query = 'SELECT * FROM fsb_1502_features_lesson_22_post_new_model'
    features_df = batch_load_sql(query)
    return features_df

def get_exp_group(user_id: int) -> str:
    salt = 'final_project'
    hash_id = int(hashlib.md5((str(user_id) + salt).encode()).hexdigest(),16)
    if hash_id % 2 == 0:
        return 'control'
    else:
        return 'test'

# Функция для получения пути к модели
def get_model_path(group: str) -> str:
    if IS_LMS:
        return '/workdir/user_input/model_control' if group == 'control' else '/workdir/user_input/model_test'
    return MODEL_CONTROL_PATH if group == 'control' else MODEL_TEST_PATH



# Функция для загрузки модели CatBoost
def load_model(group: str):
    model = CatBoostClassifier()
    model_path = get_model_path(group)
    model.load_model(model_path)
    return model


# Загрузка признаков
user_features_df_test = load_user_features_test_model()
post_features_df_test = load_post_test_features()
user_features_df_control = load_user_features_control_model()
post_features_df_control = load_post_control_features()

split_percentage = 50

# Эндпоинт для получения рекомендаций
@app.get("/post/recommendations/", response_model=Response)
def recommended_posts(id: int, limit: int = 10) -> List[PostGet]: #, time: datetime

    #Получение группы пользователя:
    group = get_exp_group(id)

    #Загрузка модели
    model = load_model(group)

    # Получение признаков для конкретного user_id
    if group == 'control':
        user_features = user_features_df_control[user_features_df_control['user_id'] == id].drop(['index', 'city', 'post_id'], axis = 1).iloc[0]
        post_features = post_features_df_control
    if group == 'test':
        user_features = user_features_df_test[user_features_df_test['user_id'] == id].drop(['index', 'city', 'post_id'], axis=1).iloc[0]
        post_features = post_features_df_test

    user_features_df_dupl = pd.DataFrame([user_features] * len(post_features)).reset_index(drop=True)
    full_df = pd.concat([post_features, user_features_df_dupl], axis=1)

    X = full_df.drop(['user_id', 'text', 'target'], axis = 1).set_index('post_id')

    #Получение предсказаний
    predictions = model.predict_proba(X)[:, 1]
    full_df['predictions'] = predictions


    # Отбираем top-N постов
    top_posts = full_df.nlargest(limit, 'predictions')[['post_id', 'text', 'topic']]

    # Формируем список рекомендованных постов
    recommended_posts_list = [
        PostGet(id=row['post_id'], text=row['text'], topic=row['topic'])
        for _, row in top_posts.iterrows()
    ]

    return Response(exp_group = group, recommendations = recommended_posts_list)

