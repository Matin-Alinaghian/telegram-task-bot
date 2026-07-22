import os
import json
import jdatetime
import taskmanager
import asyncio
import time


BASE_DIR = os.path.dirname(__file__)

FOLDER = os.path.join(
    BASE_DIR,
    "users_tasks"
)


if not os.path.exists(FOLDER):

    os.makedirs(FOLDER)



tasks = []

current_user = None



def get_file(user_id):

    return os.path.join(
        FOLDER,
        f"{user_id}.json"
    )



def load_tasks(user_id):

    global tasks
    global current_user


    current_user = user_id


    file = get_file(user_id)


    if os.path.exists(file):

        try:

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                tasks = json.load(f)


        except:

            tasks = []


    else:

        tasks = []




def save_tasks():

    file = get_file(current_user)


    with open(
        file,
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(
            tasks,
            f,
            ensure_ascii=False,
            indent=4
        )




def sort_tasks():

    priority_order = {

        "high": 1,

        "medium": 2,

        "low": 3

    }


    return sorted(

        tasks,

        key=lambda task:
        priority_order.get(
            task["level"],
            4
        )

    )




def add_task(user_id, title, level):

    load_tasks(user_id)

    task = {


        "title": title.strip(),

        "done": False,

        "level": level,

        "created_at": jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")

    }


    tasks.append(task)


    save_tasks()


    return True




def show_all_tasks(user_id):

    load_tasks(user_id)


    return sort_tasks()




def show_done_task(user_id):

    load_tasks(user_id)


    return [

        task

        for task in sort_tasks()

        if task["done"]

    ]




def show_undone_task(user_id):

    load_tasks(user_id)


    return [

        task

        for task in sort_tasks()

        if not task["done"]

    ]





def mark_task_done(user_id, index):

    load_tasks(user_id)


    sorted_tasks = sort_tasks()


    if index < 1 or index > len(sorted_tasks):

        return False



    task = sorted_tasks[index-1]



    if task["done"]:

        return "already"



    task["done"] = True

    save_tasks()


    return True





def delete_task(user_id, index):

    load_tasks(user_id)


    sorted_tasks = sort_tasks()


    if index < 1 or index > len(sorted_tasks):

        return False



    task = sorted_tasks[index-1]


    tasks.remove(task)


    save_tasks()


    return True



def delete_all_tasks(user_id):

    load_tasks(user_id)

    tasks.clear()

    save_tasks()

    return True

def edit_task(user_id, index, new_title, level):

    load_tasks(user_id)


    sorted_tasks = sort_tasks()


    if index < 1 or index > len(sorted_tasks):

        return False



    task = sorted_tasks[index-1]


    task["title"] = new_title.strip()

    task["level"] = level


    save_tasks()


    return True





def search_task(user_id, word):

    load_tasks(user_id)


    result = []


    for task in sort_tasks():


        if word.lower() in task["title"].lower():

            result.append(task)



    return result