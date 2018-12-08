import sys
import json
import argparse
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from rebroadcast.rxtx import Anthena

def main(country, nodes, config):

    with open(config) as f:
        config_data = json.load(f)

    a = Anthena(country, nodes, config_data)

    a.run()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                        description='Radio Streaming RXTX anthena',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "--country",
            help="Country of the form: <ISO-COUNTRY>"
    )

    parser.add_argument(
            "--nodes",
            help="Number of replica nodes",
            default=2
    )

    parser.add_argument(
            "--config",
            help="Topology configuration",
    )

    args = parser.parse_args()

    main(args.country, args.nodes, args.config)


