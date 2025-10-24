def function(*lists) -> [{"name": "lol"}, {"name": "count"}]:
    lol = []
    for list in lists:
        lol.append(list)
    count = len(lol)
    return {"lol": lol, "count": count}

main_callable = function