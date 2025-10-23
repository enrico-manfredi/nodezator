import math

def cosine(a):
	cos_list = []
	for elem in a:
		cos_list.append(math.cos(elem))
	return cos_list


main_callable = cosine