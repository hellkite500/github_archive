import argparse
import yaml
from pathlib import Path
from . import name as package_name
from . import archive_org_repos

def _handle_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config-yaml',
                        help='Set the YAML file for the Github organization configuration',
                        dest='config',
                        default='config.yaml')
    parser.add_argument('--skip',
                        help='List of repositories to skip',
                        dest='skip',
                        nargs='*',
                        type=str)

    parser.prog = package_name
    return parser.parse_args()


def read_config(config_file : Path):
    with open(config_file) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        return config

def main():
    args = _handle_args()

    config = read_config(Path(args.config))

    #Run the archiver
    #TODO validate config options???
    archive_org_repos(config['org'], config['token'], Path(config['destination']), config['repo_type'], args.skip)


if __name__ == '__main__':
    main()
