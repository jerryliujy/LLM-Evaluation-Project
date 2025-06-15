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

For raw questions and raw answers, the record could not be changed once it is written to the database. I use the property `is_deleted` to indicate whether the record is still available to privileged users. The users (when authorized) could soft- delete records from the database, and restore the deleted one from restoration bin. However, the users are not allowed to change the content of records. Once the raw question is deleted, the standard question referencing to it will be set to invalid, but not be straightly deleted. The same rule holds for raw answer deletion and expert answer deletion. 

For expert deletion, if `is_deleted` is true for any expert, all of his/her expert answers will be hard-deleted. 
