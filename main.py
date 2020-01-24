# import libraries
from config import config
from utils import utils

def get_apt_in_neigborhood(apt, neigborhood):
    url = utils.get_url(config.url_raw, neigborhood, config.requirements)
    print(url)
    appartments_string = utils.get_apartments_string(url)
    jsons = utils.get_all_json_strings(appartments_string)
    for json_string in jsons:
        fixed_json = utils.decode_json_string(json_string)
        apt.append(str(fixed_json))


def main():

    apt = []
    parsed_apt = []

    for neigborhood in config.neigborhoods.values():
        get_apt_in_neigborhood(apt, neigborhood)
        parsed_apt.extend(utils.extract_important_info(apt))

    print('found {} apartments'.format(len(parsed_apt)))
    utils.send_email(parsed_apt)
    print(apt)


if __name__ == '__main__':
    main()
