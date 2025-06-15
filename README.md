# This is the final project of **Database System Design** in Fudan University.

## Setup

* For starting backend, you should:

1. Start a virtual environment

```
[.]$ ./venv/Scripts/activate
```

2. Download the requirements

```
[backend]$ pip install -r requirements.txt
```

3. Run the backend

```
[backend]$ python run.py
```

* For starting frontend, you should:

1. Download npm

2. Download dependency

```
[frontend]$ 

For starting frontend: run `npm run serve` in `frontend` folder.

```txt
cd backend
docker exec -it mysql-container mysql -u root -p --default-character-set=utf8mb4 --raw
```


## For Dataset Managers

If you are a dataset manager, our platform can help you:

1. build your own question pool
2. create your own dataset
3. publicize your dataset

The most exciting part is absolutely creating and publicizing your dataset, but wait a minute. You should do some foundamental works in order to successfully create your dataset. For every question in the dataset, there must be some raw questions it refers to. This design guarantees transparency and credibility of the question. Therefore, we should construct our raw question pool first.

We enable two ways to load the raw q-a pair into the pool, manually writing the record or loading from a json file respectively. We recommend the latter for its convenience and high efficiency. The loading-file page indicates the correct format of your json file, and you should check it out. We also provide you with a demo data in `test_data` folder.

Generally, the data importing function in our system is quite straightforward and adaptable. For nearly every data importing cases in the system, we offer the manually importing method and file importing method. You will have a hand-on experience with this as long as you dive into our system.

OK, wish you have a massive question pool so that you can create more interesting datasets on it. Now let's move on to creating the dataset! First you should give a name and description (not required), and then manually create std qa pairs or load them from a json file. No matter in which way you initialize the dataset, you should always specify raw questions that the standard question refers to. You can also refer to raw answers and expert answers for a standard answer, and that's up to you.

Standard questions can be categorized into two types--choice and text. The text question requires an explanation on the question, and normally the answer will be accompanied by ordered scoring points. On the other hand, the choice question is more definite, and in our setting we only include single-choice questions. After creating the dataset, you can enter and take a look at each question pair. The dataset view functions as an interface to modify, delete or search the original questions, answers and scoring points.

We aim at building a lightweight but integrated platform that allows users to construct their databases smoothly, so we develop a version management that enables swift iteration. The dataset manager can create new version of one dataset in its view page, and the version editing resembles the crud operation on the original dataset. In the implementation, we leverage some version tables to record the modification, and only create relations for those modified or newly inserted question pairs, significantly saving the memory usage as many question pairs will stay the same. For further information, you can check the query for creating tables.

## For experts
