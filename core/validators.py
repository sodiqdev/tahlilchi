def validate_students_list(students_list):
    if not isinstance(students_list, list):
        raise TypeError("students_list ro'yxat bo'lishi kerak")
    if len(students_list) == 0:
        raise ValueError("students_list bo'sh bo'lishi mumkin emas")


def validate_num_tasks(num_tasks):
    if not isinstance(num_tasks, int) or num_tasks <= 0:
        raise ValueError("num_tasks musbat butun son bo'lishi kerak")


def prepare_config(config: dict | None) -> dict:
    default_config = {
        'tuman': 'Shovot tumani',
        'maktab': '5-maktab',
        'sinf': '10 V',
        'fan': 'algebra',
        'chorak': '4',
        'imtihon_nomi': '8-BSB',
        'oibdo': 'U.Sadiqov',
        'metod_rahbari': 'D.Nurjanova',
        'fan_oqituvchisi': 'S.Sodiqov'
    }

    if config is None:
        return default_config

    for key, value in default_config.items():
        if key not in config:
            config[key] = value

    return config


def validate_max_scores(max_scores, num_tasks):
    if max_scores is None:
        return [10] * num_tasks

    if not isinstance(max_scores, list):
        raise TypeError("max_scores list bo'lishi kerak")

    if len(max_scores) != num_tasks:
        raise ValueError(f"max_scores listida {num_tasks} ta element bo'lishi kerak")

    for x in max_scores:
        if not isinstance(x, (int, float)):
            raise ValueError("max_scores elementlari son bo'lishi kerak")

    return max_scores
