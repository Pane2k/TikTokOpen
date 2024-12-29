
def get_user_list(file_path):
    with open(file_path, 'r') as file:
        user_list = [line.strip() for line in file]
    return user_list